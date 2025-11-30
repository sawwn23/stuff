#!/usr/bin/env python3
import requests
import json

ZITADEL_DOMAIN = 'https://auth-hfsb4v.us1.zitadel.cloud'
ZITADEL_PAT = 'm4TjyY8yIm4mmAH-PvDULvdsjFpD8-lDxB4R3LVmttk10jLDgYPOMAkoBhHwxG8w0mLgSCY'

headers = {'Authorization': f'Bearer {ZITADEL_PAT}', 'Content-Type': 'application/json'}

print("Checking service account permissions...")

# Test different API endpoints to see what we can access
endpoints_to_test = [
    ('Users (v2)', f'{ZITADEL_DOMAIN}/v2/users', {'query': {'limit': 5}}),
    ('My User', f'{ZITADEL_DOMAIN}/v2/users/me', {}),
    ('Organizations', f'{ZITADEL_DOMAIN}/admin/v1/orgs/_search', {'limit': 5}),
    ('Projects', f'{ZITADEL_DOMAIN}/management/v1/projects/_search', {'limit': 5}),
]

for name, endpoint, payload in endpoints_to_test:
    try:
        if payload:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=10)
        else:
            response = requests.get(endpoint, headers=headers, timeout=10)
        
        print(f"\n{name}:")
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'result' in data:
                print(f"  ✅ Success - Found {len(data['result'])} items")
                if name == 'Users (v2)' and data['result']:
                    print("  Users found:")
                    for user in data['result'][:3]:  # Show first 3 users
                        user_type = 'Human' if 'human' in user else 'Machine'
                        print(f"    - {user.get('username', 'N/A')} ({user_type})")
            else:
                print(f"  ✅ Success - Response: {str(data)[:100]}...")
        elif response.status_code == 403:
            print(f"  ❌ Forbidden - Need more permissions")
        elif response.status_code == 404:
            print(f"  ❌ Not Found - Endpoint may not exist or no access")
        else:
            print(f"  ❌ Error: {response.text[:100]}")
            
    except Exception as e:
        print(f"  ❌ Exception: {e}")

print("\n" + "="*50)
print("DIAGNOSIS:")
print("If 'Users (v2)' shows 'Forbidden' or only shows machine users,")
print("your service account needs ORG_USER_MANAGER role.")
print("\nTo fix:")
print("1. Go to Zitadel Console")
print("2. Navigate to Organization > Members")
print("3. Add service account 'sa' with role 'ORG_USER_MANAGER'")