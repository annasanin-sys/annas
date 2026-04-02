import os
import requests
from dotenv import load_dotenv
import base64

load_dotenv()

JIRA_HOST = os.getenv("JIRA_HOST")
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT = os.getenv("JIRA_PROJECT_KEY")
MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")
MONDAY_BOARD_ID = os.getenv("MONDAY_BOARD_ID")

def test_jira():
    print(f"Testing Jira connection to {JIRA_HOST}...")
    url = f"{JIRA_HOST}/rest/api/3/project/{JIRA_PROJECT}"
    auth_str = f"{JIRA_EMAIL}:{JIRA_TOKEN}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print("[OK] Jira Connection Successful!")
            print(f"Project Name: {response.json().get('name')}")
            return True
        else:
            print(f"[ERROR] Jira Project '{JIRA_PROJECT}' not found (Status: {response.status_code})")
            print("Attempting to list accessible projects...")
            
            # Try to list all projects
            projects_url = f"{JIRA_HOST}/rest/api/3/project"
            p_response = requests.get(projects_url, headers=headers)
            if p_response.status_code == 200:
                projects = p_response.json()
                print("\nAvailable Projects:")
                for p in projects:
                    print(f"- {p['key']}: {p['name']}")
            else:
                print(f"Could not list projects: {p_response.status_code}")
                
            return False
    except Exception as e:
        print(f"[ERROR] Jira Error: {e}")
        return False

def test_monday():
    print(f"\nTesting Monday.com connection...")
    url = "https://api.monday.com/v2"
    headers = {
        "Authorization": MONDAY_TOKEN,
        "API-Version": "2023-10"
    }
    query = f'''
    query {{
        boards (ids: {MONDAY_BOARD_ID}) {{
            name
            columns {{
                id
                title
            }}
        }}
    }}
    '''
    
    try:
        response = requests.post(url, json={"query": query}, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                 print(f"[ERROR] Monday.com API Error: {data['errors']}")
                 return False
            
            boards = data.get("data", {}).get("boards", [])
            if boards:
                print("[OK] Monday.com Connection Successful!")
                print(f"Board Name: {boards[0]['name']}")
                # print(f"Columns: {[c['title'] for c in boards[0]['columns']]}")
                return True
            else:
                print("[ERROR] Monday.com Board not found (check ID/permissions)")
                return False
        else:
            print(f"[ERROR] Monday.com HTTP Fail: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Monday Error: {e}")
        return False

if __name__ == "__main__":
    j_ok = test_jira()
    m_ok = test_monday()
    
    if j_ok and m_ok:
        print("\n[SUCCESS] All systems go! Ready to sync.")
    else:
        print("\n[WARNING] Connectivity issues detected.")
