import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
TARGET_ISSUE = "AC-3309"

def get_jira_auth():
    return (JIRA_EMAIL, JIRA_TOKEN)

def get_jira_headers():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def inspect_issue():
    url = f"{JIRA_HOST}/rest/api/3/issue/{TARGET_ISSUE}"
    print(f"Fetching {TARGET_ISSUE}...")
    try:
        resp = requests.get(url, headers=get_jira_headers(), auth=get_jira_auth())
        resp.raise_for_status()
        data = resp.json()
        
        print(f"Successfully fetched {TARGET_ISSUE}.")
        
        # Dump the 'fields' part to a file for easier reading, 
        # but also print keys that look like 'customfield' or contain 'check'
        fields = data.get('fields', {})
        
        with open(f"dump_{TARGET_ISSUE}.json", "w") as f:
            json.dump(data, f, indent=2)
            
        print("Scannning fields for 'check' or non-null custom fields...")
        for key, val in fields.items():
            if val is None: continue
            
            # Check if key is a custom field
            if key.startswith("customfield_"):
                # We don't know the name yet, so just print the value structure briefly
                val_str = str(val)
                if len(val_str) > 200: val_str = val_str[:200] + "..."
                print(f"  {key}: {val_str}")
            
            # Or if the name (if we could resolve it) might contain checklist
            # (We rely on previous script for name mapping, but here let's look at data content)
            if isinstance(val, str) and "check" in val.lower():
                 print(f"  [Potential Match in String] {key}: {val}")
            elif isinstance(val, dict) and "check" in str(val).lower():
                 print(f"  [Potential Match in Dict] {key}: {str(val)[:100]}...")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_issue()
