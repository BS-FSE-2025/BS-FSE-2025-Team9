import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("TESTING STATISTICS ENDPOINT")
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

# Get statistics
print("\n2. GET STATISTICS")
print("-" * 60)
response = requests.get(f"{BASE_URL}/api/head/statistics/", cookies=cookies)
print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    if data.get('success'):
        stats = data.get('statistics', {})
        print("\n[OK] Statistics retrieved successfully!")
        print(f"\nOverall Statistics:")
        print(f"  Total Requests: {stats.get('total', 0)}")
        print(f"  Approved: {stats.get('approved', 0)}")
        print(f"  Rejected: {stats.get('rejected', 0)}")
        print(f"  Pending: {stats.get('pending', 0)}")
        print(f"  In Progress: {stats.get('in_progress', 0)}")
        print(f"  Processed: {stats.get('processed', 0)}")
        print(f"\n  Approval Rate: {stats.get('approval_rate', 0)}%")
        print(f"  Rejection Rate: {stats.get('rejection_rate', 0)}%")
        
        print(f"\nStatistics by Request Type:")
        by_type = stats.get('by_type', {})
        for req_type, type_stats in by_type.items():
            print(f"\n  {req_type}:")
            print(f"    Total: {type_stats.get('total', 0)}")
            print(f"    Approved: {type_stats.get('approved', 0)} ({type_stats.get('approval_rate', 0)}%)")
            print(f"    Rejected: {type_stats.get('rejected', 0)} ({type_stats.get('rejection_rate', 0)}%)")
            print(f"    Pending: {type_stats.get('pending', 0)}")
    else:
        print("[FAIL] Statistics request failed")
else:
    print(f"[FAIL] Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")

print("\n" + "=" * 60)
print("STATISTICS TEST COMPLETE")
print("=" * 60)
