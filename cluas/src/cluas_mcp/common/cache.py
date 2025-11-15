import json
from pathlib import Path

class CacheManager:
    def __init__(self, cache_file: str):
        self.cache_file = Path(cache_file)
        if not self.cache_file.exists():
            self.cache_file.write_text(json.dumps({}))

    def get(self, query: str):
        with open(self.cache_file, "r") as f:
            data = json.load(f)
        return data.get(query)

    def set(self, query: str, results):
        with open(self.cache_file, "r") as f:
            data = json.load(f)
        data[query] = results
        with open(self.cache_file, "w") as f:
            json.dump(data, f, indent=2)
