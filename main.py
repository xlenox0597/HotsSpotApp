"""
Apple USB HotSpot Manager - Main Entry Point
"""

import sys
import os

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.driver_manager import is_admin, install_drivers, run_as_admin, check_driver_store
from src.ui import run_app


def main():
    if "--install-drivers" in sys.argv:
        if not is_admin():
            print("Requesting administrator privileges to install drivers...")
            if not run_as_admin(sys.argv):
                print("Failed to elevate permissions.")
                sys.exit(1)
            sys.exit(0)
            
        success, msg = install_drivers()
        print(msg)
        sys.exit(0 if success else 1)

    if "--check-drivers" in sys.argv:
        status = check_driver_store()
        print(status)
        sys.exit(0 if all(status.values()) else 1)

    # Launch graphical interface
    run_app()


if __name__ == "__main__":
    main()
