import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT = os.getenv("JIRA_PROJECT_KEY")

MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")
MONDAY_BOARD_ID = os.getenv("MONDAY_BOARD_ID")

def get_jira_headers():
    return {"Accept": "application/json", "Content-Type": "application/json"}

def get_monday_headers():
    return {"Authorization": MONDAY_TOKEN, "API-Version": "2023-10", "Content-Type": "application/json"}

def search_jira_text(query_text):
    print(f"--- Searching Jira for '{query_text}' ---")
    url = f"{JIRA_HOST}/rest/api/3/search/jql"
    payload = {
        "jql": f"text ~ '{query_text}'",
        "fields": ["summary", "status", "issuetype", "parent"],
        "maxResults": 20
    }
    try:
        resp = requests.post(url, json=payload, headers=get_jira_headers(), auth=(JIRA_EMAIL, JIRA_TOKEN))
        if resp.status_code == 200:
            issues = resp.json().get("issues", [])
            print(f"Found {len(issues)} issues in Jira:")
            for i in issues:
                print(f"  - {i['key']}: {i['fields']['summary']} ({i['fields']['issuetype']['name']})")
        else:
            print(f"Jira Search Error: {resp.status_code}")
    except Exception as e:
        print(f"Jira Exception: {e}")

def search_monday_name(query_text):
    print(f"\n--- Searching Monday for items containing '{query_text}' ---")
    url = "https://api.monday.com/v2"
    query = f'''
    query {{
        boards (ids: {MONDAY_BOARD_ID}) {{
            items_page (limit: 50, query_params: {{rules: [{{column_id: "name", compare_value: ["{query_text}"], operator: contains_text}}]}}) {{
                items {{
                    id
                    name
                }}
            }}
        }}
    }}
    '''
    try:
        resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
        data = resp.json()
        items = data.get('data', {}).get('boards', [{}])[0].get('items_page', {}).get('items', [])
        print(f"Found {len(items)} items in Monday:")
        for i in items:
            print(f"  - [{i['id']}] {i['name']}")
    except Exception as e:
        print(f"Monday Exception: {e}")

if __name__ == "__main__":
    search_jira_text("AC-3644")
    search_monday_name("AC-3644")
