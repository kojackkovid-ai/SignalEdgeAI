#!/usr/bin/env python3
"""
Deploy to Fly.io using the GraphQL API (no CLI needed)
"""
import os
import sys
import json

def deploy_to_fly():
    """Deploy app to Fly.io using REST API"""
    
    try:
        import requests
    except ImportError:
        print("ERROR: requests library not available. Install with: pip install requests")
        print("\nAlternative: Use Fly.io web dashboard")
        print("1. Go to https://fly.io")
        print("2. Log in with your account")
        print("3. Select app 'signaledge-ai'")
        print("4. Go to Settings > Deployments")
        print("5. Click 'Deploy' to trigger build from GitHub")
        return False
    
    # Get Fly.io API token from environment
    fly_token = os.getenv("FLY_API_TOKEN")
    if not fly_token:
        print("ERROR: FLY_API_TOKEN environment variable not set")
        print("\nTo get your token:")
        print("1. Go to https://fly.io/app/account/tokens")
        print("2. Create a new token")
        print("3. Run: $env:FLY_API_TOKEN='your_token_here'")
        print("\nThen: python deploy_fly.py")
        return False
    
    headers = {
        "Authorization": f"Bearer {fly_token}",
        "Content-Type": "application/json",
    }
    
    # GraphQL mutation to deploy
    deploy_mutation = """
    mutation {
      appDeploy(input: {appId: "signaledge-ai"}) {
        release {
          id
          version
          status
        }
      }
    }
    """
    
    payload = {"query": deploy_mutation}
    
    print("🚀 Deploying to Fly.io...")
    print(f"App: signaledge-ai")
    print(f"Endpoint: https://api.fly.io/graphql")
    
    try:
        response = requests.post(
            "https://api.fly.io/graphql",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Deployment initiated successfully!")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    success = deploy_to_fly()
    sys.exit(0 if success else 1)
