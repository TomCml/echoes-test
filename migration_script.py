
import os
import re

TARGET_DIRS = [
    "backend/app",
    "backend/routes",
    "backend/controllers",
    "backend"
]

REPLACEMENTS = [
    (r"from models", "from app.models"),
    (r"from schemas", "from app.schemas"),
    (r"from core.database", "from app.core.database"),
    (r"from core.effects", "from app.engine.effects"),
    (r"from core.engine", "from app.engine.combat"),
    (r"import core.database", "import app.core.database"),
    # Add more as needed
]

def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    new_content = content
    for pattern, replacement in REPLACEMENTS:
        new_content = re.sub(pattern, replacement, new_content)
    
    if content != new_content:
        print(f"Updating {filepath}")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)

def main():
    root_dir = os.path.abspath(".")
    for path in TARGET_DIRS:
        full_path = os.path.join(root_dir, path)
        if os.path.isfile(full_path):
             if full_path.endswith(".py"):
                 process_file(full_path)
             continue

        for root, dirs, files in os.walk(full_path):
            for file in files:
                if file.endswith(".py") and file != "migration_script.py":
                    process_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
