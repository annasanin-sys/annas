import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT = os.getenv("JIRA_PROJECT_KEY")

def inspect_response():
    url = f"{JIRA_HOST}/rest/api/3/search/jql"
    # Basic fetch without pagination params first
    payload = {
        "jql": f"project = {JIRA_PROJECT}",
        "fields": ["summary"],
        "maxResults": 10
    }
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        resp = requests.post(url, json=payload, headers=headers, auth=(JIRA_EMAIL, JIRA_TOKEN))
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            # Print top-level keys to see pagination method
            print("Response Keys:", data.keys())
            if 'total' in data: print(f"Total: {data['total']}")
            if 'startAt' in data: print(f"startAt: {data['startAt']}")
            if 'nextPageToken' in data: print(f"nextPageToken: {data['nextPageToken']}")
            if 'isLast' in data: print(f"isLast: {data['isLast']}")
        else:
            print(resp.text)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_response()
