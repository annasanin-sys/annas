def normalize_monday_update(update_body):
    """Normalizes Monday update body for comparison with Jira text."""
    if not update_body: return ""
    marker = "**Synced Description:**"
    if marker in update_body:
        update_body = update_body.replace(marker, "", 1)
    
    text = update_body.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    return text.strip()

def test_normalization():
    print("Testing Normalization...")
    monday_raw = "**Synced Description:**<br>Line 1<br>Line 2"
    expected = "Line 1\nLine 2"
    normalized = normalize_monday_update(monday_raw)
    
    print(f"Raw: '{monday_raw}'")
    print(f"Norm: '{normalized}'")
    print(f"Expected: '{expected}'")
    
    if normalized == expected:
        print("[PASS] Normalization works.")
    else:
        print("[FAIL] Normalization mismatch.")

if __name__ == "__main__":
    test_normalization()
