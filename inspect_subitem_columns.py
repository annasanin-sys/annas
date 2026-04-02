import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")
# Using the subitem board ID from sync_script.py (hardcoded there, so using same here)
MONDAY_SUBITEM_BOARD_ID = "18393136039"

def get_monday_headers():
    return {
        "Authorization": MONDAY_TOKEN,
        "API-Version": "2023-10",
        "Content-Type": "application/json"
    }

def inspect_subitem_board_columns():
    url = "https://api.monday.com/v2"
    query = f'''
    query {{
        boards (ids: {MONDAY_SUBITEM_BOARD_ID}) {{
            columns {{
                id
                title
                settings_str
            }}
        }}
    }}
    '''
    try:
        resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
        print(json.dumps(resp.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

inspect_subitem_board_columns()
