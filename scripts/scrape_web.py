import time
import requests
from bs4 import BeautifulSoup
import json
import os

SITES_TO_SCRAPE = [
    {
        "url": "http://erasmus.agu.edu.tr/fqa",
        "tag": "div",
        "class_name": "content-widget-area",
        "lang": "en",
    },
    {
        "url": "https://oidb-en.agu.edu.tr/FREQUENTLY%20ASKED%20QUESTIONS",
        "tag": "div",
        "class_name": "col-md-12 blog-content",
        "lang": "en",
    },
    {
        "url": "https://eeew4.agu.edu.tr/faq",
        "tag": "div",
        "class_name": "col-md-12 blog-content",
        "lang": "en",
    },
    {
        "url": "http://www.agu.edu.tr/rektortr",
        "tag": "div",
        "class_name": "content-widget-area",
        "lang": "tr",
    },
    {
        "url": "http://www.agu.edu.tr/tarihce",
        "tag": "div",
        "class_name": "content-widget-area",
        "lang": "tr",
    },
    {
        "url": "http://www.agu.edu.tr/agu-degerleri",
        "tag": "div",
        "class_name": "content-widget-area",
        "lang": "tr",
    },
    {
        "url": "https://aday.agu.edu.tr/ingilizce-egitim.html",
        "tag": "div",
        "class_name": "col-md-12 blog-content text-black",
        "lang": "tr",
    },
    {
        "url": "https://aday.agu.edu.tr/yurt-disi-staj.html",
        "tag": "div",
        "class_name": "col-md-12 blog-content text-black",
        "lang": "tr",
    },
    {
        "url": "https://aday.agu.edu.tr/genclik-fabrikasi.html",
        "tag": "div",
        "class_name": "col-md-12 blog-content text-black",
        "lang": "tr",
    },
    {
        "url": "https://aday.agu.edu.tr/laboratuar.html",
        "tag": "div",
        "class_name": "col-md-12 blog-content text-black",
        "lang": "tr",
    },
    {
        "url": "https://aday.agu.edu.tr/kampuste-yasam.html",
        "tag": "div",
        "class_name": "col-md-12 blog-content text-black",
        "lang": "tr",
    },
    {
        "url": "https://aday.agu.edu.tr/kayseride-yasam.html",
        "tag": "div",
        "class_name": "col-md-12 blog-content text-black",
        "lang": "tr",
    },
    {
        "url": "http://www.agu.edu.tr/akreditasyonlarimiz",
        "tag": "div",
        "class_name": "content-widget-area",
        "lang": "tr",
    }

]

# Output file
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'scraped_content.json')

# Headers to mimic a real browser
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/91.0.4472.124 Safari/537.36'
    )
}


def scrape_site(url, tag, class_name, lang=None):
    """
    Scrapes a single website, finds the main content block, and then
    extracts text from all relevant sub-tags (p, li, h1-h6).
    Adds:
      - type: heading / paragraph / list_item
      - lang: language code (if provided)
    """
    print(f"Scraping: {url}")
    try:
        # Use verify=False to ignore SSL certificate errors
        response = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        response.raise_for_status()
    except requests.exceptions.SSLError as e:
        print(f"SSL Error for {url}. Bypassed with verify=False. Error: {e}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error scraping {url}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the main content block
    content_block = soup.find(tag, class_=class_name)

    if not content_block:
        print(f"Warning: No main content block found for tag '{tag}' and class '{class_name}' at {url}")
        return []

    data = []

    # Find all relevant tags within the main content block
    for element in content_block.find_all(['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        text = element.get_text(strip=True, separator=" ")

        cleaned_text = ' '.join(text.split())

        # Only add non-empty strings that have meaningful content
        if cleaned_text and len(cleaned_text) > 10:  # Avoid tiny fragments
            tag_name = element.name

            if tag_name.startswith('h'):
                section_type = 'heading'
            elif tag_name == 'li':
                section_type = 'list_item'
            else:
                section_type = 'paragraph'

            entry = {
                "source": url,
                "content": cleaned_text,
                "type": section_type,
            }

            # Only include lang if we have it
            if lang:
                entry["lang"] = lang

            data.append(entry)

    if not data:
        print(
            f"Warning: Main block was found, but no <p>, <li>, or <h*> tags with content were found inside it at {url}"
        )

    return data


def main():
    """
    Main function to orchestrate the scraping process.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_data = []
    print(f"Starting web scraping for {len(SITES_TO_SCRAPE)} site(s)...")

    # Disable SSL warnings from requests
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

    for site in SITES_TO_SCRAPE:
        scraped_data = scrape_site(
            site['url'],
            site['tag'],
            site['class_name'],
            lang=site.get('lang'),
        )
        all_data.extend(scraped_data)
        time.sleep(1)

    # Save the combined data to the output file
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"Error writing to JSON file {OUTPUT_FILE}: {e}")
        return

    print(f"\nSuccessfully scraped and processed {len(all_data)} content block(s).")
    print(f"Data saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
