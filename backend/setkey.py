## A small utility to automatically push the right environement variables from local .env to github secret to set up the CI CD workflow 

import os
import requests
from dotenv import load_dotenv
# pip install pynacl
from nacl import encoding, public
import base64
import sys

def get_github_public_key(owner: str, repo: str, token: str):
    """Fetches the public key for encrypting GitHub secrets."""
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        data = response.json()
        return data["key_id"], data["key"]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching GitHub public key: {e}")
        print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
        print(f"Response body: {response.text if 'response' in locals() else 'N/A'}")
        sys.exit(1)

def encrypt_secret(public_key: str, secret_value: str) -> str:
    """Encrypts a secret value using the provided public key."""
    # Decode the public key from base64
    decoded_public_key = base64.b64decode(public_key)
    # Create a SealedBox with the decoded public key
    sealed_box = public.SealedBox(public.PublicKey(decoded_public_key))
    # Encrypt the secret value
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    # Encode the encrypted message to base64 for GitHub API
    return base64.b64encode(encrypted).decode("utf-8")

def create_or_update_github_secret(owner: str, repo: str, secret_name: str, encrypted_value: str, key_id: str, token: str):
    """Creates or updates a GitHub repository secret."""
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    data = {
        "encrypted_value": encrypted_value,
        "key_id": key_id
    }
    try:
        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()
        if response.status_code == 201:
            print(f"Secret '{secret_name}' created successfully.")
        elif response.status_code == 204:
            print(f"Secret '{secret_name}' updated successfully.")
        else:
            print(f"Unexpected status code {response.status_code} for secret '{secret_name}'.")
            print(f"Response body: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error creating/updating secret '{secret_name}': {e}")
        print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
        print(f"Response body: {response.text if 'response' in locals() else 'N/A'}")

def main():
    # --- Configuration ---
    # Replace with your GitHub repository details
    github_owner = "edouard-legoupil"  # Your GitHub username or organization name
    github_repo = "proposal_drafter" # Your repository name

    # Path to your .env file
    env_file_path = ".env"

    # GitHub Personal Access Token (PAT)
    # It's highly recommended to set this as an environment variable
    # rather than hardcoding it directly in the script.
    # For example: export GITHUB_TOKEN="ghp_YOUR_TOKEN_HERE"
    github_token = os.getenv("GITHUB_TOKEN")

    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set.")
        print("Please set it (e.g., export GITHUB_TOKEN='ghp_YOUR_TOKEN_HERE') before running the script.")
        sys.exit(1)

    # Load environment variables from .env file
    if not os.path.exists(env_file_path):
        print(f"Error: .env file not found at '{env_file_path}'. Please create it.")
        sys.exit(1)

    # Load .env variables into os.environ
    # We'll then iterate through the file directly to avoid loading system env vars
    # that might not be intended for GitHub secrets.
    env_vars_to_upload = {}
    with open(env_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'): # Ignore empty lines and comments
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars_to_upload[key] = value

    if not env_vars_to_upload:
        print(f"No environment variables found in '{env_file_path}' to upload.")
        sys.exit(0)

    print(f"Attempting to upload {len(env_vars_to_upload)} secrets to {github_owner}/{github_repo}...")

    # Get the public key for the repository
    key_id, public_key = get_github_public_key(github_owner, github_repo, github_token)
    print(f"Fetched GitHub public key with ID: {key_id}")

    # Upload each environment variable as a secret
    for key, value in env_vars_to_upload.items():
        print(f"Processing secret: {key}...")
        encrypted_value = encrypt_secret(public_key, value)
        create_or_update_github_secret(github_owner, github_repo, key, encrypted_value, key_id, github_token)

    print("\nScript finished.")

if __name__ == "__main__":
    main()
