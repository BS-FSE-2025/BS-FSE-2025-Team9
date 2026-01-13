import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("TESTING DJANGO REQUEST MANAGEMENT SYSTEM")
print("=" * 60)

# Test 1: Login
print("\n1. LOGIN as Head of Department")
print("-" * 60)
try:
    response = requests.post(
        f"{BASE_URL}/login/",
        json={"email": "head@example.com", "password": "password"},
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        cookies = response.cookies
        sessionid = cookies.get('sessionid')
        print(f"[OK] Login successful! Session ID: {sessionid[:20]}...")
    else:
        print(f"[FAIL] Login failed: {response.text[:200]}")
        cookies = None
except Exception as e:
    print(f"[ERROR] {e}")
    cookies = None

if cookies:
    # Test 2: Get Pending Requests
    print("\n2. GET PENDING REQUESTS")
    print("-" * 60)
    try:
        response = requests.get(
            f"{BASE_URL}/api/head/pending-requests/",
            cookies=cookies
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Total Pending Requests: {data.get('count', 0)}")
            if data.get('requests'):
                print("\nFirst Request:")
                req = data['requests'][0]
                print(f"  ID: {req.get('id')}")
                print(f"  Title: {req.get('title')}")
                print(f"  Type: {req.get('request_type')}")
                print(f"  Status: {req.get('status')}")
                print(f"  Priority: {req.get('priority')}")
                print(f"  Student: {req.get('student_name')}")
                print(f"  Created: {req.get('created_at')}")
                print("[OK] Pending requests retrieved successfully!")
                request_id = req.get('id')
            else:
                print("No pending requests found.")
                request_id = None
        else:
            print(f"[FAIL] Failed: {response.text[:200]}")
            request_id = None
    except Exception as e:
        print(f"[ERROR] {e}")
        request_id = None

    if request_id:
        # Test 3: Approve Request
        print("\n3. APPROVE REQUEST")
        print("-" * 60)
        try:
            response = requests.post(
                f"{BASE_URL}/api/head/approve-request/{request_id}/",
                json={"action": "approve", "notes": "Approved via API test"},
                cookies=cookies,
                headers={"Content-Type": "application/json"}
            )
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                print("[OK] Request approved successfully!")
            else:
                print(f"[FAIL] Failed: {response.text[:200]}")
        except Exception as e:
            print(f"[ERROR] {e}")

        # Test 4: Add Final Notes
        print("\n4. ADD FINAL NOTES")
        print("-" * 60)
        try:
            response = requests.post(
                f"{BASE_URL}/api/head/add-final-notes/{request_id}/",
                json={"notes": "These are final notes visible to the student. Request has been processed and approved."},
                cookies=cookies,
                headers={"Content-Type": "application/json"}
            )
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                print("[OK] Final notes added successfully!")
            else:
                print(f"[FAIL] Failed: {response.text[:200]}")
        except Exception as e:
            print(f"[ERROR] {e}")

        # Test 5: Get Request Details
        print("\n5. GET REQUEST DETAILS")
        print("-" * 60)
        try:
            response = requests.get(
                f"{BASE_URL}/api/head/request-details/{request_id}/",
                cookies=cookies
            )
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"\nRequest Details:")
                req = data.get('request', {})
                print(f"  Title: {req.get('title')}")
                print(f"  Status: {req.get('status')}")
                print(f"  Final Notes: {req.get('final_notes', 'None')}")
                print(f"\nApproval Logs: {len(data.get('approval_logs', []))} entries")
                for log in data.get('approval_logs', [])[:3]:
                    print(f"  - {log.get('action').upper()} by {log.get('approver_name')} on {log.get('created_at')}")
                print("[OK] Request details retrieved successfully!")
            else:
                print(f"[FAIL] Failed: {response.text[:200]}")
        except Exception as e:
            print(f"[ERROR] {e}")

    # Test 6: Filter Requests
    print("\n6. FILTER REQUESTS BY TYPE")
    print("-" * 60)
    try:
        response = requests.get(
            f"{BASE_URL}/api/head/pending-requests/?request_type=Study Approval",
            cookies=cookies
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Filtered Results: {data.get('count', 0)} requests of type 'Study Approval'")
            print("[OK] Filtering works!")
        else:
            print(f"[FAIL] Failed: {response.text[:200]}")
    except Exception as e:
        print(f"[ERROR] {e}")

print("\n" + "=" * 60)
print("TESTING COMPLETE")
print("=" * 60)
