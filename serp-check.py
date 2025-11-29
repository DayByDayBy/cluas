import serpapi
import inspect

# See the GoogleSearch class
print("=== GoogleSearch Class ===")
print(inspect.getsource(serpapi.GoogleSearch))

# See the google_search function
print("\n=== google_search Function ===")
print(inspect.getsource(serpapi.google_search))

# See their signatures
print("\n=== Signatures ===")
print("GoogleSearch:", inspect.signature(serpapi.GoogleSearch))
print("google_search:", inspect.signature(serpapi.google_search))

# See what methods GoogleSearch has
print("\n=== GoogleSearch Methods ===")
gs = serpapi.GoogleSearch({})
print(dir(gs))

# See GoogleSearch __init__ docstring
print("\n=== GoogleSearch Docstring ===")
print(serpapi.GoogleSearch.__doc__)