import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("TESTING COMMENT FUNCTIONALITY")
print("=" * 60)

# Login
print("\n1. LOGIN as Head of Department")
print("-" * 60)
response = requests.post(
    f"{BASE_URL}/login/",
    json={"email": "head@example.com", "password": "password"},
    headers={"Content-Type": "application/json"}
)
print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    cookies = response.cookies
    print("[OK] Login successful!")
else:
    print("[FAIL] Login failed")
    exit(1)

# Get a pending request
print("\n2. GET PENDING REQUESTS")
print("-" * 60)
response = requests.get(f"{BASE_URL}/api/head/pending-requests/", cookies=cookies)
if response.status_code == 200:
    data = response.json()
    if data.get('requests'):
        request_id = data['requests'][0]['id']
        print(f"[OK] Found request ID: {request_id}")
        print(f"Title: {data['requests'][0]['title']}")
    else:
        print("[FAIL] No requests found")
        exit(1)
else:
    print("[FAIL] Could not get requests")
    exit(1)

# Add a comment
print("\n3. ADD COMMENT")
print("-" * 60)
response = requests.post(
    f"{BASE_URL}/api/head/add-comment/{request_id}/",
    json={"comment": "This is a test comment from the Department Head. Need to review this request carefully."},
    cookies=cookies,
    headers={"Content-Type": "application/json"}
)
print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"[OK] Comment added successfully!")
    print(f"Comment: {data.get('comment', {}).get('comment', '')}")
else:
    print(f"[FAIL] Failed: {response.text[:200]}")

# Add another comment
print("\n4. ADD SECOND COMMENT")
print("-" * 60)
response = requests.post(
    f"{BASE_URL}/api/head/add-comment/{request_id}/",
    json={"comment": "Second comment: Request looks good, will approve after verification."},
    cookies=cookies,
    headers={"Content-Type": "application/json"}
)
print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    print("[OK] Second comment added!")

# Get request details with comments
print("\n5. GET REQUEST DETAILS WITH COMMENTS")
print("-" * 60)
response = requests.get(f"{BASE_URL}/api/head/request-details/{request_id}/", cookies=cookies)
if response.status_code == 200:
    data = response.json()
    comments = data.get('comments', [])
    print(f"[OK] Found {len(comments)} comment(s)")
    for i, comment in enumerate(comments, 1):
        print(f"\nComment {i}:")
        print(f"  Author: {comment.get('author_name')}")
        print(f"  Date: {comment.get('created_at')}")
        print(f"  Comment: {comment.get('comment')}")

print("\n" + "=" * 60)
print("COMMENT TESTING COMPLETE")
print("=" * 60)
