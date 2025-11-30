#!/usr/bin/env python3
import requests
import json

AWS_SCIM_ENDPOINT = 'https://scim.ca-central-1.amazonaws.com/bdhf3c444cd-9c12-4afa-a19c-6604347ebb99/scim/v2'
AWS_SCIM_TOKEN = 'd16e6382-3c2a-479b-b31f-86bb6051405a:1bbe7903-f6fe-4da4-81a5-4693f5378cfd:3cjzJOxfG1SDEmyQZMIzK4iRnSuXUfxA9ZqSeEgoJRe2xo5YHb5MZi2wECdCOj3Uu3HUpHXSeHcXd8XrOahrlKal4vFZzyheyXQFDYNFNohj7bqPWyWJ4Zepmg7OidAhSjMvXtpAQHkfAhBCp9uhcTlgJ6T+6NYd+a6x+v6F9cZ1jg3PxANpUEg=:GjjJTHMsCgxh/DKQflDlYqsSXfeZXUdfpWzSniBFDU3BBQn1sWr5Me4SRIb8026O/Km2RiSZ7e13IaLgrgoO7t+d87P5HAS6vpZlrZCWAAmu61G65Twt0ULXzf70Zm6ktYzm/uo1G+3fuW0U8zEp1XPGxModbssr6EkEVGIlPrtikPuUPj6VaTrOEKqEyaDR3qBE8moa567sHX/XEj9MQ9Z3d2sR7MYvS24GITcyJ9GKwJV7MvU3hlrxqACyKVpjiLZGrWAnxvV49GDD5ijbOO4+rLYzXfv3LJyt6x5e8hJzfi7R1VNWzRbzhxwWrK+cr28cnjBSd0Lc6hftvY/FGA=='

headers = {'Authorization': f'Bearer {AWS_SCIM_TOKEN}', 'Content-Type': 'application/scim+json'}

print("Testing AWS SCIM API...")

# Test 1: List existing users
print("\n1. Testing GET /Users (list existing users)")
try:
    response = requests.get(f'{AWS_SCIM_ENDPOINT}/Users', headers=headers, timeout=30)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success - Found {len(data.get('Resources', []))} existing users")
        print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"❌ Error: {response.text}")
except Exception as e:
    print(f"❌ Exception: {e}")

# Test 2: Create a test user
print("\n2. Testing POST /Users (create user)")
test_user = {
    'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
    'userName': 'test-user-123',
    'name': {'givenName': 'Test', 'familyName': 'User'},
    'emails': [{'value': 'test@example.com', 'primary': True}],
    'active': True
}

try:
    response = requests.post(f'{AWS_SCIM_ENDPOINT}/Users', headers=headers, json=test_user, timeout=30)
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        print("✅ Success - User created")
        created_user = response.json()
        print(f"Created user ID: {created_user.get('id')}")
        
        # Clean up - delete the test user
        user_id = created_user.get('id')
        if user_id:
            delete_response = requests.delete(f'{AWS_SCIM_ENDPOINT}/Users/{user_id}', headers=headers, timeout=30)
            print(f"Cleanup delete status: {delete_response.status_code}")
    else:
        print(f"❌ Error: {response.text}")
except Exception as e:
    print(f"❌ Exception: {e}")

# Test 3: Check SCIM endpoint health
print("\n3. Testing SCIM endpoint health")
try:
    response = requests.get(f'{AWS_SCIM_ENDPOINT}/ServiceProviderConfig', headers=headers, timeout=30)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ SCIM endpoint is healthy")
    else:
        print(f"❌ SCIM endpoint issue: {response.text}")
except Exception as e:
    print(f"❌ Exception: {e}")

print("\n" + "="*50)
print("AWS SCIM DIAGNOSIS:")
print("If all tests pass, the AWS SCIM endpoint is working correctly.")
print("If tests fail, check:")
print("1. AWS SCIM token is valid and not expired")
print("2. AWS Identity Center SCIM endpoint is correctly configured")
print("3. Network connectivity to AWS")