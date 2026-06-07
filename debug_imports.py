"""
Simple test to verify the imports work.
"""
import sys
import os

# Print current directory and path
print("Current directory:", os.getcwd())
print("Python path:", sys.path)

# Try to import
try:
    from botilleria_core.config.database import SessionLocal
    print("✓ Successfully imported SessionLocal")
except Exception as e:
    print("✗ Failed to import SessionLocal:", e)
    
try:
    from botilleria_core.config.settings import settings
    print("✓ Successfully imported settings")
except Exception as e:
    print("✗ Failed to import settings:", e)
    
try:
    from botilleria_core.models import Tenant
    print("✓ Successfully imported Tenant")
except Exception as e:
    print("✗ Failed to import Tenant:", e)