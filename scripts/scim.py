import requests
import json
import os
import logging
import time
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration from environment variables
ZITADEL_DOMAIN = os.getenv('ZITADEL_DOMAIN', 'https://auth-hfsb4v.us1.zitadel.cloud')
ZITADEL_PAT = os.getenv('ZITADEL_PAT', 'm4TjyY8yIm4mmAH-PvDULvdsjFpD8-lDxB4R3LVmttk10jLDgYPOMAkoBhHwxG8w0mLgSCY')
ZITADEL_SERVICE_ACCOUNT_ID = os.getenv('ZITADEL_SERVICE_ACCOUNT_ID')
ZITADEL_SERVICE_ACCOUNT_KEY = os.getenv('ZITADEL_SERVICE_ACCOUNT_KEY')
ZITADEL_PROJECT_ID = os.getenv('ZITADEL_PROJECT_ID')
AWS_SCIM_ENDPOINT = os.getenv('AWS_SCIM_ENDPOINT', 'https://scim.ca-central-1.amazonaws.com/bdhf3c444cd-9c12-4afa-a19c-6604347ebb99/scim/v2')
AWS_SCIM_TOKEN = os.getenv('AWS_SCIM_TOKEN', 'd16e6382-3c2a-479b-b31f-86bb6051405a:1bbe7903-f6fe-4da4-81a5-4693f5378cfd:3cjzJOxfG1SDEmyQZMIzK4iRnSuXUfxA9ZqSeEgoJRe2xo5YHb5MZi2wECdCOj3Uu3HUpHXSeHcXd8XrOahrlKal4vFZzyheyXQFDYNFNohj7bqPWyWJ4Zepmg7OidAhSjMvXtpAQHkfAhBCp9uhcTlgJ6T+6NYd+a6x+v6F9cZ1jg3PxANpUEg=:GjjJTHMsCgxh/DKQflDlYqsSXfeZXUdfpWzSniBFDU3BBQn1sWr5Me4SRIb8026O/Km2RiSZ7e13IaLgrgoO7t+d87P5HAS6vpZlrZCWAAmu61G65Twt0ULXzf70Zm6ktYzm/uo1G+3fuW0U8zEp1XPGxModbssr6EkEVGIlPrtikPuUPj6VaTrOEKqEyaDR3qBE8moa567sHX/XEj9MQ9Z3d2sR7MYvS24GITcyJ9GKwJV7MvU3hlrxqACyKVpjiLZGrWAnxvV49GDD5ijbOO4+rLYzXfv3LJyt6x5e8hJzfi7R1VNWzRbzhxwWrK+cr28cnjBSd0Lc6hftvY/FGA==')
STATE_FILE = os.getenv('STATE_FILE', 'state.json')
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
RATE_LIMIT_DELAY = float(os.getenv('RATE_LIMIT_DELAY', '0.5'))

logger.info("Configuration loaded successfully")

def get_zitadel_access_token() -> Optional[str]:
    """Get access token using service account JWT authentication."""
    # Check if we have a PAT token as fallback
    if ZITADEL_PAT:
        logger.info("Using PAT token for authentication")
        return ZITADEL_PAT
    
    if not ZITADEL_SERVICE_ACCOUNT_ID or not ZITADEL_SERVICE_ACCOUNT_KEY:
        logger.error("Neither PAT token nor service account credentials provided. Please set ZITADEL_PAT or (ZITADEL_SERVICE_ACCOUNT_ID and ZITADEL_SERVICE_ACCOUNT_KEY)")
        return None
    
    try:
        # Parse the service account key (should be JSON)
        if isinstance(ZITADEL_SERVICE_ACCOUNT_KEY, str):
            key_data = json.loads(ZITADEL_SERVICE_ACCOUNT_KEY)
        else:
            key_data = ZITADEL_SERVICE_ACCOUNT_KEY
        
        # Create JWT assertion
        now = datetime.utcnow()
        payload = {
            'iss': ZITADEL_SERVICE_ACCOUNT_ID,
            'sub': ZITADEL_SERVICE_ACCOUNT_ID,
            'aud': f'{ZITADEL_DOMAIN}',
            'iat': now,
            'exp': now + timedelta(minutes=5)
        }
        
        # Sign the JWT
        assertion = jwt.encode(payload, key_data['key'], algorithm='RS256', headers={'kid': key_data['keyId']})
        
        # Exchange JWT for access token
        token_data = {
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'assertion': assertion,
            'scope': 'openid profile urn:zitadel:iam:org:project:id:zitadel:aud'
        }
        
        response = requests.post(
            f'{ZITADEL_DOMAIN}/oauth/v2/token',
            data=token_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        if response.status_code == 200:
            token_response = response.json()
            return token_response['access_token']
        else:
            logger.error(f"Failed to get access token: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting access token: {e}")
        return None

def test_zitadel_connection() -> bool:
    """Test basic connectivity to Zitadel API."""
    logger.info("Testing Zitadel connection...")
    
    # Test with actual API call since well-known endpoint returns 404
    access_token = get_zitadel_access_token()
    if not access_token:
        logger.error("Cannot get access token")
        return False
    
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    response = make_request_with_retry('POST', f'{ZITADEL_DOMAIN}/v2/users', headers, json={'query': {'limit': 1}})
    
    if response and response.status_code == 200:
        logger.info("Zitadel API connection successful")
        return True
    else:
        logger.error(f"Cannot connect to Zitadel API: {response.status_code if response else 'No response'}")
        return False

def load_state() -> Dict:
    """Load previous sync state from file."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load state file: {e}. Starting fresh.")
    return {'users': {}}

def save_state(state: Dict) -> None:
    """Save current sync state to file."""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        logger.info("State saved successfully")
    except IOError as e:
        logger.error(f"Failed to save state: {e}")

def make_request_with_retry(method: str, url: str, headers: Dict, **kwargs) -> Optional[requests.Response]:
    """Make HTTP request with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            time.sleep(RATE_LIMIT_DELAY)  # Rate limiting
            logger.debug(f"Making {method} request to {url}")
            response = requests.request(method, url, headers=headers, timeout=30, **kwargs)
            logger.debug(f"Response status: {response.status_code}")
            if response.status_code < 500:  # Don't retry client errors
                return response
            logger.warning(f"Server error {response.status_code}, attempt {attempt + 1}/{MAX_RETRIES}")
        except requests.RequestException as e:
            logger.warning(f"Request failed, attempt {attempt + 1}/{MAX_RETRIES}: {e}")
        
        if attempt < MAX_RETRIES - 1:
            time.sleep(2 ** attempt)  # Exponential backoff
    
    logger.error(f"Failed to complete request after {MAX_RETRIES} attempts to {url}")
    return None

# Load previous state
previous_state = load_state()

def fetch_zitadel_users() -> Dict[str, Dict]:
    """Fetch all users from ZITADEL with pagination."""
    access_token = get_zitadel_access_token()
    if not access_token:
        logger.error("Failed to get Zitadel access token")
        return {}
    
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    zitadel_users = {}
    offset = 0
    limit = 100
    
    while True:
        logger.info(f"Fetching ZITADEL users, offset: {offset}")
        
        # Try the original API call format first
        payload = {
            'query': {'limit': limit, 'offset': offset}
        }
        
        response = make_request_with_retry('POST', f'{ZITADEL_DOMAIN}/v2/users', headers, json=payload)
        
        if not response:
            logger.error('No response from ZITADEL API')
            return None
            
        if response.status_code != 200:
            logger.error(f'Error fetching ZITADEL users: Status {response.status_code}, Response: {response.text}')
            # Try alternative endpoint format
            logger.info("Trying alternative API endpoint...")
            alt_response = make_request_with_retry('POST', f'{ZITADEL_DOMAIN}/v2/users/search', headers, json=payload)
            if alt_response and alt_response.status_code == 200:
                response = alt_response
            else:
                return None
        
        data = response.json()
        users = data.get('result', [])
        
        if not users:
            break
            
        for user in users:
            user_id = user.get('userId')
            if not user_id:
                logger.warning("Skipping user without userId")
                continue
            
            # Check if it's a human user (has 'human' field) or machine user
            if 'human' in user:
                # Human user
                human_data = user.get('human', {})
                profile_data = human_data.get('profile', {})
                email_data = human_data.get('email', {})
                
                # Skip users without required fields
                if not user.get('username') or not email_data.get('email'):
                    logger.warning(f"Skipping human user {user_id}: missing username or email")
                    continue
                    
                zitadel_users[user_id] = {
                    'username': user.get('username'),
                    'first_name': profile_data.get('givenName', ''),
                    'last_name': profile_data.get('familyName', ''),
                    'email': email_data.get('email'),
                    'active': user.get('state') == 'USER_STATE_ACTIVE'
                }
            elif 'machine' in user:
                # Machine user (service account) - skip for SCIM sync
                logger.info(f"Skipping machine user: {user.get('username')}")
                continue
            else:
                logger.warning(f"Unknown user type for user {user_id}")
                continue
        
        offset += limit
        if len(users) < limit:  # Last page
            break
    
    logger.info(f"Fetched {len(zitadel_users)} users from ZITADEL")
    return zitadel_users

# Step 1: Test connection and fetch users from ZITADEL
if not test_zitadel_connection():
    logger.error("Cannot connect to Zitadel. Please check your domain and network connectivity.")
    exit(1)

zitadel_users = fetch_zitadel_users()
if zitadel_users is None:
    logger.error("Failed to fetch users from ZITADEL")
    exit(1)
elif len(zitadel_users) == 0:
    logger.info("No human users found in ZITADEL to sync")
    logger.info("Create some human users in your Zitadel instance to test the sync")
    exit(0)

def fetch_aws_users() -> Dict[str, str]:
    """Fetch existing AWS users for comparison."""
    scim_headers = {'Authorization': f'Bearer {AWS_SCIM_TOKEN}', 'Content-Type': 'application/scim+json'}
    current_aws_users = {}
    
    logger.info("Fetching existing AWS users")
    response = make_request_with_retry('GET', f'{AWS_SCIM_ENDPOINT}/Users', scim_headers)
    
    if not response or response.status_code != 200:
        logger.error(f'Error fetching AWS users: {response.text if response else "No response"}')
        return {}
    
    aws_data = response.json()
    for resource in aws_data.get('Resources', []):
        current_aws_users[resource['userName']] = resource['id']
    
    logger.info(f"Found {len(current_aws_users)} existing AWS users")
    return current_aws_users

# Step 2: Sync to AWS SCIM
scim_headers = {'Authorization': f'Bearer {AWS_SCIM_TOKEN}', 'Content-Type': 'application/scim+json'}
current_aws_users = fetch_aws_users()

def sync_user_to_aws(user: Dict, scim_headers: Dict) -> bool:
    """Sync a single user to AWS SCIM."""
    # Create display name from first and last name, fallback to username
    display_name = f"{user['first_name']} {user['last_name']}".strip()
    if not display_name:
        display_name = user['username']
    
    scim_user = {
        'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
        'userName': user['username'],
        'displayName': display_name,
        'name': {'givenName': user['first_name'], 'familyName': user['last_name']},
        'emails': [{'value': user['email'], 'primary': True}],
        'active': user['active']
    }
    
    # Check if user exists in AWS
    filter_query = f'userName eq "{user["username"]}"'
    check_resp = make_request_with_retry('GET', f'{AWS_SCIM_ENDPOINT}/Users?filter={filter_query}', scim_headers)
    
    if not check_resp:
        logger.error(f"Failed to check user existence: {user['username']}")
        return False
    
    if check_resp.status_code == 200 and check_resp.json().get('totalResults', 0) > 0:
        # Update existing user
        aws_id = check_resp.json()['Resources'][0]['id']
        patch_body = {
            'schemas': ['urn:ietf:params:scim:api:messages:2.0:PatchOp'],
            'Operations': [{'op': 'replace', 'value': scim_user}]
        }
        update_resp = make_request_with_retry('PATCH', f'{AWS_SCIM_ENDPOINT}/Users/{aws_id}', scim_headers, json=patch_body)
        
        if update_resp and update_resp.status_code in [200, 204]:
            logger.info(f'Updated user: {user["username"]}')
            return True
        else:
            logger.error(f'Failed to update user {user["username"]}: {update_resp.status_code if update_resp else "No response"}')
            return False
    else:
        # Create new user
        create_resp = make_request_with_retry('POST', f'{AWS_SCIM_ENDPOINT}/Users', scim_headers, json=scim_user)
        
        if create_resp and create_resp.status_code == 201:
            logger.info(f'Created user: {user["username"]}')
            return True
        else:
            logger.error(f'Failed to create user {user["username"]}: {create_resp.status_code if create_resp else "No response"}')
            return False

# Process creates/updates
success_count = 0
for user_id, user in zitadel_users.items():
    if sync_user_to_aws(user, scim_headers):
        success_count += 1

logger.info(f"Successfully synced {success_count}/{len(zitadel_users)} users")

# Process deletions (compare with previous state)
deleted_count = 0
for prev_id, prev_user in previous_state.get('users', {}).items():
    if prev_id not in zitadel_users:
        username = prev_user.get('username')
        if username and username in current_aws_users:
            aws_id = current_aws_users[username]
            delete_resp = make_request_with_retry('DELETE', f'{AWS_SCIM_ENDPOINT}/Users/{aws_id}', scim_headers)
            
            if delete_resp and delete_resp.status_code in [200, 204]:
                logger.info(f'Deleted user: {username}')
                deleted_count += 1
            else:
                logger.error(f'Failed to delete user {username}: {delete_resp.status_code if delete_resp else "No response"}')

logger.info(f"Deleted {deleted_count} users from AWS")

# Save new state
save_state({'users': zitadel_users})
logger.info("Sync completed successfully")