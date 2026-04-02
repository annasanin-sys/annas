
import os
import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT = os.getenv("JIRA_PROJECT_KEY")

def get_jira_auth():
    return (JIRA_EMAIL, JIRA_TOKEN)

def get_jira_headers():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def fetch_unique_statuses():
    jql = f"project = {JIRA_PROJECT}"
    statuses = set()
    
    url = f"{JIRA_HOST}/rest/api/3/search/jql"
    
    # Just need one batch usually to get most, but let's paging to be safe
    # Actually, we can use 'expand=names' or just iterating
    
    payload = {
        "jql": jql,
        "fields": ["status"],
        "maxResults": 1000
    }
    
    print("Fetching Jira statuses...")
    try:
        resp = requests.post(url, json=payload, headers=get_jira_headers(), auth=get_jira_auth())
        resp.raise_for_status()
        data = resp.json()
        
        for issue in data.get('issues', []):
            name = issue['fields']['status']['name']
            statuses.add(name)
            
        print("\nUnique Statuses Found in Jira:")
        for s in statuses:
            print(f" - '{s}'")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_unique_statuses()
