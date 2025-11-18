import requests
import feedparser

KEYWORDS = ['corvid','crow','raven','corvus','jay','magpie','jackdaw','rook','chough','nutcracker']

def search_arxiv_clean(keywords, max_results=10):
    query = " OR ".join(keywords)
    url = (
        "https://export.arxiv.org/api/query?"
        f"search_query=all:({query})&"
        f"start=0&max_results={max_results}&"
        "sortBy=lastUpdatedDate&sortOrder=descending"
    )

    data = requests.get(url).text
    feed = feedparser.parse(data)

    cleaned = []

    for entry in feed.entries:
        # skip if summary missing or empty
        if not hasattr(entry, "summary") or not entry.summary.strip():
            continue

        cleaned.append({
            "title": entry.title,
            "abstract": entry.summary.replace("\n", " "),
            "authors": [a.name for a in entry.authors],
            "published": entry.published,
            "link": entry.link,
        })

    return cleaned

if __name__ == "__main__":
    results = search_arxiv_clean(KEYWORDS, max_results=1)
    for r in results:
        print(r)
