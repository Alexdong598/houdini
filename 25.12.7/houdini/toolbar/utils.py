import os
import sys
import re
import json
import logging

def add_module_path():
    path = os.getenv("PATH")
    new_path = re.split(r";", path)[7]
    if new_path not in sys.path:
        sys.path.append(new_path)

def read_json_file(json_path):
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    try:
        with open(json_path, "r") as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to read JSON file: {e}")

def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")