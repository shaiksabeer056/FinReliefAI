import requests

BASE_URL = "http://localhost:8000"

def test_flow():
    # 1. Register a test user if not exists
    reg_data = {
        "email": "verify@example.com",
        "password": "verify_password123",
        "name": "Verification User"
    }
    
    print("Testing Registration...")
    r = requests.post(f"{BASE_URL}/api/auth/register", json=reg_data)
    print("Reg Status:", r.status_code)
    if r.status_code == 201:
        print("Registration success!")
    elif r.status_code == 400 and "already registered" in r.text.lower():
        print("User already exists, proceeding to login.")
    else:
        print("Registration failed:", r.text)
        return

    # 2. Login
    login_data = {
        "email": "verify@example.com",
        "password": "verify_password123"
    }
    print("\nTesting Login...")
    r = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print("Login Status:", r.status_code)
    if r.status_code != 200:
        print("Login failed:", r.text)
        return
        
    tokens = r.json()
    access_token = tokens["access_token"]
    print("Login success! Got access token:", access_token[:20] + "...")

    # 3. Call /me endpoint
    headers = {"Authorization": f"Bearer {access_token}"}
    print("\nTesting /api/auth/me...")
    r = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    print("/me Status:", r.status_code)
    print("/me Response:", r.json())
    
    # 4. Call dashboard metrics
    print("\nTesting /api/dashboard/metrics...")
    r = requests.get(f"{BASE_URL}/api/dashboard/metrics", headers=headers)
    print("Metrics Status:", r.status_code)
    print("Metrics keys:", r.json().keys() if r.status_code == 200 else r.text)

if __name__ == "__main__":
    test_flow()
