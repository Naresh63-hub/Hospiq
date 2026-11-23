"""HospitalIQ - Healthcare Analytics Dashboard Entry Point (v2.1).

This root entry file forwards execution to dashboard/app.py, allowing
seamless deployment on Streamlit Community Cloud with default settings.
"""

import os
import sys

# Ensure repository root is on sys.path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Import and execute main dashboard
from dashboard.app import main

if __name__ == "__main__":
    main()
