import serpapi
import inspect

# google_search is a MODULE, so let's see what's IN it
print("=== google_search module contents ===")
print(dir(serpapi.google_search))

# See what's exported
print("\n=== Checking for functions in google_search ===")
for name in dir(serpapi.google_search):
    if not name.startswith('_'):
        obj = getattr(serpapi.google_search, name)
        print(f"{name}: {type(obj)}")

# Try to find the actual function
print("\n=== Looking for callable ===")
if hasattr(serpapi.google_search, 'GoogleSearch'):
    print("Found GoogleSearch in module")
if hasattr(serpapi.google_search, 'search'):
    print("Found search function")