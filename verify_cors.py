import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from fastapi.middleware.cors import CORSMiddleware

from app.main import app

print("Checking Middleware...")
cors_middleware = None
for middleware in app.user_middleware:
    if middleware.cls == CORSMiddleware:
        cors_middleware = middleware
        break

if cors_middleware:
    print("CORSMiddleware found!")
    print(f"Allowed Origins: {cors_middleware.options['allow_origins']}")
    expected_origin = "https://vietcycleconnect.vercel.app"
    if expected_origin in cors_middleware.options["allow_origins"]:
        print(f"SUCCESS: {expected_origin} is in allowed origins.")
    else:
        print(f"FAILURE: {expected_origin} is NOT in allowed origins.")
        sys.exit(1)
else:
    print("FAILURE: CORSMiddleware NOT found.")
    sys.exit(1)
