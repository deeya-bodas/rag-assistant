# Import required libraries
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import json

# Set the base URL to start crawling from
BASE_URL = "https://developer.visa.com"
# Set the maximum number of pages to crawl - 400 is arbirtrary and can be updated later
MAX_PAGES = 400

# Track visited URLs to avoid revisiting
visited = set()
# Queue of URLs to visit, starting with the base URL
to_visit = deque([BASE_URL])

# List to store the site map information
site_map = []

# Function to determine if a link is valid for crawling
def is_valid_link(link):
    parsed = urlparse(link)
    return link.startswith(BASE_URL) and not any(skip in parsed.path for skip in ["/static", "/images", "/fonts", "/contact"])

# Main crawling loop: continue until queue is empty or max pages reached
while to_visit and len(visited) < MAX_PAGES:
    url = to_visit.popleft()
    if url in visited:
        continue
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            continue
        soup = BeautifulSoup(res.text, "html.parser")
        title = soup.title.string.strip() if soup.title else ""
        links = {urljoin(BASE_URL, a['href']) for a in soup.find_all("a", href=True)}
        valid_links = [l for l in links if is_valid_link(l) and l not in visited]

        # Add the current page's info (URL, title, links) to the site map -- save URL for the RAG system to tell you about later
        site_map.append({
            "url": url,
            "title": title,
            "links": valid_links
        })

        # Add valid links to the queue for future crawling
        to_visit.extend(valid_links)
        visited.add(url)

        print(f"Crawled: {url} - found {len(valid_links)} links")
    except Exception as e:
        print(f"Failed to crawl {url}: {e}")

# Save the site map as a JSON file
with open("visa_site_map.json", "w") as f:
    json.dump(site_map, f, indent=2)

print(f"Site map saved with {len(site_map)} pages.")