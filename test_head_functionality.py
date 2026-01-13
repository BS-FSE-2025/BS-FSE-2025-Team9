"""
Test script for Department Head functionality
Run this after starting the Flask server to test all features
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000"

def test_login():
    """Test login as head of department"""
    print("Testing login...")
    response = requests.post(
        f"{BASE_URL}/login",
        json={"email": "head@example.com", "password": "password"},
        headers={"Content-Type": "application/json"}
    )
    if response.status_code == 200:
        print("✓ Login successful")
        return response.cookies
    else:
        print("✗ Login failed")
        return None

def test_get_pending_requests(cookies):
    """Test fetching pending requests"""
    print("\nTesting get pending requests...")
    response = requests.get(
        f"{BASE_URL}/api/head/pending-requests",
        cookies=cookies
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {data['count']} pending requests")
        return True
    else:
        print(f"✗ Failed: {response.status_code}")
        return False

def test_filter_requests(cookies):
    """Test filtering requests by type"""
    print("\nTesting filter by request type...")
    response = requests.get(
        f"{BASE_URL}/api/head/pending-requests?request_type=Study Approval",
        cookies=cookies
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Filtered requests: {data['count']} found")
        return True
    else:
        print(f"✗ Filter failed: {response.status_code}")
        return False

def test_approve_request(cookies):
    """Test approving a request"""
    print("\nTesting approve request...")
    # First get a pending request
    response = requests.get(
        f"{BASE_URL}/api/head/pending-requests",
        cookies=cookies
    )
    if response.status_code == 200:
        data = response.json()
        if data['requests']:
            request_id = data['requests'][0]['id']
            response = requests.post(
                f"{BASE_URL}/api/head/approve-request/{request_id}",
                json={"action": "approve", "notes": "Test approval"},
                cookies=cookies,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                print(f"✓ Request {request_id} approved successfully")
                return True
            else:
                print(f"✗ Approval failed: {response.status_code}")
                return False
        else:
            print("✗ No pending requests to approve")
            return False
    else:
        print("✗ Could not fetch requests")
        return False

def test_add_final_notes(cookies):
    """Test adding final notes"""
    print("\nTesting add final notes...")
    # Get an approved request (or create one)
    response = requests.get(
        f"{BASE_URL}/api/head/pending-requests",
        cookies=cookies
    )
    if response.status_code == 200:
        data = response.json()
        if data['requests']:
            request_id = data['requests'][0]['id']
            response = requests.post(
                f"{BASE_URL}/api/head/add-final-notes/{request_id}",
                json={"notes": "These are final notes visible to the student."},
                cookies=cookies,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                print(f"✓ Final notes added to request {request_id}")
                return True
            else:
                print(f"✗ Failed to add notes: {response.status_code}")
                return False
        else:
            print("✗ No requests available")
            return False
    else:
        print("✗ Could not fetch requests")
        return False

def main():
    print("=" * 50)
    print("Department Head Functionality Test")
    print("=" * 50)
    
    # Test login
    cookies = test_login()
    if not cookies:
        print("\nCannot proceed without login. Make sure the server is running.")
        return
    
    # Run tests
    results = []
    results.append(("Get Pending Requests", test_get_pending_requests(cookies)))
    results.append(("Filter Requests", test_filter_requests(cookies)))
    results.append(("Approve Request", test_approve_request(cookies)))
    results.append(("Add Final Notes", test_add_final_notes(cookies)))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    print(f"\nTotal: {passed}/{len(results)} tests passed")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server.")
        print("Make sure the Flask server is running on http://localhost:5000")
    except Exception as e:
        print(f"Error: {e}")
