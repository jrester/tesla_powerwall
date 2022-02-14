import json
import os

ENDPOINT = "https://1.1.1.1/api/"

PREFIX = "tests/unit/fixtures"


def _load_fixtures():
    for file in os.listdir("tests/unit/fixtures"):
        if file.endswith(".json"):
            file_path = os.path.join(PREFIX, file)
            with open(file_path) as f:
                name = file[:-5].upper() + "_RESPONSE"
                globals()[name] = json.loads(f.read())


_load_fixtures()
