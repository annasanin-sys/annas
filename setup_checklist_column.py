import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")
MONDAY_SUBITEM_BOARD_ID = "18393136039" 

def get_monday_headers():
    return {
        "Authorization": MONDAY_TOKEN,
        "API-Version": "2023-10",
        "Content-Type": "application/json"
    }

def setup_column():
    url = "https://api.monday.com/v2"
    
    # 1. Check if it exists
    query = f'''
    query {{
        boards (ids: {MONDAY_SUBITEM_BOARD_ID}) {{
            columns {{
                id
                title
                type
            }}
        }}
    }}
    '''
    try:
        resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
        data = resp.json()
        cols = data.get('data', {}).get('boards', [])[0].get('columns', [])
        
        existing_id = None
        for c in cols:
            if c['title'] == "Jira Checklist":
                existing_id = c['id']
                print(f"Found existing column: {c['title']} ({c['id']})")
                break
        
        if existing_id:
            return existing_id
            
        # 2. Create if not exists
        print("Creating 'Jira Checklist' column (long_text)...")
        query_create = f'''
        mutation {{
            create_column (board_id: {MONDAY_SUBITEM_BOARD_ID}, title: "Jira Checklist", column_type: long_text) {{
                id
                title
            }}
        }}
        '''
        resp = requests.post(url, json={"query": query_create}, headers=get_monday_headers())
        new_col = resp.json().get('data', {}).get('create_column', {})
        print(f"Created: {new_col}")
        return new_col.get('id')

    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    setup_column()
