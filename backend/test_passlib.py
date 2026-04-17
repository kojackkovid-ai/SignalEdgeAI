from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Test with long password
long_password = "a" * 100
print(f"Testing password of length: {len(long_password)}")

try:
    hashed = pwd_context.hash(long_password)
    print(f"Success! Hash: {hashed[:50]}...")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
