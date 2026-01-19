#!/usr/bin/env python3
"""
Elastic Security MCP Server
A Model Context Protocol server for translating natural language to ES|QL queries
for SOC analysts and threat hunters.
"""

import os
import re
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pydantic import BaseModel, field_validator

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("elastic-security-mcp")

# Configuration
ES_HOST = os.getenv('ES_HOST', 'http://localhost:9200')
ES_API_KEY = os.getenv('ES_API_KEY')

# Data Models
class QueryIntent(BaseModel):
    """Structured representation of query intent"""
    category: Optional[str] = None
    outcome: Optional[str] = None
    time_range: Optional[str] = None
    filters: List[Dict] = []
    aggregation: Optional[Dict] = None
    index_pattern: Optional[str] = None
    limit: int = 100

class NLQueryParams(BaseModel):
    """Parameters for natural language query"""
    query: str
    
    @field_validator('query')
    def validate_query(cls, value):
        if not value or len(value.strip()) < 3:
            raise ValueError("Query must be at least 3 characters long")
        return value.strip()

class ESQLQueryParams(BaseModel):
    """Parameters for ES|QL query execution"""
    query: str
    dry_run: bool = False
    
    @field_validator('query')
    def validate_esql(cls, value):
        if not value.strip().upper().startswith('FROM'):
            raise ValueError("ES|QL query must start with FROM clause")
        return value.strip()

# Schema definitions
SCHEMAS = {
    "logs-auth-*": {
        "description": "Authentication logs with ECS fields",
        "fields": [
            "@timestamp", "event.category", "event.action", "event.outcome",
            "user.name", "user.domain", "source.ip", "source.geo.country_name",
            "destination.ip", "network.protocol", "network.transport",
            "user_agent.original"
        ]
    },
    "logs-endpoint-*": {
        "description": "Endpoint/process logs with ECS fields", 
        "fields": [
            "@timestamp", "event.category", "event.action", "process.name",
            "process.parent.name", "process.command_line", "process.pid",
            "process.parent.pid", "user.name", "host.name", "file.path",
            "file.name", "network.direction"
        ]
    },
    "logs-network-*": {
        "description": "Network traffic logs with ECS fields",
        "fields": [
            "@timestamp", "event.category", "source.ip", "destination.ip",
            "source.port", "destination.port", "network.protocol",
            "network.transport", "network.bytes", "network.packets",
            "source.geo.country_name", "destination.geo.country_name"
        ]
    }
}

# Hunting templates
HUNTING_TEMPLATES = {
    "auth_failures": {
        "name": "Authentication Failures Analysis",
        "description": "Detect failed authentication attempts and potential brute force",
        "category": "authentication",
        "query_template": 'FROM logs-auth-* | WHERE @timestamp >= NOW() - {hours}h AND event.category == "authentication" AND event.outcome == "failure" | STATS count() BY user.name, source.ip | LIMIT 100'
    },
    "process_spawning": {
        "name": "Suspicious Process Spawning",
        "description": "Track processes spawned by suspicious parents",
        "category": "process", 
        "query_template": 'FROM logs-endpoint-* | WHERE @timestamp >= NOW() - {hours}h AND event.category == "process" AND process.parent.name == "{parent}" | STATS count() BY process.name, user.name | LIMIT 100'
    },
    "geographic_anomalies": {
        "name": "Geographic Authentication Anomalies",
        "description": "Detect authentication from unusual locations",
        "category": "authentication",
        "query_template": 'FROM logs-auth-* | WHERE @timestamp >= NOW() - {hours}h AND event.category == "authentication" | STATS count() BY user.name, source.geo.country_name | WHERE count > 1 | LIMIT 50'
    }
}

# Security policies
class ValidationPolicy:
    ALLOWED_INDEXES = list(SCHEMAS.keys())
    MAX_TIME_RANGE_HOURS = 168  # 7 days
    MAX_LIMIT = 1000
    FORBIDDEN_OPERATIONS = ["JOIN", "ENRICH"]
    ALLOWED_PROTOCOLS = ["ssh", "rdp", "http", "https", "ftp", "smb"]

# Natural Language Parser
class NLParser:
    def __init__(self):
        self.time_patterns = {
            r'last (\d+) hours?': lambda m: f"last_{m.group(1)}_hours",
            r'past (\d+) hours?': lambda m: f"last_{m.group(1)}_hours",
            r'last (\d+) days?': lambda m: f"last_{int(m.group(1)) * 24}_hours",
            r'last day': lambda m: "last_24_hours",
            r'last hour': lambda m: "last_1_hours",
            r'today': lambda m: "last_24_hours"
        }
        
        self.category_patterns = {
            r'auth|login|logon|sign': 'authentication',
            r'process|spawn|exec|run': 'process',
            r'network|connection|traffic': 'network',
            r'file|create|delete|modify': 'file'
        }
        
        self.outcome_patterns = {
            r'success(?:ful|es)?': 'success',
            r'fail(?:ed|ure)s?': 'failure',
            r'block(?:ed)?': 'failure',
            r'allow(?:ed)?': 'success'
        }

    def parse(self, query: str) -> QueryIntent:
        query_lower = query.lower()
        intent = QueryIntent()
        
        # Detect category and set index
        for pattern, category in self.category_patterns.items():
            if re.search(pattern, query_lower):
                intent.category = category
                if category == 'authentication':
                    intent.index_pattern = 'logs-auth-*'
                elif category == 'process':
                    intent.index_pattern = 'logs-endpoint-*'
                elif category == 'network':
                    intent.index_pattern = 'logs-network-*'
                break
        
        # Extract time range
        for pattern, extractor in self.time_patterns.items():
            match = re.search(pattern, query_lower)
            if match:
                intent.time_range = extractor(match)
                break
        
        # Extract outcome
        for pattern, outcome in self.outcome_patterns.items():
            if re.search(pattern, query_lower):
                intent.outcome = outcome
                break
        
        # Extract filters
        countries = ['china', 'russia', 'iran', 'usa', 'uk', 'germany', 'france']
        for country in countries:
            if country in query_lower:
                intent.filters.append({
                    "field": "source.geo.country_name",
                    "operator": "==", 
                    "value": country.title()
                })
                break
        
        # Protocol filters
        protocols = ['ssh', 'rdp', 'http', 'https', 'ftp', 'smb']
        for protocol in protocols:
            if protocol in query_lower:
                intent.filters.append({
                    "field": "network.protocol",
                    "operator": "==",
                    "value": protocol
                })
                break
        
        # Aggregation detection
        if any(phrase in query_lower for phrase in ['by user', 'per user', 'group by user']):
            intent.aggregation = {
                "type": "stats",
                "function": "count()",
                "group_by": ["user.name"]
            }
        
        # Process-specific patterns
        if intent.category == 'process':
            parent_patterns = {
                r'spawned by (\w+)': lambda m: m.group(1),
                r'from (\w+\.exe)': lambda m: m.group(1),
                r'(\w+) process': lambda m: m.group(1)
            }
            
            for pattern, extractor in parent_patterns.items():
                match = re.search(pattern, query_lower)
                if match:
                    parent_name = extractor(match)
                    intent.filters.append({
                        "field": "process.parent.name",
                        "operator": "==",
                        "value": parent_name
                    })
                    break
        
        return intent

# Helper functions
def validate_query_intent(intent: QueryIntent) -> tuple[bool, list[str]]:
    """Validate query intent against security policies"""
    errors = []
    
    # Check for ambiguous terms
    ambiguous_terms = ['risky', 'suspicious', 'unusual', 'anomalous', 'bad', 'malicious']
    # This would need the original query, but we'll skip for now
    
    # Require time range for safety
    if not intent.time_range and not intent.aggregation:
        errors.append("Time range required for safety")
    
    # Check time bounds
    if intent.time_range:
        hours = parse_time_range(intent.time_range)
        if hours > ValidationPolicy.MAX_TIME_RANGE_HOURS:
            errors.append(f"Time range {hours}h exceeds maximum {ValidationPolicy.MAX_TIME_RANGE_HOURS}h")
    
    return len(errors) == 0, errors

def parse_time_range(time_range: str) -> int:
    """Parse time range string to hours"""
    if '_' in time_range:
        parts = time_range.split('_')
        if len(parts) >= 2:
            try:
                return int(parts[1])
            except ValueError:
                pass
    return 24

def generate_esql(intent: QueryIntent) -> str:
    """Generate ES|QL query from intent"""
    query_parts = [f"FROM {intent.index_pattern or 'logs-*'}"]
    
    # Build WHERE conditions
    where_conditions = []
    
    if intent.time_range:
        hours = parse_time_range(intent.time_range)
        where_conditions.append(f"@timestamp >= NOW() - {hours}h")
    
    if intent.category:
        where_conditions.append(f'event.category == "{intent.category}"')
    
    if intent.outcome:
        where_conditions.append(f'event.outcome == "{intent.outcome}"')
    
    for filter_item in intent.filters:
        field = filter_item.get('field')
        operator = filter_item.get('operator', '==')
        value = filter_item.get('value')
        if field and value:
            where_conditions.append(f'{field} {operator} "{value}"')
    
    if where_conditions:
        query_parts.append("| WHERE " + " AND ".join(where_conditions))
    
    if intent.aggregation:
        agg = intent.aggregation
        if agg.get('type') == 'stats':
            function = agg.get('function', 'count()')
            group_by = agg.get('group_by', [])
            if group_by:
                query_parts.append(f"| STATS {function} BY {', '.join(group_by)}")
            else:
                query_parts.append(f"| STATS {function}")
    
    query_parts.append(f"| LIMIT {intent.limit}")
    
    return " ".join(query_parts)

# Resources
@mcp.resource("security://schemas")
def list_schemas() -> str:
    """List available log schemas and their fields"""
    return json.dumps({
        "schemas": SCHEMAS,
        "schema_count": len(SCHEMAS)
    }, indent=2)

@mcp.resource("security://templates")
def list_templates() -> str:
    """List available hunting templates"""
    return json.dumps({
        "templates": HUNTING_TEMPLATES,
        "template_count": len(HUNTING_TEMPLATES)
    }, indent=2)

@mcp.resource("security://policies")
def get_policies() -> str:
    """Get current security policies and limits"""
    return json.dumps({
        "allowed_indexes": ValidationPolicy.ALLOWED_INDEXES,
        "max_time_range_hours": ValidationPolicy.MAX_TIME_RANGE_HOURS,
        "max_limit": ValidationPolicy.MAX_LIMIT,
        "forbidden_operations": ValidationPolicy.FORBIDDEN_OPERATIONS,
        "allowed_protocols": ValidationPolicy.ALLOWED_PROTOCOLS
    }, indent=2)

# Tools
@mcp.tool()
def get_schema(index_pattern: str) -> str:
    """
    Get schema information for an index pattern
    
    Args:
        index_pattern: Elasticsearch index pattern (e.g., "logs-auth-*")
    """
    if index_pattern in SCHEMAS:
        schema = SCHEMAS[index_pattern]
        return json.dumps({
            "success": True,
            "index": index_pattern,
            "description": schema["description"],
            "fields": schema["fields"],
            "field_count": len(schema["fields"])
        }, indent=2)
    
    available = list(SCHEMAS.keys())
    return json.dumps({
        "success": False,
        "error": f"Index pattern '{index_pattern}' not found",
        "available_indexes": available
    }, indent=2)

@mcp.tool()
def nl_to_esql_plan(params: NLQueryParams) -> str:
    """
    Convert natural language to structured ES|QL intent
    
    Args:
        params: Natural language query parameters
    """
    try:
        parser = NLParser()
        intent = parser.parse(params.query)
        
        # Validate intent
        is_valid, errors = validate_query_intent(intent)
        
        if not is_valid:
            return json.dumps({
                "success": False,
                "errors": errors,
                "intent": None
            }, indent=2)
        
        return json.dumps({
            "success": True,
            "errors": [],
            "intent": asdict(intent),
            "original_query": params.query
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "errors": [str(e)],
            "intent": None
        }, indent=2)

@mcp.tool()
def generate_esql_query(intent_json: str) -> str:
    """
    Generate ES|QL query from structured intent
    
    Args:
        intent_json: JSON string containing structured intent
    """
    try:
        intent_data = json.loads(intent_json)
        intent = QueryIntent(**intent_data)
        
        esql_query = generate_esql(intent)
        
        return json.dumps({
            "success": True,
            "query": esql_query,
            "index_pattern": intent.index_pattern,
            "has_aggregation": intent.aggregation is not None,
            "has_time_filter": intent.time_range is not None
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "query": None
        }, indent=2)

@mcp.tool()
def validate_esql_query(params: ESQLQueryParams) -> str:
    """
    Validate ES|QL query against security policies
    
    Args:
        params: ES|QL query parameters
    """
    query = params.query
    errors = []
    warnings = []
    
    # Extract index pattern
    index_match = re.search(r'FROM\s+([\w\-\*]+)', query, re.IGNORECASE)
    if not index_match:
        errors.append("No FROM clause found")
    else:
        index_pattern = index_match.group(1)
        if index_pattern not in ValidationPolicy.ALLOWED_INDEXES:
            errors.append(f"Index '{index_pattern}' not in allowed list")
    
    # Check forbidden operations
    query_upper = query.upper()
    for forbidden_op in ValidationPolicy.FORBIDDEN_OPERATIONS:
        if forbidden_op in query_upper:
            errors.append(f"Operation '{forbidden_op}' is not allowed")
    
    # Check time bounds
    time_match = re.search(r'NOW\(\)\s*-\s*(\d+)h', query)
    if time_match:
        hours = int(time_match.group(1))
        if hours > ValidationPolicy.MAX_TIME_RANGE_HOURS:
            errors.append(f"Time range {hours}h exceeds maximum")
    else:
        if "STATS" not in query_upper:
            warnings.append("No time filter detected")
    
    # Check LIMIT
    limit_match = re.search(r'LIMIT\s+(\d+)', query, re.IGNORECASE)
    if limit_match:
        limit = int(limit_match.group(1))
        if limit > ValidationPolicy.MAX_LIMIT:
            errors.append(f"LIMIT {limit} exceeds maximum {ValidationPolicy.MAX_LIMIT}")
    
    return json.dumps({
        "success": len(errors) == 0,
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings)
    }, indent=2)

@mcp.tool()
def translate_nl_to_esql(params: NLQueryParams) -> str:
    """
    Complete translation from natural language to validated ES|QL
    
    Args:
        params: Natural language query parameters
    """
    try:
        # Step 1: Parse to intent
        parser = NLParser()
        intent = parser.parse(params.query)
        
        # Step 2: Validate intent
        is_valid, errors = validate_query_intent(intent)
        if not is_valid:
            return json.dumps({
                "success": False,
                "errors": errors,
                "query": None,
                "explanation": None
            }, indent=2)
        
        # Step 3: Generate ES|QL
        esql_query = generate_esql(intent)
        
        # Step 4: Generate explanation
        explanation = f"Searching {intent.category or 'all'} events"
        if intent.outcome:
            explanation += f" with {intent.outcome} outcome"
        if intent.time_range:
            hours = parse_time_range(intent.time_range)
            if hours < 24:
                explanation += f" from the last {hours} hours"
            else:
                days = hours // 24
                explanation += f" from the last {days} days"
        if intent.aggregation:
            explanation += " grouped by user"
        
        return json.dumps({
            "success": True,
            "query": esql_query,
            "explanation": explanation,
            "intent": asdict(intent),
            "original_query": params.query
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "query": None,
            "explanation": None
        }, indent=2)

# Prompts
@mcp.prompt()
def threat_hunting_guide(category: str = "authentication") -> str:
    """Generate a threat hunting guide for a specific category"""
    if category == "authentication":
        return """Analyze authentication events for potential threats:

1. Failed login patterns - look for brute force attempts
2. Geographic anomalies - logins from unusual countries
3. Time-based anomalies - logins at unusual hours
4. Protocol analysis - unusual authentication methods
5. Account enumeration - systematic login attempts

Use these ES|QL patterns:
- Failed logins: event.outcome == "failure"
- Geographic filter: source.geo.country_name == "Country"
- Time analysis: @timestamp >= NOW() - 24h
- User aggregation: STATS count() BY user.name"""
    
    elif category == "process":
        return """Analyze process events for suspicious activity:

1. Parent-child relationships - unusual process spawning
2. Command line analysis - suspicious commands
3. Living off the land - abuse of legitimate tools
4. Persistence mechanisms - scheduled tasks, services
5. Privilege escalation - process elevation

Use these ES|QL patterns:
- Process spawning: process.parent.name == "parent.exe"
- Command analysis: process.command_line LIKE "*suspicious*"
- User context: user.name and host.name correlation"""
    
    else:
        return f"""General threat hunting guide for {category} events:

1. Establish baseline behavior patterns
2. Look for statistical anomalies
3. Correlate events across time windows
4. Focus on high-risk indicators
5. Validate findings with additional context

Start with time-bounded queries and gradually expand scope."""

@mcp.prompt()
def esql_best_practices() -> str:
    """ES|QL query best practices for security analysts"""
    return """ES|QL Best Practices for Security Analysis:

PERFORMANCE:
- Always include time filters: @timestamp >= NOW() - 24h
- Use specific index patterns: logs-auth-* vs logs-*
- Limit results appropriately: | LIMIT 100
- Aggregate when possible: STATS count() BY field

SECURITY:
- Avoid unbounded queries without time filters
- Use exact matches over wildcards when possible
- Validate field names against schema
- Be cautious with JOIN operations

ANALYSIS PATTERNS:
- Start broad, then narrow down
- Use aggregations for pattern detection
- Combine multiple fields for context
- Consider time-based grouping for trends

COMMON MISTAKES:
- Missing time filters (expensive queries)
- Using wrong field names (check schema first)
- Overly complex WHERE clauses
- Forgetting to limit results"""

# Main execution
if __name__ == "__main__":
    mcp.run()