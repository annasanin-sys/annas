import os
import json
import datetime
import requests
from dotenv import load_dotenv

# Load credentials
load_dotenv()

# Configuration
JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT = os.getenv("JIRA_PROJECT_KEY")

MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")
MONDAY_BOARD_ID = os.getenv("MONDAY_BOARD_ID")
# Subitems live on a separate board. ID found via inspection.
# Ideally this is fetched dynamically, but for this fix we hardcode it.
MONDAY_SUBITEM_BOARD_ID = "18393136039" 
MONDAY_CHECKLIST_COLUMN_ID = "long_text_mkyyh8gb"

SYNC_DB_FILE = "sync_db.json"

# Status Mapping
# Jira Status Name -> Monday Label Index
# Main Board: 0: Working on it, 1: Done, 5: To Do
JIRA_TO_MONDAY_STATUS = {
    "To Do": "5",
    "In Progress": "0",
    "Done": "1"
}

# Subitem Board: 0: Working on it, 1: Done, 5: To Do
# User added "To Do" label (Index 5).
JIRA_TO_MONDAY_SUBITEM_STATUS = {
    "To Do": "5", 
    "In Progress": "0",
    "Done": "1"
}

# Monday Label Index -> Jira Transition ID
MONDAY_TO_JIRA_TRANSITION = {
    "5": "11",
    "0": "21",
    "1": "31"
}

# --- Helpers ---

def load_db():
    if os.path.exists(SYNC_DB_FILE):
        try:
            with open(SYNC_DB_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"jira_to_monday": {}, "monday_to_jira": {}, "last_sync": None}

def save_db(db):
    # READ-MERGE-WRITE to prevent overwriting manual fixes (Race Condition Protection)
    current_disk_db = load_db()
    
    # Merge keys: Diskwins? Or MemoryWins? 
    # Usually Memory has latest sync results, but Disk has manual repairs.
    # Manual repairs (healing) usually add missing keys.
    # Sync usually adds missing keys too.
    # Conflicts are rare if we just assume "If in doubt, keep existing".
    # But wait, we want to persist our sync results (memory).
    
    # Let's simple union:
    # 1. Start with Disk DB (preserve manual edits)
    # 2. Update with Memory DB (persist sync results)
    
    merged_db = current_disk_db.copy()
    merged_db['jira_to_monday'].update(db['jira_to_monday'])
    merged_db['monday_to_jira'].update(db['monday_to_jira'])
    merged_db['last_sync'] = db.get('last_sync', datetime.datetime.now().isoformat())
    
    # Retry loop for file locking (Windows frequent issue)
    import time
    for attempt in range(5):
        try:
            with open(SYNC_DB_FILE, 'w') as f:
                json.dump(merged_db, f, indent=4)
            return
        except PermissionError:
            print(f"[WARN] DB Locked (Permission Denied). Retrying in 1s ({attempt+1}/5)...")
            time.sleep(1)
        except Exception as e:
            print(f"[ERROR] Failed to save DB: {e}")
            break

def get_jira_auth():
    return (JIRA_EMAIL, JIRA_TOKEN)

def get_jira_headers():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def get_monday_headers():
    return {
        "Authorization": MONDAY_TOKEN,
        "API-Version": "2023-10",
        "Content-Type": "application/json"
    }


def extract_text_from_adf(adf_body):
    """Simple extractor for Jira ADF (Atlassian Document Format)."""
    if not adf_body: return ""
    try:
        if isinstance(adf_body, str): return adf_body # v2 API returns string
        if 'content' not in adf_body: return ""
        
        text_lines = []
        for node in adf_body['content']:
            if node['type'] == 'paragraph' or node['type'] == 'listItem': # Simplified traversal
                 # This is a very basic recursive crawler would be better, but for bullet lists:
                 # node['content'] -> list of text nodes
                 pass
            # Quick hack: generic traverse
            text_lines.append(extract_node_text(node))
        return "\\n".join(filter(None, text_lines))
    except:
        return ""

def extract_node_text(node):
    text = ""
    if 'text' in node: text += node['text']
    if 'content' in node:
        for child in node['content']:
            text += extract_node_text(child)
    return text

def normalize_monday_update(update_body):
    """Normalizes Monday update body for comparison with Jira text."""
    if not update_body: return ""
    # Remove the header marker
    marker = "**Synced Description:**"
    if marker in update_body:
        update_body = update_body.replace(marker, "", 1)
    
    # Replace breaks with newlines
    # Monday can return <br>, <br/>, <br />
    text = update_body.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    
    # Simple unescape if needed (basic chars)
    # text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    
    return text.strip()

def fetch_jira_checklist_content(issue_key):
    """Fetches the 'checklist' property from the Jira issue."""
    url = f"{JIRA_HOST}/rest/api/3/issue/{issue_key}/properties/checklist"
    try:
        resp = requests.get(url, headers=get_jira_headers(), auth=get_jira_auth())
        if resp.status_code == 200:
            data = resp.json()
            # Try to return the 'items' string from the value object
            # Value usually looks like: { "items": "Item 1... Item 2..." }
            return data.get('value', {}).get('items', "")
        return None
    except Exception as e:
        print(f"[ERROR] Fetching checklist for {issue_key}: {e}")
        return None
    
def fetch_jira_issues(last_sync_time=None):
    """Fetch all Jira issues and split into parents and subtasks (using nextPageToken)."""
    jql = f"project = {JIRA_PROJECT}"
    parents = []
    subtasks = []
    
    next_token = None
    has_more = True
    max_results = 100 
    
    url = f"{JIRA_HOST}/rest/api/3/search/jql"
    
    while has_more:
        print(f"Fetching Jira issues (Batch)...")
        payload = {
            "jql": jql,
            "fields": ["summary", "status", "description", "updated", "issuetype", "parent", "attachment"],
            "maxResults": max_results
        }
        if next_token:
            payload["nextPageToken"] = next_token
        
        try:
            resp = requests.post(url, json=payload, headers=get_jira_headers(), auth=get_jira_auth())
            resp.raise_for_status()
            data = resp.json()
            
            issues_batch = data.get("issues", [])
            for i in issues_batch:
                if i['fields']['issuetype']['subtask']:
                    subtasks.append(i)
                else:
                    parents.append(i)
            
            next_token = data.get("nextPageToken")
            # 'isLast' usually indicates end, or if no next token
            if not next_token or (data.get("isLast") is True):
                has_more = False
                
        except Exception as e:
            print(f"[ERROR] Fetching Jira issues: {e}")
            break
            
    return parents, subtasks

def create_jira_issue(title, description="", status_index=None):
    print("[SAFETY] Jira creation disabled.")
    return None

def transition_jira_issue(issue_key, transition_id):
    print(f"[SAFETY] Jira transition for {issue_key} disabled.")
    return False

def create_monday_update(item_id, text_body):
    url = "https://api.monday.com/v2"
    # Simple text body. If complex, could use HTML Monday API takes basic text/html in 'body'.
    query = f'''
    mutation {{
        create_update (item_id: {item_id}, body: "{text_body}") {{
            id
        }}
    }}
    '''
    try:
        resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
        data = resp.json()
        return data.get('data', {}).get('create_update', {}).get('id')
    except:
        return None

def download_jira_attachment(url):
    try:
        resp = requests.get(url, headers=get_jira_headers(), auth=get_jira_auth(), stream=True)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        print(f"[ERROR] Downloading attachment {url}: {e}")
        return None


def upload_file_to_monday(item_id, filename, file_content, mimetype):
    url = "https://api.monday.com/v2/file"
    
    # 1. Create an Update to attach to
    update_id = create_monday_update(item_id, f"**Attachment:** {filename}")
    if not update_id: return
    
    # 2. Upload file to that update
    # Monday GraphQL multipart upload
    query = f'''
    mutation ($file: File!) {{
        add_file_to_update (update_id: {update_id}, file: $file) {{
            id
        }}
    }}
    '''
    
    # Prepare multipart
    files = {
        'query': (None, query),
        'map': (None, json.dumps({"image": ["variables.file"]})),
        'image': (filename, file_content, mimetype)
    }
    
    try:
        # Note: Do NOT use standard json header for multipart
        headers = {"Authorization": MONDAY_TOKEN} 
        resp = requests.post(url, files=files, headers=headers)
        resp.raise_for_status()
        # print("Upload Response:", resp.json())
    except Exception as e:
        print(f"[ERROR] Uploading file to Tuesday: {e}")

def get_item_updates(item_id):
    url = "https://api.monday.com/v2"
    query = f'''
    query {{
        items (ids: [{item_id}]) {{
            updates {{
                body
            }}
        }}
    }}
    '''
    try:
        resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
        data = resp.json()
        updates = data.get('data', {}).get('items', [{}])[0].get('updates', [])
        return [u['body'] for u in updates]
    except:
        return []

def sync_attachments(jira_issue, monday_item_id):
    attachments = jira_issue['fields'].get('attachment', [])
    if not attachments: return

    # Check existing updates to prevent duplicates
    existing_updates = get_item_updates(monday_item_id)
    # Naive check: if update body contains "Attachment: {filename}"
    
    for att in attachments:
        filename = att['filename']
        content_url = att['content']
        mimetype = att['mimeType']
        
        # Check duplicate
        is_dupe = False
        marker = f"**Attachment:** {filename}"
        for body in existing_updates:
            if marker in body:
                is_dupe = True
                break
        
        if is_dupe:
            # print(f"[SKIP] Attachment {filename} already synced.")
            continue
            
        print(f"  -> Syncing Attachment: {filename}...")
        content = download_jira_attachment(content_url)
        if content:
            upload_file_to_monday(monday_item_id, filename, content, mimetype)


def update_jira_issue(issue_key, title, status_index=None):
    print(f"[SAFETY] Jira update for {issue_key} disabled.")
    return True

# --- Monday API ---

# --- Monday API Helpers ---

def execute_monday_query(query, retries=3):
    url = "https://api.monday.com/v2"
    for attempt in range(retries):
        try:
            resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
            if resp.status_code >= 500:
                print(f"  [WARN] Monday API 500 Error. Retrying ({attempt+1}/{retries})...")
                import time
                time.sleep(2 * (attempt + 1))
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            if attempt < retries - 1:
                print(f"  [WARN] Request failed: {e}. Retrying ({attempt+1}/{retries})...")
                import time
                time.sleep(2 * (attempt + 1))
            else:
                raise e

def fetch_monday_items():
    all_items = []
    cursor = None
    
    print("Fetching Monday items...")
    
    while True:
        # If we have a cursor, use it. Otherwise start fresh.
        if cursor:
            query = f'''
            query {{
                boards (ids: {MONDAY_BOARD_ID}) {{
                    items_page (cursor: "{cursor}", limit: 100) {{
                        cursor
                        items {{
                            id
                            name
                            updated_at
                            column_values {{
                                id
                                text
                                ... on StatusValue {{
                                    index
                                    label
                                }}
                            }}
                        }}
                    }}
                }}
            }}
            '''
        else:
            query = f'''
            query {{
                boards (ids: {MONDAY_BOARD_ID}) {{
                    items_page (limit: 100) {{
                        cursor
                        items {{
                            id
                            name
                            updated_at
                            column_values {{
                                id
                                text
                                ... on StatusValue {{
                                    index
                                    label
                                }}
                            }}
                        }}
                    }}
                }}
            }}
            '''
            
        try:
            data = execute_monday_query(query)
            
            # Navigate response structure safely
            boards = data.get('data', {}).get('boards', [])
            if not boards: 
                break
                
            items_page = boards[0].get('items_page', {})
            items = items_page.get('items', [])
            cursor = items_page.get('cursor')
            
            all_items.extend(items)
            print(f"  -> Fetched batch of {len(items)} items. Total so far: {len(all_items)}")
            
            if not cursor:
                break
                
        except Exception as e:
            print(f"[ERROR] Fetching Monday items: {e}")
            break
            
    return all_items

def fetch_monday_subitems():
    subitems = {} # {subitem_id: {parent_id, name, status_index}}
    cursor = None
    
    print("Fetching Monday subitems (Full Detail)...")
    
    while True:
        if cursor:
            query = f'''
            query {{
                boards (ids: {MONDAY_SUBITEM_BOARD_ID}) {{
                    items_page (cursor: "{cursor}", limit: 100) {{
                        cursor
                        items {{
                            id
                            name
                            parent_item {{
                                id
                            }}
                            column_values {{
                                id
                                ... on StatusValue {{
                                    index
                                }}
                            }}
                        }}
                    }}
                }}
            }}
            '''
        else:
            query = f'''
            query {{
                boards (ids: {MONDAY_SUBITEM_BOARD_ID}) {{
                    items_page (limit: 100) {{
                        cursor
                        items {{
                            id
                            name
                            parent_item {{
                                id
                            }}
                            column_values {{
                                id
                                ... on StatusValue {{
                                    index
                                }}
                            }}
                        }}
                    }}
                }}
            }}
            '''
            
        try:
            data = execute_monday_query(query)
            
            boards = data.get('data', {}).get('boards', [])
            if not boards: 
                break
                
            items_page = boards[0].get('items_page', {})
            items = items_page.get('items', [])
            cursor = items_page.get('cursor')
            
            for item in items:
                p_id = item.get('parent_item', {}).get('id') if item.get('parent_item') else None
                
                # Extract Status Index
                status_idx = None
                for col in item.get('column_values', []):
                    if col['id'] == 'status':
                        status_idx = col.get('index')
                        break # Optimization
                
                # Store full object (or flattened)
                subitems[item['id']] = {
                    "parent_id": p_id,
                    "name": item['name'],
                    "status_index": status_idx
                }
            
            print(f"  -> Fetched batch of {len(items)} subitems. Total so far: {len(subitems)}")
            
            if not cursor:
                break
                
        except Exception as e:
            print(f"[ERROR] Fetching Monday subitems: {e}")
            break
            
    return subitems

def create_monday_item(title, status_label_index="5"):
    url = "https://api.monday.com/v2"
    col_vals = json.dumps({
        "status": {"index": int(status_label_index)}
    }).replace('"', '\\"')
    
    query = f'''
    mutation {{
        create_item (board_id: {MONDAY_BOARD_ID}, item_name: "{title}", column_values: "{col_vals}") {{
            id
        }}
    }}
    '''
    try:
        resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("create_item", {})
    except Exception as e:
        print(f"[ERROR] Creating Monday item: {e}")
        return None

def create_monday_subitem(parent_id, title, status_label_index=None):
    url = "https://api.monday.com/v2"
    
    col_vals_dict = {}
    if status_label_index is not None:
        col_vals_dict["status"] = {"index": int(status_label_index)}
        
    col_vals = json.dumps(col_vals_dict).replace('"', '\\"')

    query = f'''
    mutation {{
        create_subitem (parent_item_id: {parent_id}, item_name: "{title}", column_values: "{col_vals}") {{
            id
        }}
    }}
    '''
    try:
        resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("create_subitem", {})
    except Exception as e:
        print(f"[ERROR] Creating Monday subitem: {e}")
        return None

def delete_monday_item(item_id):
    url = "https://api.monday.com/v2"
    query = f'''
    mutation {{
        delete_item (item_id: {item_id}) {{
            id
        }}
    }}
    '''
    try:
        requests.post(url, json={"query": query}, headers=get_monday_headers())
        return True
    except:
        return False


def update_monday_item(item_id, title, status_label_index=None, board_id=MONDAY_BOARD_ID):
    url = "https://api.monday.com/v2"
    
    col_vals_dict = {}
    if status_label_index is not None:
        col_vals_dict["status"] = {"index": int(status_label_index)}
    
    # Also update the Name
    if title:
        col_vals_dict["name"] = title
    
    col_vals = json.dumps(col_vals_dict).replace('"', '\\"')
    
    query = f'''
    mutation {{
        change_multiple_column_values (item_id: {item_id}, board_id: {board_id}, column_values: "{col_vals}") {{
            id
        }}
    }}
    '''
    try:
        resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
        data = resp.json()
        if "errors" in data:
            for err in data["errors"]:
                if "inactive items" in err.get("message", "").lower():
                    print(f"[ERROR] Item {item_id} is inactive/archived.")
                    return "INACTIVE"
        return True
    except: 
        return False

def verify_monday_item_exists(item_id):
    query = f'''
    query {{
        items (ids: [{item_id}]) {{
            id
            state
        }}
    }}
    '''
    try:
        # Use simple retry logic via execute_monday_query if possible, 
        # but that function returns the full JSON. 
        # Let's just use it to get free retries.
        data = execute_monday_query(query)
        items = data.get('data', {}).get('items', [])
        # strict check: must return item AND be active
        if items and items[0].get('state') == 'active':
            return True
    except Exception as e:
        print(f"[WARN] Verify existence failed: {e}")
        pass
    return False

# --- Sync Logic ---

def sync():
    db = load_db()
    print(f"--- Starting Sync at {datetime.datetime.now()} ---")

    # 1. Fetch
    jira_parents, jira_subtasks = fetch_jira_issues()

    monday_items = fetch_monday_items()
    monday_subitems_map = fetch_monday_subitems()
    
    # helper set for fast lookup
    monday_item_ids = set(item['id'] for item in monday_items)

    print(f"Jira: {len(jira_parents)} Parents, {len(jira_subtasks)} Subtasks. Monday: {len(monday_items)} Items.")

    # Sort Jira items by Priority (In Progress > To Do > Done) for processing order
    # Status Map: "In Progress": "0", "To Do": "5", "Done": "1"
    # We want processing order: In Progress, To Do, then others.
    def get_priority_score(issue):
        status = issue['fields']['status']['name']
        if status == "In Progress": return 0
        if status == "To Do": return 1
        return 2
    
    jira_parents.sort(key=get_priority_score)
    jira_subtasks.sort(key=get_priority_score)

    # 2. Sync Jira Parents -> Monday
    for issue in jira_parents:

        key = issue['key']
        summary = issue['fields']['summary']
        jira_status = issue['fields']['status']['name']
        monday_status_idx = JIRA_TO_MONDAY_STATUS.get(jira_status, "5")
        
        # Check if already mapped AND if the mapped item actually exists on Monday
        m_id = db['jira_to_monday'].get(key)
        
        # Validation: If mapped but missing in Monday items list
        if m_id and m_id not in monday_item_ids:
             print(f"[RE-SYNC] Parent {m_id} not found in Monday list (Deleted?). Clearing map to allow search/re-create...")
             del db['jira_to_monday'][key]
             if m_id in db['monday_to_jira']: del db['monday_to_jira'][m_id]
             save_db(db)
             m_id = None # Treat as unmapped

        # If Valid -> Update
        if m_id: 
             result = update_monday_item(m_id, f"[{key}] {summary}", monday_status_idx, MONDAY_BOARD_ID)
             if result == "INACTIVE":
                 print(f"[RE-SYNC] Parent {m_id} is inactive (API detected). Removing map...")
                 del db['jira_to_monday'][key]
                 if m_id in db['monday_to_jira']: del db['monday_to_jira'][m_id]
                 save_db(db)
        
        # If Not Mapped (or map cleared above) -> Search or Create
        if not m_id:
             # Not in DB. Check by NAME to avoid duplication
             expected_name = f"[{key}] {summary}"
             key_prefix = f"[{key}] "
             
             existing_match_id = None
             for m_item in monday_items:
                 if m_item['name'].strip() == expected_name.strip():
                     existing_match_id = m_item['id']
                     break
                 if m_item['name'].strip().startswith(key_prefix):
                     existing_match_id = m_item['id']
                     break

             if existing_match_id:
                 print(f"[SYNC] Found existing Monday Parent '{existing_match_id}' for {key}. Mapping...")
                 m_id = existing_match_id
                 db['jira_to_monday'][key] = m_id
                 db['monday_to_jira'][m_id] = key
                 save_db(db)
                 
                 update_monday_item(m_id, f"[{key}] {summary}", monday_status_idx, MONDAY_BOARD_ID)
                 
             else:
                 # Create NEW
                 print(f"[SYNC] Creating Monday Parent for {key}")
                 m_item = create_monday_item(f"[{key}] {summary}", monday_status_idx)
                 if m_item:
                     m_id = m_item['id']
                     db['jira_to_monday'][key] = m_id
                     db['monday_to_jira'][m_id] = key
                     monday_item_ids.add(m_id)
                     save_db(db)
                     
                     desc_adf = issue['fields'].get('description')
                     desc_text = extract_text_from_adf(desc_adf)
                     if desc_text and desc_text.strip():
                          print(f"  -> Posting Description Update for Parent {key}...")
                          create_monday_update(m_id, f"**Synced Description:**\\n{desc_text}")

                     sync_attachments(issue, m_id)

    # 3. Sync Jira Subtasks -> Monday Subitems
    for sub in jira_subtasks:
        key = sub['key']
        summary = sub['fields']['summary']
        jira_status = sub['fields']['status']['name']
        jira_parent_key = sub['fields'].get('parent', {}).get('key')
        
        # Use Subitem specific status map
        monday_status_idx = JIRA_TO_MONDAY_SUBITEM_STATUS.get(jira_status)
        
        # Fix Naming: Don't duplicate [KEY] prefix
        if summary.strip().startswith(f"[{key}]"):
            monday_title = summary
        else:
            monday_title = f"[{key}] {summary}"

        # DEBUG STATUS MAPPING
        print(f"[DEBUG] Processing {key}: Jira Status '{jira_status}' -> Monday Index '{monday_status_idx}' (Title: '{monday_title}')")
        if monday_status_idx is None:
             print(f"[WARN] No Monday status map for Jira status '{jira_status}' (Subtask {key})")

        # Determine expected parent ID
        expected_parent_id = None
        if jira_parent_key and jira_parent_key in db['jira_to_monday']:
             expected_parent_id = db['jira_to_monday'][jira_parent_key]

        if key in db['jira_to_monday']:
             m_id = db['jira_to_monday'][key]

             # Validate Existence and Parentage
             # If m_id is not in map, it's missing.
             # If m_id is in map but parent mismatches expected, it's orphaned.
             validation_error = None
             if m_id not in monday_subitems_map:
                 validation_error = "Missing on Monday"
             elif expected_parent_id and monday_subitems_map[m_id].get('parent_id') != expected_parent_id:
                 validation_error = f"Orphaned (Old Parent {monday_subitems_map[m_id].get('parent_id')} != New {expected_parent_id})"
             
             if validation_error:
                 print(f"[RE-SYNC] Subitem {key} {validation_error}. Removing map to re-create...")
                 
                 del db['jira_to_monday'][key]
                 if m_id in db['monday_to_jira']: del db['monday_to_jira'][m_id]
                 save_db(db)
                 # Fall through to Create logic
             else:
                 # Optimize: Only update if changed
                 current_data = monday_subitems_map[m_id]
                 current_status_idx = current_data.get('status_index')
                 current_name = current_data.get('name', "")
                 
                 # Name check: strict equality? or stripping? item names on monday might be edited.
                 # Let's trust our mapped name logic: monday_title
                 # Jira "In Progress" (0) vs Monday (0)
                 
                 # Normalizing for comparison
                 target_idx_int = int(monday_status_idx) if monday_status_idx is not None else -1
                 current_idx_int = int(current_status_idx) if current_status_idx is not None else -1
                 
                 # Name check:
                 # Only update name if it REALLY mismatches to avoid fighting user edits?
                 # User said: "if i edit an item in monday kanban, i don't want it to change jira item"
                 # But sync usually enforces Jira -> Monday. 
                 # Let's check if name is different.
                 name_mismatch = current_name.strip() != monday_title.strip()
                 status_mismatch = (target_idx_int != -1) and (target_idx_int != current_idx_int)
                 
                 if not name_mismatch and not status_mismatch:
                     # print(f"  [SKIP] Subitem {key} already synced. ({current_name} | Status: {current_status_idx})")
                     continue
                 
                 if status_mismatch:
                      print(f"  [UPDATE] Status Mismatch for {key}: Jira '{jira_status}' ({monday_status_idx}) != Monday ({current_status_idx})")
                 if name_mismatch:
                      print(f"  [UPDATE] Name Mismatch for {key}")

                 # Update existing
                 # Attempt update using SUBITEM BOARD ID
                 result = update_monday_item(m_id, monday_title, monday_status_idx, MONDAY_SUBITEM_BOARD_ID)
                 
                 print(f"  -> Update Result for {key}: {result}")
                 
                 # Note: "INACTIVE" check might still be useful, keeping it just in case
                 if result == "INACTIVE":
                      print(f"[RE-SYNC] Subitem {m_id} is inactive. Removing map to re-create {key}...")
                      del db['jira_to_monday'][key]
                      if m_id in db['monday_to_jira']: del db['monday_to_jira'][m_id]
                      save_db(db)
                      # Fall through
                 else:
                     # Sync Description (Update-on-Change)
                     desc_adf = sub['fields'].get('description')
                     desc_text = extract_text_from_adf(desc_adf)
                     
                     if desc_text and desc_text.strip():
                         existing_updates = get_item_updates(m_id)
                         
                         # Find latest synced description (updates are usually returned newest first)
                         latest_monday_desc = None
                         for u_body in existing_updates:
                             if "**Synced Description:**" in u_body:
                                 latest_monday_desc = normalize_monday_update(u_body)
                                 break
                         
                         # Compare
                         jira_desc_clean = desc_text.strip()
                         
                         # If mismatch or never synced -> Update
                         if latest_monday_desc != jira_desc_clean:
                              print(f"  [UPDATE] Description changed for {key}. Posting new update...")
                              # debug
                              # print(f"    Jira: {jira_desc_clean[:20]}...")
                              # print(f"    Mon : {latest_monday_desc[:20]}...")
                              create_monday_update(m_id, f"**Synced Description:**\\n{desc_text}")
                         else:
                              # print(f"  [SKIP] Description match for {key}.")
                              pass
    
                     # Sync Attachments
                     sync_attachments(sub, m_id)
                     
                     # Sync Checklist (Update Existing)
                     checklist_content = fetch_jira_checklist_content(key)
                     if checklist_content:
                         # For efficiency, we could check if it changed, but fetching column value is extra call.
                         # Just overwriting for now is safer/simpler for MVP.
                         # print(f"  -> Syncing Checklist to Column for {key}...")
                         col_vals = json.dumps({MONDAY_CHECKLIST_COLUMN_ID: checklist_content}).replace('"', '\\"')
                         
                         query_checklist = f'''
                         mutation {{
                             change_multiple_column_values (item_id: {m_id}, board_id: {MONDAY_SUBITEM_BOARD_ID}, column_values: "{col_vals}") {{
                                 id
                             }}
                         }}
                         '''
                         try:
                             requests.post("https://api.monday.com/v2", json={"query": query_checklist}, headers=get_monday_headers())
                         except:
                             pass
                     
                     continue

        # Create Logic (if new or fell through)
        if key not in db['jira_to_monday']:
            
            # --- FIX: LOOKUP EXISTING SUBITEM BEFORE CREATING ---
            # Search monday_subitems_map for a match by Name AND Parent
            found_subitem_id = None
            
            # Determine expected parent ID (repeated logic, but safe)
            expected_parent_id = None
            if jira_parent_key and jira_parent_key in db['jira_to_monday']:
                 expected_parent_id = db['jira_to_monday'][jira_parent_key]

            if expected_parent_id:
                for sub_id, sub_data in monday_subitems_map.items():
                    # Strict check: Parent must match
                    if sub_data.get('parent_id') != expected_parent_id:
                        continue
                        
                    # Name check: Matches "monday_title" OR starts with "[{key}]"
                    m_name = sub_data.get('name', "").strip()
                    if m_name == monday_title.strip() or m_name.startswith(f"[{key}]"):
                        found_subitem_id = sub_id
                        break
            
            if found_subitem_id:
                 print(f"[SYNC] Found existing Monday Subitem '{found_subitem_id}' for {key}. Mapping...")
                 db['jira_to_monday'][key] = found_subitem_id
                 db['monday_to_jira'][found_subitem_id] = key
                 save_db(db)
                 
                 # Continue to next loop to trigger 'update' logic if needed (or just skip for now)
                 # If we continue, we need to ensure the top of the loop handles it. 
                 # Actually, simpler to just Map it here and let next run update it, OR update it now.
                 # Let's simple-update it now to be robust.
                 update_monday_item(found_subitem_id, monday_title, monday_status_idx, MONDAY_SUBITEM_BOARD_ID)
                 continue 

            # Create

            if jira_parent_key and jira_parent_key in db['jira_to_monday']:
                monday_parent_id = db['jira_to_monday'][jira_parent_key]
                
                parent_exists = monday_parent_id in monday_item_ids
                if not parent_exists:
                     # Lazy Verification: If not in batch (limit 100?), check specifically before skipping
                     if verify_monday_item_exists(monday_parent_id):
                         print(f"  [VERIFY] Parent {monday_parent_id} exists (was missing from batch). Proceeding.")
                         parent_exists = True
                         monday_item_ids.add(monday_parent_id) # Cache to avoid re-querying for siblings

                if parent_exists: 
                    print(f"[SYNC] Creating Monday Subitem for {key} (Parent {monday_parent_id}) [Status: '{jira_status}' -> '{monday_status_idx}']")
                    sub_item = create_monday_subitem(monday_parent_id, monday_title, monday_status_idx)
                    if sub_item:
                        m_id = sub_item['id']
                        db['jira_to_monday'][key] = m_id
                        db['monday_to_jira'][m_id] = key
                        save_db(db)
                        
                        # Sync Description to Update (Comment)
                        desc_adf = sub['fields'].get('description')
                        desc_text = extract_text_from_adf(desc_adf)
                        if desc_text and desc_text.strip():
                             print(f"  -> Posting Description Update check...")
                             create_monday_update(m_id, f"**Synced Description:**\\n{desc_text}")
                        
                        sync_attachments(sub, m_id)

                        # Sync Checklist (New Creation)
                        checklist_content = fetch_jira_checklist_content(key)
                        if checklist_content:
                            print(f"  -> Syncing Checklist to Column for New Subitem {key}...")
                            col_vals = json.dumps({MONDAY_CHECKLIST_COLUMN_ID: checklist_content}).replace('"', '\\"')
                            
                            query_checklist = f'''
                            mutation {{
                                change_multiple_column_values (item_id: {m_id}, board_id: {MONDAY_SUBITEM_BOARD_ID}, column_values: "{col_vals}") {{
                                    id
                                }}
                            }}
                            '''
                            requests.post("https://api.monday.com/v2", json={"query": query_checklist}, headers=get_monday_headers())

                else: 
                     print(f"[SKIP] Parent {monday_parent_id} exists in DB but missing on Monday. Cannot create subitem {key}.")
            else:
                print(f"[SKIP] Parent {jira_parent_key} not found in Monday map for subtask {key}")

    # 4. Sync Monday -> Jira (Main items only for MVP)
    # USER REQUEST: "if i edit an item in monday kanban, i don't want it to change jira item unless specifically requested"
    # We will DISABLE auto-update from Monday to Jira.
    ENABLE_MONDAY_TO_JIRA_UPDATE = False

    for item in monday_items:
        m_id = item['id']
        name = item['name']
        monday_status_idx = "5"
        for col in item.get('column_values', []):
             if col['id'] == 'status': monday_status_idx = str(col.get('index', 5))

        if m_id in db['monday_to_jira']:
             if ENABLE_MONDAY_TO_JIRA_UPDATE:
                 j_key = db['monday_to_jira'][m_id]
                 update_jira_issue(j_key, name, monday_status_idx)
        else:
            if name.strip().startswith(f"[{JIRA_PROJECT}-"): continue
            
            print(f"[SYNC] Creating Jira issue for Monday item {m_id}")
            j_issue = create_jira_issue(name, status_index=monday_status_idx)
            if j_issue:
                j_key = j_issue['key']
                db['jira_to_monday'][j_key] = m_id
                db['monday_to_jira'][m_id] = j_key
                save_db(db)

    db['last_sync'] = str(datetime.datetime.now())
    save_db(db)
    print("--- Sync Complete ---")

if __name__ == "__main__":
    sync()
