#!/usr/bin/env python3
import requests

ZITADEL_DOMAIN = 'https://auth-hfsb4v.us1.zitadel.cloud'
ZITADEL_PAT = 'm4TjyY8yIm4mmAH-PvDULvdsjFpD8-lDxB4R3LVmttk10jLDgYPOMAkoBhHwxG8w0mLgSCY'

print("Testing Zitadel API endpoints...")

# Test different endpoints
endpoints_to_test = [
    f'{ZITADEL_DOMAIN}/.well-known/openid_configuration',
    f'{ZITADEL_DOMAIN}/v2/users',
    f'{ZITADEL_DOMAIN}/management/v1/users/_search',
    f'{ZITADEL_DOMAIN}/admin/v1/users/_search'
]

headers = {'Authorization': f'Bearer {ZITADEL_PAT}', 'Content-Type': 'application/json'}

for endpoint in endpoints_to_test:
    try:
        if 'well-known' in endpoint:
            response = requests.get(endpoint, timeout=10)
        else:
            response = requests.post(endpoint, headers=headers, json={}, timeout=10)
        
        print(f"{endpoint}: {response.status_code}")
        if response.status_code < 400:
            print(f"  ✅ Success")
        else:
            print(f"  ❌ Error: {response.text[:100]}")
    except Exception as e:
        print(f"{endpoint}: ❌ Exception: {e}")

print("\nTrying to list users with different API versions...")

# Try v2 API
try:
    response = requests.post(
        f'{ZITADEL_DOMAIN}/v2/users',
        headers=headers,
        json={'query': {'limit': 5}},
        timeout=10
    )
    print(f"v2 API: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Found users: {len(data.get('result', []))}")
    else:
        print(f"  Error: {response.text}")
except Exception as e:
    print(f"v2 API: Exception: {e}")

# Try management API
try:
    response = requests.post(
        f'{ZITADEL_DOMAIN}/management/v1/users/_search',
        headers=headers,
        json={'limit': 5},
        timeout=10
    )
    print(f"Management API: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Found users: {len(data.get('result', []))}")
    else:
        print(f"  Error: {response.text}")
except Exception as e:
    print(f"Management API: Exception: {e}")