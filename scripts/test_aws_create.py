#!/usr/bin/env python3
import requests
import json

AWS_SCIM_ENDPOINT = 'https://scim.ca-central-1.amazonaws.com/bdhf3c444cd-9c12-4afa-a19c-6604347ebb99/scim/v2'
AWS_SCIM_TOKEN = 'd16e6382-3c2a-479b-b31f-86bb6051405a:1bbe7903-f6fe-4da4-81a5-4693f5378cfd:3cjzJOxfG1SDEmyQZMIzK4iRnSuXUfxA9ZqSeEgoJRe2xo5YHb5MZi2wECdCOj3Uu3HUpHXSeHcXd8XrOahrlKal4vFZzyheyXQFDYNFNohj7bqPWyWJ4Zepmg7OidAhSjMvXtpAQHkfAhBCp9uhcTlgJ6T+6NYd+a6x+v6F9cZ1jg3PxANpUEg=:GjjJTHMsCgxh/DKQflDlYqsSXfeZXUdfpWzSniBFDU3BBQn1sWr5Me4SRIb8026O/Km2RiSZ7e13IaLgrgoO7t+d87P5HAS6vpZlrZCWAAmu61G65Twt0ULXzf70Zm6ktYzm/uo1G+3fuW0U8zEp1XPGxModbssr6EkEVGIlPrtikPuUPj6VaTrOEKqEyaDR3qBE8moa567sHX/XEj9MQ9Z3d2sR7MYvS24GITcyJ9GKwJV7MvU3hlrxqACyKVpjiLZGrWAnxvV49GDD5ijbOO4+rLYzXfv3LJyt6x5e8hJzfi7R1VNWzRbzhxwWrK+cr28cnjBSd0Lc6hftvY/FGA=='

headers = {'Authorization': f'Bearer {AWS_SCIM_TOKEN}', 'Content-Type': 'application/scim+json'}

print("Testing AWS SCIM user creation with displayName...")

# Test with correct SCIM format including displayName
test_user = {
    'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
    'userName': 'test-user-456',
    'displayName': 'Test User',
    'name': {'givenName': 'Test', 'familyName': 'User'},
    'emails': [{'value': 'test456@example.com', 'primary': True}],
    'active': True
}

try:
    response = requests.post(f'{AWS_SCIM_ENDPOINT}/Users', headers=headers, json=test_user, timeout=30)
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        print("✅ Success - User created with displayName")
        created_user = response.json()
        print(f"Created user: {created_user.get('userName')} (ID: {created_user.get('id')})")
        
        # Clean up - delete the test user
        user_id = created_user.get('id')
        if user_id:
            print("Cleaning up test user...")
            delete_response = requests.delete(f'{AWS_SCIM_ENDPOINT}/Users/{user_id}', headers=headers, timeout=30)
            print(f"Delete status: {delete_response.status_code}")
    else:
        print(f"❌ Error: {response.text}")
except Exception as e:
    print(f"❌ Exception: {e}")