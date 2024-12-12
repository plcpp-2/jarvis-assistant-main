import os
import json
import subprocess
import sys

def load_secrets():
    """Load secrets from the generated JSON file."""
    secrets_path = os.path.join(os.path.dirname(__file__), 'secrets', 'github_secrets.json')
    with open(secrets_path, 'r') as f:
        return json.load(f)

def set_github_secrets(secrets, repo):
    """Set GitHub secrets using GitHub CLI."""
    for key, value in secrets.items():
        if isinstance(value, dict):
            # For complex secrets like Azure Credentials, convert to JSON string
            value = json.dumps(value)
        
        try:
            # Use GitHub CLI to set secret
            result = subprocess.run([
                'gh', 'secret', 'set', key, 
                '--body', str(value), 
                '--repo', repo
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Successfully set secret: {key}")
            else:
                print(f"❌ Failed to set secret {key}: {result.stderr}")
        
        except Exception as e:
            print(f"❌ Error setting {key}: {e}")

def main():
    # Check if repo is provided as command-line argument
    if len(sys.argv) < 2:
        print("❌ Please provide your GitHub repository name (e.g., your-username/jarvis-assistant)")
        sys.exit(1)
    
    repo = sys.argv[1]
    
    # Ensure GitHub CLI is installed and authenticated
    try:
        subprocess.run(['gh', 'auth', 'status'], check=True)
    except subprocess.CalledProcessError:
        print("❌ You must be logged in to GitHub CLI. Run 'gh auth login' first.")
        return
    
    secrets = load_secrets()
    set_github_secrets(secrets, repo)
    
    print("\n🔐 Secret Setup Complete!")
    print("IMPORTANT: Verify these secrets in your GitHub repository settings.")

if __name__ == "__main__":
    main()
