import secrets
import string
import json
import sys
import os
import hashlib
import hmac

CREDENTIALS_FILE = "xiaoice_credentials.json"

def generate_key():
    """Generate a secure 64-character hex string."""
    return secrets.token_hex(32)

def generate_deterministic_key(project_id, seed, key_type):
    """Generate a deterministic 64-character hex string based on project_id, seed and key_type."""
    msg = f"{project_id}_{key_type}".encode('utf-8')
    key = seed.encode('utf-8')
    return hmac.new(key, msg, hashlib.sha256).hexdigest()

def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {CREDENTIALS_FILE}: {e}")
            return {}
    return {}

def save_credentials(creds):
    with open(CREDENTIALS_FILE, 'w') as f:
        json.dump(creds, f, indent=2)

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_keys.py [optional_hash_seed] <project_id1,project_id2,...>")
        print("Example: python generate_keys.py Summer,Alita")
        print("Example with seed: python generate_keys.py my_secret_seed_123 Summer")
        sys.exit(1)
        
    if len(sys.argv) == 3:
        seed = sys.argv[1]
        project_ids_str = sys.argv[2]
    else:
        seed = None
        project_ids_str = sys.argv[1]
        
    project_ids = [pid.strip() for pid in project_ids_str.split(",") if pid.strip()]
    
    creds = load_credentials()
    
    # Map existing project IDs to their access keys for easy lookup
    existing_projects = {}
    for access_key, data in creds.items():
        existing_projects[data["project_id"]] = access_key
        
    results = {}

    for project_id in project_ids:
        if project_id in existing_projects:
            print(f"\n--- Existing Credentials Found ---")
            access_key = existing_projects[project_id]
            secret_key = creds[access_key]["secret_key"]
        else:
            print(f"\n--- Generating New Credentials ---")
            if seed:
                access_key = generate_deterministic_key(project_id, seed, 'access')
                secret_key = generate_deterministic_key(project_id, seed, 'secret')
            else:
                access_key = generate_key()
                secret_key = generate_key()
            creds[access_key] = {
                "secret_key": secret_key,
                "project_id": project_id
            }

        print(f"Project ID: {project_id}")
        print(f"Access Key (X-Key): {access_key}")
        print(f"Secret Key (for signatures): {secret_key}")
        
        results[access_key] = {
            "secret_key": secret_key,
            "project_id": project_id
        }

    save_credentials(creds)
    
    print(f"\nCredentials have been saved to {CREDENTIALS_FILE}")

if __name__ == "__main__":
    main()
