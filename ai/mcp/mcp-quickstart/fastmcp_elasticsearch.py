#!/usr/bin/env python3
"""
Elastic Defend Security Events MCP Server
A Model Context Protocol server for querying Elastic Defend security and threat events stored in Elasticsearch.

Author: Alex Salgado
"""
import os
from typing import Any, Optional
import json
from datetime import datetime
from pydantic import BaseModel, field_validator, ValidationError
from fastmcp import FastMCP
from elasticsearch import AsyncElasticsearch
from contextlib import asynccontextmanager

# Initialize FastMCP server
mcp = FastMCP("elastic-defend-security")

# Constants
ES_HOST = "http://localhost:9200"
ES_INDEX = "logs-endpoint.events.*"

# API key from environment variable or fallback for development
ES_API_KEY = os.getenv('ES_API_KEY')


# Pydantic model for parameter validation
class QuerySecurityEventsParams(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    event_type: Optional[str] = None
    process_name: Optional[str] = None
    hostname: Optional[str] = None
    severity: Optional[str] = None
    
    @field_validator('start_date', 'end_date')
    def validate_date_format(cls, value):
        if value is None:
            return value
        try:
            datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
            return value
        except ValueError:
            raise ValueError("Invalid datetime format. Use YYYY-MM-DDTHH:MM:SS")
    
    @field_validator('event_type')
    def validate_event_type(cls, value):
        valid_types = ["process", "network", "file", "host", "alert", None]
        if value not in valid_types:
            raise ValueError(f"Invalid event_type. Use one of: {valid_types[:-1]}")
        return value
    
    @field_validator('severity')
    def validate_severity(cls, value):
        valid_severities = ["critical", "high", "medium", "low", "info", None]
        if value not in valid_severities:
            raise ValueError(f"Invalid severity. Use one of: {valid_severities[:-1]}")
        return value

@asynccontextmanager
async def get_es_client():
    """Context manager for Elasticsearch client."""
    client = AsyncElasticsearch([ES_HOST], api_key=ES_API_KEY)
    try:
        yield client
    finally:
        await client.close()

# Elasticsearch helper function
async def query_elasticsearch(query: dict) -> dict[str, Any] | None:
    """Makes a request to Elasticsearch with proper error handling."""
    print(f"Sending query to Elasticsearch: {json.dumps(query)}")
    
    # Use context manager
    async with get_es_client() as client:
        try:
            response = await client.search(
                index=ES_INDEX,
                body=query
            )
            return response
        except Exception as e:
            print(f"Error querying Elasticsearch: {e}")
            return None


# Resources
@mcp.resource("security://events/types")
async def list_event_types() -> str:
    """List all available security event types"""
    query = {
        "size": 0,
        "aggs": {
            "event_types": {
                "terms": {
                    "field": "event.type",
                    "size": 100
                }
            }
        }
    }
    
    data = await query_elasticsearch(query)
    if not data:
        return json.dumps({"error": "Unable to query Elasticsearch"}, indent=2)
    
    event_types = [bucket["key"] for bucket in data["aggregations"]["event_types"]["buckets"]]
    
    return json.dumps({
        "available_types": event_types,
        "count": len(event_types)
    }, indent=2)

@mcp.resource("security://events/latest")
async def get_latest_events() -> str:
    """Gets the most recent security events"""
    query = {
        "query": {
            "match_all": {}
        },
        "sort": [
            {"@timestamp": {"order": "desc"}}
        ],
        "size": 10
    }
    
    data = await query_elasticsearch(query)
    if not data:
        return json.dumps({"error": "Unable to query Elasticsearch"}, indent=2)
    
    results = []
    for hit in data["hits"]["hits"]:
        source = hit["_source"]
        results.append({
            "timestamp": source.get("@timestamp"),
            "event_type": source.get("event.type"),
            "event_action": source.get("event.action"),
            "process_name": source.get("process.name"),
            "process_pid": source.get("process.pid"),
            "hostname": source.get("host.name"),
            "severity": source.get("event.severity"),
            "outcome": source.get("event.outcome"),
            "message": source.get("message")
        })
    
    return json.dumps({
        "latest_events": results
    }, indent=2)

@mcp.resource("security://events/summary")
async def get_events_summary() -> str:
    """Get summary statistics for security events"""
    query = {
        "aggs": {
            "event_type_breakdown": {
                "terms": {
                    "field": "event.type",
                    "size": 10
                }
            },
            "severity_breakdown": {
                "terms": {
                    "field": "event.severity",
                    "size": 10
                }
            },
            "hostname_breakdown": {
                "terms": {
                    "field": "host.name",
                    "size": 10
                }
            }
        },
        "size": 0
    }
    
    data = await query_elasticsearch(query)
    if not data:
        return json.dumps({"error": "Unable to query Elasticsearch"}, indent=2)
    
    return json.dumps(data["aggregations"], indent=2)

# Tools
@mcp.tool()
async def query_security_events(params: QuerySecurityEventsParams) -> str:
    """
    Query security events with customizable parameters
    
    Args:
        start_date: Start datetime in YYYY-MM-DDTHH:MM:SS format
        end_date: End datetime in YYYY-MM-DDTHH:MM:SS format
        event_type: Type of event (process, network, file, host, alert)
        process_name: Filter by specific process name
        hostname: Filter by specific hostname
        severity: Filter by severity level (critical, high, medium, low, info)
    """
    # Extract parameters from model
    start_date = params.start_date
    end_date = params.end_date
    event_type = params.event_type
    process_name = params.process_name
    hostname = params.hostname
    severity = params.severity
    
    query = {"query": {"bool": {"must": []}}}
    filters = query["query"]["bool"]["must"]
    
    # Date range filter
    if start_date or end_date:
        range_obj = {}
        if start_date:
            range_obj["gte"] = start_date
        if end_date:
            range_obj["lte"] = end_date
        filters.append({"range": {"@timestamp": range_obj}})
    
    # Event type filter
    if event_type:
        filters.append({"match": {"event.type": event_type}})
    
    # Process name filter
    if process_name:
        filters.append({"wildcard": {"process.name": f"*{process_name}*"}})
    
    # Hostname filter
    if hostname:
        filters.append({"match": {"host.name": hostname}})
    
    # Severity filter
    if severity:
        filters.append({"match": {"event.severity": severity}})
    
    # If no filters, use match_all
    if not filters:
        query["query"] = {"match_all": {}}
    
    query.update({
        "sort": [{"@timestamp": "desc"}],
        "size": 20
    })
    
    data = await query_elasticsearch(query)
    if not data:
        return json.dumps({
            "error": "Unable to query Elasticsearch",
            "query": query
        }, indent=2)
    
    # Process results
    results = []
    for hit in data["hits"]["hits"]:
        source = hit["_source"]
        results.append({
            "timestamp": source.get("@timestamp"),
            "event_type": source.get("event.type"),
            "event_action": source.get("event.action"),
            "process_name": source.get("process.name"),
            "process_pid": source.get("process.pid"),
            "hostname": source.get("host.name"),
            "severity": source.get("event.severity"),
            "outcome": source.get("event.outcome"),
            "user": source.get("user.name"),
            "message": source.get("message"),
            "parent_process": source.get("process.parent.name"),
            "command_line": source.get("process.command_line")
        })
    
    return json.dumps({
        "filters_applied": {
            "event_type": event_type,
            "process_name": process_name,
            "hostname": hostname,
            "severity": severity,
            "date_range": f"{start_date} to {end_date}" if (start_date or end_date) else "all"
        },
        "total_records": data["hits"]["total"]["value"],
        "data": results,
        "query": query
    }, indent=2)

@mcp.tool()
async def get_suspicious_events() -> str:
    """Get all security events with high or critical severity"""
    query = {
        "query": {
            "bool": {
                "must": [
                    {"terms": {"event.severity": ["critical", "high"]}}
                ]
            }
        },
        "sort": [{"@timestamp": "desc"}],
        "size": 50
    }
    
    data = await query_elasticsearch(query)
    if not data:
        return json.dumps({"error": "Unable to query Elasticsearch"}, indent=2)
    
    results = []
    for hit in data["hits"]["hits"]:
        source = hit["_source"]
        results.append({
            "timestamp": source.get("@timestamp"),
            "severity": source.get("event.severity"),
            "event_type": source.get("event.type"),
            "process_name": source.get("process.name"),
            "hostname": source.get("host.name"),
            "message": source.get("message"),
            "outcome": source.get("event.outcome")
        })
    
    return json.dumps({
        "total_suspicious_events": data["hits"]["total"]["value"],
        "data": results
    }, indent=2)

# Pydantic model for ES|QL natural language generation
class NaturalLanguageQueryParams(BaseModel):
    query_description: str
    limit: Optional[int] = 100
    
    @field_validator('query_description')
    def validate_query_description(cls, value):
        if not value or len(value.strip()) == 0:
            raise ValueError("Query description cannot be empty")
        if len(value) > 500:
            raise ValueError("Query description too long, max 500 characters")
        return value

class ESQLQueryParams(BaseModel):
    esql_query: str
    limit: Optional[int] = 100
    
    @field_validator('esql_query')
    def validate_esql_query(cls, value):
        if not value or len(value.strip()) == 0:
            raise ValueError("ES|QL query cannot be empty")
        return value

@mcp.tool()
async def generate_esql_from_natural_language(params: NaturalLanguageQueryParams) -> str:
    """
    Convert natural language description to ES|QL query.
    This tool helps generate ES|QL queries from plain English descriptions.
    
    Args:
        query_description: Natural language description of what you want to query
        limit: Maximum number of results to return (default: 100)
    
    Examples:
        - "Show me all critical severity events from the last 24 hours"
        - "Find all processes executed by administrator users"
        - "List network connections from suspicious hosts"
    """
    description = params.query_description
    limit = params.limit or 100
    
    # AI-powered ES|QL suggestions based on common patterns
    esql_templates = {
        "critical": f"FROM {ES_INDEX} | WHERE event.severity == \"critical\" | LIMIT {limit}",
        "process execution": f"FROM {ES_INDEX} | WHERE event.type == \"process\" | KEEP @timestamp, process.name, process.pid, host.name | LIMIT {limit}",
        "network": f"FROM {ES_INDEX} | WHERE event.type == \"network\" | KEEP @timestamp, process.name, destination.ip, destination.port | LIMIT {limit}",
        "file": f"FROM {ES_INDEX} | WHERE event.type == \"file\" | KEEP @timestamp, process.name, file.path, file.name | LIMIT {limit}",
        "user activity": f"FROM {ES_INDEX} | WHERE user.name != null | KEEP @timestamp, user.name, process.name, event.action | LIMIT {limit}",
        "failed events": f"FROM {ES_INDEX} | WHERE event.outcome == \"failure\" | KEEP @timestamp, event.type, process.name, message | LIMIT {limit}",
        "suspicious": f"FROM {ES_INDEX} | WHERE event.severity IN (\"critical\", \"high\") | KEEP @timestamp, event.severity, process.name, host.name | LIMIT {limit}",
        "last 24 hours": f"FROM {ES_INDEX} | WHERE @timestamp > now() - 1 day | LIMIT {limit}",
        "last 7 days": f"FROM {ES_INDEX} | WHERE @timestamp > now() - 7 days | LIMIT {limit}",
    }
    
    # Find best matching template
    best_match = None
    best_score = 0
    description_lower = description.lower()
    
    for keyword, template in esql_templates.items():
        if keyword.lower() in description_lower:
            best_score = len(keyword)
            best_match = template
    
    # If no perfect match, create a generic query
    if not best_match:
        best_match = f"FROM {ES_INDEX} | LIMIT {limit}"
        suggestion = "Generic query - consider refining with specific keywords like 'critical', 'process', 'network', 'file', etc."
    else:
        suggestion = f"Generated based on keyword match: '{[k for k in esql_templates.keys() if k.lower() in description_lower][0]}'"
    
    return json.dumps({
        "natural_language_query": description,
        "generated_esql": best_match,
        "generation_note": suggestion,
        "limit": limit,
        "instructions": "Use the 'execute_esql_query' tool with the 'esql_query' parameter to run this query"
    }, indent=2)

@mcp.tool()
async def execute_esql_query(params: ESQLQueryParams) -> str:
    """
    Execute an ES|QL query against Elasticsearch security events.
    ES|QL is Elasticsearch Query Language for powerful, flexible querying.
    
    Args:
        esql_query: The ES|QL query to execute
        limit: Maximum number of results to return (default: 100)
    
    Common ES|QL patterns:
        - FROM logs-endpoint.events.* | LIMIT 10
        - FROM logs-endpoint.events.* | WHERE event.severity == "critical"
        - FROM logs-endpoint.events.* | STATS count() BY event.type
        - FROM logs-endpoint.events.* | WHERE @timestamp > now() - 1 day | STATS count() BY host.name
    """
    esql_query = params.esql_query
    limit = params.limit or 100
    
    try:
        async with get_es_client() as client:
            # Execute ES|QL query
            response = await client.perform_request(
                method="POST",
                url="/_query",
                body={
                    "query": esql_query,
                    "limit": limit
                }
            )
            
            # Format results
            columns = response.get("columns", [])
            values = response.get("values", [])
            
            results = []
            for row in values:
                result_row = {}
                for col, val in zip(columns, row):
                    result_row[col["name"]] = val
                results.append(result_row)
            
            return json.dumps({
                "esql_query": esql_query,
                "total_rows": len(results),
                "columns": [col["name"] for col in columns],
                "data": results,
                "execution_status": "success"
            }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "esql_query": esql_query,
            "error": str(e),
            "execution_status": "failed",
            "help": "Check ES|QL syntax. Common queries: FROM logs-endpoint.events.* | LIMIT 10"
        }, indent=2)

# Prompts
@mcp.prompt()
def security_alert_analysis(hostname: str = None) -> str:
    """Analyze security alerts for a specific host"""
    if hostname:
        return f"""Analyze the security events for host {hostname}. Provide:
1. Summary of high and critical severity events
2. Most common event types and processes
3. Any suspicious process execution patterns
4. Network activity anomalies
5. Recommendations for remediation or further investigation"""
    else:
        return """Analyze the latest security events across all hosts. Provide:
1. Summary of high and critical severity events
2. Most affected hosts and process names
3. Event type distribution
4. Any notable patterns or suspicious activity
5. Recommended priority actions"""

@mcp.prompt()
def threat_hunt_investigation(process_name: str, start_date: str) -> str:
    """Investigate a specific process for threat hunting"""
    return f"""Conduct a threat hunt investigation for process '{process_name}' starting from {start_date}.
Please include:
1. All execution instances of this process
2. Process parent-child relationships
3. Network connections established by this process
4. Files accessed or created
5. User accounts involved
6. Risk assessment and recommended actions"""

@mcp.prompt()
def incident_response_summary() -> str:
    """Generate an incident response summary"""
    return """Generate an incident response summary based on recent security events:
1. Timeline of key events
2. Affected systems and users
3. Severity assessment
4. Root cause analysis (if identifiable)
5. Recommended containment and remediation steps
6. Detection and prevention recommendations"""

# Main function to run the server
if __name__ == "__main__":
    mcp.run()