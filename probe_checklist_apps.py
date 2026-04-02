import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
TARGET_ISSUE_ID = "14293" # AC-3309 ID from dump

def get_jira_auth():
    return (JIRA_EMAIL, JIRA_TOKEN)

def get_jira_headers():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def probe_apps():
    # 1. Smart Checklist (Railsware)
    # https://docs.smartchecklist.com/smart-checklist-cloud/developer-guide/rest-api
    # Endpoint: /rest/railsware/1.0/checklist/{issue_id}
    
    url_smart = f"{JIRA_HOST}/rest/railsware/1.0/checklist/{TARGET_ISSUE_ID}"
    print(f"Probing Smart Checklist: {url_smart}")
    try:
        resp = requests.get(url_smart, headers=get_jira_headers(), auth=get_jira_auth())
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print("FOUND Smart Checklist Data!")
            print(resp.text[:500])
    except Exception as e:
        print(f"Error: {e}")

    # 2. Issue Checklist (HeroCoders)
    # They usually expose a custom field, but maybe hidden?
    # Or property 'com.herocoders.jira.issue-checklist' which I supposedly checked.
    
    # 3. Checklists for Jira (Okapya)
    # Endpoint: /rest/checklists/1.0/checklists/{issue_id}
    url_okapya = f"{JIRA_HOST}/rest/checklists/1.0/checklists/{TARGET_ISSUE_ID}"
    print(f"Probing Okapya Checklist: {url_okapya}")
    try:
        resp = requests.get(url_okapya, headers=get_jira_headers(), auth=get_jira_auth())
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
             print("FOUND Okapya Data!")
             print(resp.text[:500])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    probe_apps()
