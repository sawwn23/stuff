#!/usr/bin/env python3
"""
Simple test script to verify Zitadel connection and credentials
"""
import requests
import json
import os

ZITADEL_DOMAIN = 'https://auth-hfsb4v.us1.zitadel.cloud'

def test_basic_connection():
    """Test if we can reach Zitadel"""
    print("Testing basic connection to Zitadel...")
    try:
        response = requests.get(f'{ZITADEL_DOMAIN}/.well-known/openid_configuration', timeout=10)
        if response.status_code == 200:
            print("✅ Zitadel endpoint is reachable")
            config = response.json()
            print(f"   Issuer: {config.get('issuer')}")
            print(f"   Token endpoint: {config.get('token_endpoint')}")
            return True
        else:
            print(f"❌ Failed to reach Zitadel: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_with_pat():
    """Test with PAT token if available"""
    pat_token = os.getenv('ZITADEL_PAT')
    if not pat_token:
        print("No ZITADEL_PAT environment variable found")
        return False
    
    print("Testing with PAT token...")
    headers = {'Authorization': f'Bearer {pat_token}', 'Content-Type': 'application/json'}
    
    try:
        # Try to list users
        response = requests.post(
            f'{ZITADEL_DOMAIN}/v2/users',
            headers=headers,
            json={'query': {'limit': 1, 'offset': 0}},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ PAT token authentication successful")
            data = response.json()
            print(f"   Found {len(data.get('result', []))} users in first page")
            return True
        else:
            print(f"❌ PAT authentication failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ PAT test error: {e}")
        return False

if __name__ == "__main__":
    print("=== Zitadel Connection Test ===")
    
    # Test basic connection
    if not test_basic_connection():
        exit(1)
    
    # Test PAT if available
    test_with_pat()
    
    print("\n=== Service Account Setup ===")
    print("To use service account authentication:")
    print("1. Go to your Zitadel project")
    print("2. Navigate to Service Accounts")
    print("3. Find your 'sa' service account")
    print("4. Note the Service Account ID (looks like: 123456789012345678@projectname)")
    print("5. Create/download a key for this service account")
    print("6. Set environment variables:")
    print("   export ZITADEL_SERVICE_ACCOUNT_ID='your_service_account_id'")
    print("   export ZITADEL_SERVICE_ACCOUNT_KEY='{\"keyId\":\"...\",\"key\":\"-----BEGIN RSA PRIVATE KEY-----\\n...\\n-----END RSA PRIVATE KEY-----\"}'")