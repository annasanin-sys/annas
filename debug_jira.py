import os
import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")

auth = (JIRA_EMAIL, JIRA_TOKEN)
headers = {"Accept": "application/json", "Content-Type": "application/json"}

def test_endpoint(name, method, endpoint, json_data=None):
    url = f"{JIRA_HOST}{endpoint}"
    print(f"Testing {name}: {method} {url}")
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, auth=auth)
        else:
            resp = requests.post(url, headers=headers, auth=auth, json=json_data)
        
        print(f"Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Response: {resp.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print(f"Host: {JIRA_HOST}")
    print(f"User: {JIRA_EMAIL}")
    
    test_endpoint("V3 MySelf", "GET", "/rest/api/3/myself")
    test_endpoint("V2 MySelf", "GET", "/rest/api/2/myself")
    test_endpoint("Server Info", "GET", "/rest/api/3/serverInfo")
    
    payload = {"jql": "project = AC", "maxResults": 1}
    # Test GET which is often safer
    test_endpoint("V3 Search GET", "GET", "/rest/api/3/search?jql=project=AC&maxResults=1")
    
    # Test new POST endpoint suggested by error
    test_endpoint("V3 Search JQL POST", "POST", "/rest/api/3/search/jql", payload)
