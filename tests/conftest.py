"""Config for starting tests"""

import os
import sys

ROOT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "src", "backend")
)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

PACKAGES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "src", "packages")
)
if PACKAGES_DIR not in sys.path:
    sys.path.insert(0, PACKAGES_DIR)
