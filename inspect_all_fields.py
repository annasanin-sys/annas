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

def fetch_all_fields():
    # Use *all to get everything
    url = f"{JIRA_HOST}/rest/api/3/issue/{TARGET_ISSUE}?fields=*all&expand=names"
    print(f"Fetching {TARGET_ISSUE} with fields=*all ...")
    try:
        resp = requests.get(url, headers=get_jira_headers(), auth=get_jira_auth())
        resp.raise_for_status()
        data = resp.json()
        
        fields = data.get('fields', {})
        names = data.get('names', {})
        
        print(f"Total fields returned: {len(fields)}")
        
        found_content = False
        with open("full_dump_AC-3309.json", "w") as f:
            json.dump(data, f, indent=2)

        for key, val in fields.items():
            if val: # Not None, Not Empty List, Not Empty Dict
                # Filter out standard noise
                if key in ["issuetype", "project", "status", "priority", "creator", "reporter", "watches", "votes", "worklog", "comment"]:
                    continue
                
                name = names.get(key, key)
                val_str = str(val)
                if len(val_str) > 500: val_str = val_str[:500] + "..."
                
                try:
                    print(f"[{key}] {name}: {val_str}")
                except UnicodeEncodeError:
                    print(f"[{key}] {name}: {val_str.encode('utf-8')}")

                found_content = True
        
        if not found_content:
            print("No non-empty custom fields found.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_all_fields()
