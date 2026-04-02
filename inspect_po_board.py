import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Hardcoded for the requested board
MONDAY_BOARD_ID = "18378310412"
MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")

def get_monday_headers():
    return {
        "Authorization": MONDAY_TOKEN,
        "API-Version": "2023-10",
        "Content-Type": "application/json"
    }

def inspect_board():
    if not MONDAY_TOKEN:
        print("Error: MONDAY_API_TOKEN not found in .env")
        return

    url = "https://api.monday.com/v2"
    query = f'''
    query {{
        boards (ids: {MONDAY_BOARD_ID}) {{
            name
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
        
        boards = data.get("data", {}).get("boards", [])
        if not boards:
            print(f"Board {MONDAY_BOARD_ID} not found.")
            return

        board = boards[0]
        print(f"Board: {board['name']}")
        print("-" * 30)
        
        for col in board['columns']:
            print(f"Column: {col['title']} (ID: {col['id']}, Type: {col['type']})")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_board()
