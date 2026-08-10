import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def _normalize_url(raw_url: str) -> str | none:
    if not raw_url:
        return None
    url = raw_url.strip()
    if not url:
        return None

    parsed = urlparse(url)
    if parsed.scheme in ("http", "https"):
        return url

    # If the user entered a domain without https//http://
    return f"https://{url}"


def get_links_from_web(url: str, limit: int = 10) -> list[str]:
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    links: list[str] = []

    for a in soup.find_all("a"):
        href = a.get("href")
        if href:
            links.append(href)
        if len(links) >= limit:
            break
    return links


def main() -> None:
    raw_url = input("Enter Link: ")
    url = _normalize_url(raw_url)

    if url is None:
        print("Please enter a valid web link.")
        return

    try:
        links = get_links_from_web(url, limit=10)
    except Exception as err:
        print(f"Could not read that page. Error: {err}")
        return
    
    # Save one link per line for easy reading
    with open("myLinks.txt", "a", encoding="utf-8") as f:
        for h in links:
            f.write(h + "\n")

    print(f"Saved {len(links)} links to myLinks.txt")


if __name__ == "__main__":
    main()
