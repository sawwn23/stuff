#!/usr/bin/env python3
import requests
import json

ZITADEL_DOMAIN = 'https://auth-hfsb4v.us1.zitadel.cloud'
ZITADEL_PAT = 'm4TjyY8yIm4mmAH-PvDULvdsjFpD8-lDxB4R3LVmttk10jLDgYPOMAkoBhHwxG8w0mLgSCY'

headers = {'Authorization': f'Bearer {ZITADEL_PAT}', 'Content-Type': 'application/json'}

print("Fetching detailed user data from Zitadel...")

response = requests.post(
    f'{ZITADEL_DOMAIN}/v2/users',
    headers=headers,
    json={'query': {'limit': 10}},
    timeout=10
)

if response.status_code == 200:
    data = response.json()
    print(f"Total users found: {len(data.get('result', []))}")
    
    for i, user in enumerate(data.get('result', [])):
        print(f"\n--- User {i+1} ---")
        print(f"Raw data: {json.dumps(user, indent=2)}")
        
        # Process like the script does
        user_id = user.get('userId')
        print(f"User ID: {user_id}")
        print(f"Username: {user.get('username')}")
        print(f"State: {user.get('state')}")
        
        if 'human' in user:
            print("Type: Human user")
            human_data = user.get('human', {})
            email_data = human_data.get('email', {})
            
            print(f"First name: {human_data.get('firstName', 'N/A')}")
            print(f"Last name: {human_data.get('lastName', 'N/A')}")
            print(f"Email: {email_data.get('email', 'N/A')}")
            print(f"Email verified: {email_data.get('isEmailVerified', 'N/A')}")
            
            # Check if this user would be processed
            if not user.get('username') or not email_data.get('email'):
                print("❌ WOULD BE SKIPPED: Missing username or email")
            else:
                print("✅ WOULD BE PROCESSED")
                
        elif 'machine' in user:
            print("Type: Machine user (service account)")
            print("❌ WOULD BE SKIPPED: Machine users not synced")
        else:
            print("Type: Unknown")
            print("❌ WOULD BE SKIPPED: Unknown user type")
else:
    print(f"Error: {response.status_code} - {response.text}")