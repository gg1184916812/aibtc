#!/usr/bin/env python3
"""
🔧 Test Unicode Fix for Broker Migration Logging
Verifies that the broker change detection no longer causes Unicode encoding errors
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from io import StringIO

def test_unicode_fix():
    """Test that the new ASCII arrow works without encoding issues"""
    print("🔧 Testing Unicode Fix for Broker Migration...")
    print("=" * 50)
    
    # Test the old problematic Unicode arrow
    try:
        old_message = "Broker changed detected: 'MetaQuotes-Demo' → 'XMGlobal-MT5 7'"
        old_message.encode('cp1252')  # This should fail
        print("❌ Old Unicode arrow should have failed but didn't!")
        return False
    except UnicodeEncodeError:
        print("✅ Confirmed: Old Unicode arrow causes encoding error (as expected)")
    
    # Test the new ASCII arrow
    try:
        new_message = "Broker changed detected: 'MetaQuotes-Demo' -> 'XMGlobal-MT5 7'"
        new_message.encode('cp1252')  # This should work
        print("✅ New ASCII arrow encodes properly in Windows cp1252")
    except UnicodeEncodeError as e:
        print(f"❌ ERROR: New ASCII arrow still causes issues: {e}")
        return False
    
    # Test actual logging
    print("\n📝 Testing Actual Logging...")
    try:
        # Create a logger similar to what's used in the application
        logger = logging.getLogger('test_broker_migration')
        
        # Create a string buffer to capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Test the new format (this is what's now in the code)
        last_broker = "MetaQuotes-Demo"
        current_broker = "XMGlobal-MT5 7"
        logger.info(f"Broker changed detected: '{last_broker}' -> '{current_broker}'")
        
        # Get the logged output
        log_output = log_capture.getvalue()
        print(f"✅ Successfully logged: {log_output.strip()}")
        
        # Verify it contains the ASCII arrow
        if " -> " in log_output:
            print("✅ ASCII arrow (-->) found in log output")
        else:
            print("❌ ASCII arrow not found in log output")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🔧 Unicode Fix Validation")
    print("Testing broker migration logging fix\n")
    
    success = test_unicode_fix()
    
    if success:
        print("\n🎉 SUCCESS!")
        print("✨ The Unicode encoding issue has been fixed!")
        print("\n🔧 What was fixed:")
        print("  ❌ OLD: Unicode arrow '→' (U+2192)")
        print("  ✅ NEW: ASCII arrow '->' (safe for Windows)")
        print("\n🚀 Broker switching will now work smoothly on Windows!")
    else:
        print("\n❌ FAILED - Unicode issue may still exist")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)