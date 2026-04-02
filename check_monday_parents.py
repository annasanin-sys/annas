import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()
MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")

def check_parents():
    with open("sync_db.json", "r") as f:
        db = json.load(f)
    
    parents = ["AC-3308", "AC-3344"]
    monday_ids = []
    
    for p in parents:
        m_id = db['jira_to_monday'].get(p)
        print(f"{p} -> Monday ID: {m_id}")
        if m_id:
            monday_ids.append(int(m_id))
            
    if not monday_ids:
        print("No IDs found.")
        return

    # Query Monday
    url = "https://api.monday.com/v2"
    query = f'''
    query {{
        items (ids: {monday_ids}) {{
            id
            name
            state
            board {{
                id
                name
            }}
        }}
    }}
    '''
    
    try:
        resp = requests.post(url, json={"query": query}, headers={"Authorization": MONDAY_TOKEN, "API-Version": "2023-10"})
        data = resp.json()
        items = data.get('data', {}).get('items', [])
        
        print(f"\nFound {len(items)} items on Monday:")
        found_ids = set()
        for item in items:
            print(f"  - [{item['id']}] {item['name']} (State: {item['state']}) Board: {item['board']['name']}")
            found_ids.add(item['id'])
            
        # Check for missing
        for req_id in monday_ids:
            if str(req_id) not in found_ids:
                 print(f"  - [{req_id}] NOT FOUND in Monday response (Access/Deleted/Archived?)")
                 
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_parents()
