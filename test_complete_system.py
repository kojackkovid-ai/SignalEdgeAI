import requests

print("\nSYSTEM STATUS CHECK")
print("="*50)

# Check Backend
try:
    r = requests.get("http://localhost:8000/health", timeout=3)
    if r.status_code == 200:
        print("Backend (port 8000): RUNNING")
    else:
        print(f"Backend: ERROR {r.status_code}")
except:
    print("Backend: NOT RUNNING")

# Check Frontend
try:
    r = requests.get("http://localhost:5173", timeout=3)
    if r.status_code == 200:
        print("Frontend (port 5173): RUNNING")
    else:
        print(f"Frontend: ERROR {r.status_code}")
except:
    print("Frontend: NOT RUNNING")

print("="*50)
print("\nPAYMENT FLOW TEST:")
print("1. Open: http://localhost:5173")
print("2. Register/Login")
print("3. Go to Pricing page")
print("4. Click 'Upgrade' on any plan")
print("5. Test card: 4242 4242 4242 4242")
print("6. Expiry: 12/26, CVC: 123")
print("7. Verify tier upgrade\n")
