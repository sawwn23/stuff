#!/usr/bin/env python3
import requests
import json

ZITADEL_DOMAIN = 'https://auth-hfsb4v.us1.zitadel.cloud'
ZITADEL_PAT = 'm4TjyY8yIm4mmAH-PvDULvdsjFpD8-lDxB4R3LVmttk10jLDgYPOMAkoBhHwxG8w0mLgSCY'

headers = {'Authorization': f'Bearer {ZITADEL_PAT}', 'Content-Type': 'application/json'}

print("Fetching user data to see structure...")

response = requests.post(
    f'{ZITADEL_DOMAIN}/v2/users',
    headers=headers,
    json={'query': {'limit': 5}},
    timeout=10
)

if response.status_code == 200:
    data = response.json()
    print("Response structure:")
    print(json.dumps(data, indent=2))
else:
    print(f"Error: {response.status_code} - {response.text}")