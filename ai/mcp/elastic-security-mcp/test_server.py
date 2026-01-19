#!/usr/bin/env python3
"""
Test suite for Elastic Security MCP Server
Tests all use cases from the specifications
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from server import translate_query

def test_use_case(name: str, query: str, expected_contains: list = None, should_fail: bool = False):
    """Test a specific use case"""
    print(f"\n=== {name} ===")
    print(f"Input: {query}")
    
    result = translate_query(query)
    
    if should_fail:
        if not result['success']:
            print(f"✅ PASS - Correctly rejected: {result['error']}")
        else:
            print(f"❌ FAIL - Should have been rejected but got: {result['query']}")
    else:
        if result['success']:
            print(f"✅ PASS - Generated query:")
            print(f"   {result['query']}")
            print(f"   Explanation: {result['explanation']}")
            
            if expected_contains:
                for expected in expected_contains:
                    if expected in result['query']:
                        print(f"   ✓ Contains: {expected}")
                    else:
                        print(f"   ❌ Missing: {expected}")
        else:
            print(f"❌ FAIL - Error: {result['error']}")

def run_tests():
    """Run all test cases from specifications"""
    
    print("🧪 Testing Elastic Security MCP Server")
    print("=" * 50)
    
    # UC-01: Basic Authentication Query
    test_use_case(
        "UC-01: Basic Authentication Success",
        "Show authentication successes from the last 24 hours",
        ["event.category == \"authentication\"", "event.outcome == \"success\"", "24h"]
    )
    
    # UC-02: Failed Authentication by User
    test_use_case(
        "UC-02: Failed Auth by User",
        "Show failed authentication attempts by user in the last 12 hours",
        ["event.outcome == \"failure\"", "STATS count() BY user.name", "12h"]
    )
    
    # UC-03: Protocol-Specific Authentication
    test_use_case(
        "UC-03: SSH Authentication",
        "Successful SSH logins in the last 6 hours",
        ["network.protocol == \"ssh\"", "event.outcome == \"success\"", "6h"]
    )
    
    # UC-04: Geographic Authentication Filtering
    test_use_case(
        "UC-04: Geographic Filtering",
        "Failed logins from China in the last day",
        ["geo.country == \"China\"", "event.outcome == \"failure\"", "24h"]
    )
    
    # UC-05: Multiple Countries (Impossible Travel)
    test_use_case(
        "UC-05: Multiple Countries",
        "Users logging in from multiple countries in the last 2 hours",
        ["STATS count() BY user.name", "2h"]
    )
    
    # UC-06: Raw Event Review
    test_use_case(
        "UC-06: Raw Events",
        "Show authentication events from last hour",
        ["event.category == \"authentication\"", "1h"]
    )
    
    # UC-07: Ambiguous Query Handling
    test_use_case(
        "UC-07: Ambiguous Query",
        "Show risky logins",
        should_fail=True
    )
    
    # UC-08: Policy Violation
    test_use_case(
        "UC-08: Unbounded Query",
        "Show all authentication logs",
        should_fail=True
    )
    
    # Additional edge cases
    test_use_case(
        "Edge Case: RDP Protocol",
        "Failed RDP connections in the past 3 hours",
        ["network.protocol == \"rdp\"", "event.outcome == \"failure\"", "3h"]
    )
    
    test_use_case(
        "Edge Case: Unsupported Protocol",
        "Telnet logins from yesterday",
        should_fail=True
    )
    
    test_use_case(
        "Edge Case: Long Time Range",
        "Authentication events from the last 30 days",
        should_fail=True
    )

if __name__ == "__main__":
    run_tests()