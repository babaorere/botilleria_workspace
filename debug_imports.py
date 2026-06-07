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
    print("✓ Successfully imported SessionLocal")
except Exception as e:
    print("✗ Failed to import SessionLocal:", e)
    
try:
    print("✓ Successfully imported settings")
except Exception as e:
    print("✗ Failed to import settings:", e)
    
try:
    print("✓ Successfully imported Tenant")
except Exception as e:
    print("✗ Failed to import Tenant:", e)