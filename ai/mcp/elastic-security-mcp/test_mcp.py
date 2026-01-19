#!/usr/bin/env python3
"""
Test the MCP server functionality without running the full server
"""

import json
from server import (
    NLParser, QueryIntent, generate_esql, validate_query_intent,
    SCHEMAS, HUNTING_TEMPLATES, ValidationPolicy
)

def test_nl_parsing():
    """Test natural language parsing"""
    print("🧪 Testing Natural Language Parsing")
    print("=" * 40)
    
    parser = NLParser()
    
    test_cases = [
        "Show failed SSH logins from China in the last 6 hours",
        "Processes spawned by powershell in the last 2 hours", 
        "Authentication successes from the last 24 hours",
        "Failed authentication attempts by user in the last 12 hours"
    ]
    
    for query in test_cases:
        print(f"\nQuery: {query}")
        intent = parser.parse(query)
        print(f"  Category: {intent.category}")
        print(f"  Outcome: {intent.outcome}")
        print(f"  Time: {intent.time_range}")
        print(f"  Index: {intent.index_pattern}")
        print(f"  Filters: {len(intent.filters)}")
        if intent.filters:
            for f in intent.filters:
                print(f"    {f['field']} {f['operator']} {f['value']}")

def test_esql_generation():
    """Test ES|QL query generation"""
    print("\n\n🔧 Testing ES|QL Generation")
    print("=" * 35)
    
    # Test case 1: Basic auth query
    intent = QueryIntent(
        category="authentication",
        outcome="failure", 
        time_range="last_6_hours",
        index_pattern="logs-auth-*",
        filters=[
            {"field": "source.geo.country_name", "operator": "==", "value": "China"},
            {"field": "network.protocol", "operator": "==", "value": "ssh"}
        ]
    )
    
    query = generate_esql(intent)
    print(f"Generated Query:\n{query}")
    
    # Test case 2: Aggregation query
    intent2 = QueryIntent(
        category="authentication",
        outcome="failure",
        time_range="last_12_hours", 
        index_pattern="logs-auth-*",
        aggregation={
            "type": "stats",
            "function": "count()",
            "group_by": ["user.name"]
        }
    )
    
    query2 = generate_esql(intent2)
    print(f"\nAggregation Query:\n{query2}")

def test_validation():
    """Test query validation"""
    print("\n\n✅ Testing Validation")
    print("=" * 25)
    
    # Valid intent
    valid_intent = QueryIntent(
        category="authentication",
        time_range="last_24_hours",
        index_pattern="logs-auth-*"
    )
    
    is_valid, errors = validate_query_intent(valid_intent)
    print(f"Valid intent: {is_valid}, Errors: {errors}")
    
    # Invalid intent (no time range)
    invalid_intent = QueryIntent(
        category="authentication",
        index_pattern="logs-auth-*"
    )
    
    is_valid, errors = validate_query_intent(invalid_intent)
    print(f"Invalid intent: {is_valid}, Errors: {errors}")

def test_schemas():
    """Test schema information"""
    print("\n\n📋 Testing Schemas")
    print("=" * 20)
    
    for index, schema in SCHEMAS.items():
        print(f"\n{index}:")
        print(f"  Description: {schema['description']}")
        print(f"  Fields: {len(schema['fields'])}")
        print(f"  Sample fields: {schema['fields'][:5]}")

def test_templates():
    """Test hunting templates"""
    print("\n\n🎯 Testing Templates")
    print("=" * 22)
    
    for name, template in HUNTING_TEMPLATES.items():
        print(f"\n{name}:")
        print(f"  Category: {template['category']}")
        print(f"  Description: {template['description']}")

def test_complete_workflow():
    """Test complete NL to ES|QL workflow"""
    print("\n\n🔄 Testing Complete Workflow")
    print("=" * 32)
    
    query = "Show failed SSH logins from China in the last 6 hours"
    print(f"Input: {query}")
    
    # Step 1: Parse
    parser = NLParser()
    intent = parser.parse(query)
    print(f"✓ Parsed intent: {intent.category}, {intent.outcome}")
    
    # Step 2: Validate
    is_valid, errors = validate_query_intent(intent)
    print(f"✓ Validation: {is_valid}")
    
    if is_valid:
        # Step 3: Generate ES|QL
        esql = generate_esql(intent)
        print(f"✓ Generated ES|QL:\n  {esql}")
        
        # Step 4: Explain
        explanation = f"Searching {intent.category} events with {intent.outcome} outcome from the last 6 hours from China using SSH protocol"
        print(f"✓ Explanation: {explanation}")
    else:
        print(f"✗ Validation failed: {errors}")

if __name__ == "__main__":
    test_nl_parsing()
    test_esql_generation()
    test_validation()
    test_schemas()
    test_templates()
    test_complete_workflow()
    
    print("\n\n🎉 All tests completed!")
    print("\nTo run the MCP server:")
    print("python server.py")