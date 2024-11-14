import requests
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: The 'bs4' package is not installed.")
    print("To install it, run: pip install beautifulsoup4")
    exit(1)
import concurrent.futures
from collections import defaultdict
import re
from urllib.parse import urljoin

# sample command:
# python wiki_check_articles.py "https://wiki.warthunder.com/Category:Sixth_rank_ships"

WIKI_BASE_URL = "https://wiki.warthunder.com"
SECTIONS_TO_CHECK = [
    "Description",
    "Survivability and armour",
    "Mobility",
    "Primary armament", # Naval
    "Main armament", # Ground
    "Offensive armament", # Air, Helicopters
    "Secondary armament", 
    "Anti-aircraft armament",
    "Additional armament",
    "Suspended armament", # Air, Drones, Helicopters
    "Defensive armament", # Air
    "Scout plane", # Naval
    "Usage in battles",
    "Pros and cons",
    "History"
]

def get_page_content(url):
    try:
        response = requests.get(url)
        if response.status_code == 502:
            print(f"\nWiki errored with 502 code when trying to read {url}. Stopping the program. Please, try again in a few seconds.")
            sys.exit(1)
        if response.status_code == 404:  # Handle 404 silently
            print(f"\nWiki errored with 404 code when trying to read {url}.")
            return None
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def check_sections(url):
    content = get_page_content(url)
    if not content:
        return None, []
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Get page title
    title = soup.find('h1', {'id': 'firstHeading'})
    if title:
        title = title.text.strip()
    else:
        title = url.split('/')[-1]
    
    found_sections_with_content = []
    found_sections_with_no_content = []
    
    # Check Description section - requires at least 2 paragraphs
    for header in soup.find_all(['h2', 'h3']):
        if header.get_text().strip() == "Description":
            paragraph_count = 0
            current = header.next_sibling
            while current and not current.name in ['h2', 'h3']:
                if current.name == 'p' and current.get_text().strip():
                    paragraph_count += 1
                current = current.next_sibling
            
            if paragraph_count >= 2:
                found_sections_with_content.append("Description")
            else:
                found_sections_with_no_content.append("Description")
    
    # Check all other sections - require real content (not just template text)
    for header in soup.find_all(['h2', 'h3']):  # Look for both h2 and h3 headers
        header_text = header.get_text().strip()
        
        # Skip Description as it's handled separately
        if header_text == "Description":
            continue
            
        # Check if this header matches any of our target sections
        for section in SECTIONS_TO_CHECK:
            if section.lower() == header_text.lower():
                # Check content between this header and the next header of same or higher level
                current = header.next_sibling
                has_real_content = False
                
                # Determine what level headers to stop at based on current header
                # History section special handling - content can start with h3
                stop_tags = ['h2'] if section == 'History' and header.name == 'h2' else ['h2', 'h3']
                
                while current and not current.name in stop_tags:

                    # History section special handling - Check if there are any h3 subsections under h2
                    # Not a perfect solution, but I haven't found any page where it would cause false positives
                    # If you have found a page where this causes a problem - contact Jareel_Skaj
                    if header.name == 'h2' and current.name == 'h3' and (not current.contents[0].name == 'i'):
                        has_real_content = True
                        break
                    
                    if current.name in ['p', 'ul', 'li']:
                        text = current.get_text().strip()
                        if (text and (not current.contents[0].name == 'i')):
                            # Check if it's not just headers, empty bullets, main article links, or ammo lists
                            if (not text.startswith('Main article') and 
                                not text in ['Pros:', 'Cons:', '•'] and
                                not current.find('b')):  # Skip bullet points that start with bold text (ammo lists)
                                has_real_content = True
                                break
                    current = current.next_sibling
                if has_real_content:
                    found_sections_with_content.append(section)
                else:
                    found_sections_with_no_content.append(section)
                break
    
    return title, found_sections_with_content, found_sections_with_no_content

def process_category_page(url, processed_categories=None):
    if processed_categories is None:
        processed_categories = set()
    
    if url in processed_categories:
        return []
    
    processed_categories.add(url)
    content = get_page_content(url)
    if not content:
        return []
    
    soup = BeautifulSoup(content, 'html.parser')
       
    category_name = soup.find('h1', {'id': 'firstHeading'}).text.strip()
    print(f"Processing: {category_name}", end="\n")
    
    # Try different possible category content locations
    category_elements = soup.select('div.mw-category')
    if not category_elements:
        # Fallback to li elements only if no mw-category div is found
        category_elements = soup.select('.mw-content-ltr li')
    
    if not category_elements:
        print(f"Found 0 pages to analyze in {category_name}")
        return []
    
    links = set()  # Set to store unique links
    duplicates_count = 0
    
    # Find regular page links across all category elements
    for element in category_elements:
        for link in element.find_all('a'):
            href = link.get('href')
            if href and not href.startswith('#') and not 'action=edit' in href:
                full_url = urljoin(WIKI_BASE_URL, href)
                if full_url in links:
                    duplicates_count += 1
                else:
                    links.add(full_url)
    
    if len(links) == 0:
        print(f"\nFound 0 pages to analyze in {category_name}")
        return []
    
    if duplicates_count > 0:
        print(f"\n{duplicates_count} articles from {category_name} were already added")
    
    subcategories = {}  # Changed to dict to store subcategory URLs and names

    # Find subcategories
    subcats_div = soup.find('div', {'id': 'mw-subcategories'})
    if subcats_div:
        for link in subcats_div.find_all('a'):
            href = link.get('href')
            if href and not href.startswith('#') and not 'action=edit' in href:
                subcat_url = urljoin(WIKI_BASE_URL, href)
                subcat_name = link.text.strip()
                # Get page count for each subcategory
                subcat_content = get_page_content(subcat_url)
                if subcat_content:
                    subcat_soup = BeautifulSoup(subcat_content, 'html.parser')
                    category_elements = subcat_soup.select('div.mw-category, .mw-content-ltr li')
                    
                    subcat_links = 0
                    if category_elements:
                        subcat_links = len([l for element in category_elements 
                                          for l in element.find_all('a')
                                          if l.get('href') and not l.get('href').startswith('#') 
                                          and not 'action=edit' in l.get('href')])
                    subcategories[subcat_url] = (subcat_name, subcat_links)
    
    # If subcategories exist, show them with page counts and ask user
    if subcategories:
        subcats_info = [f"{name} ({count} pages)" for _, (name, count) in subcategories.items()]
        print("\nSubcategories found:", end=" ")
        print(", ".join(subcats_info))
        
        # Calculate total pages in all subcategories
        total_subcat_pages = sum(count for _, (_, count) in subcategories.items())
        
        if total_subcat_pages > 0:
            response = input("Would you like to include links from the subcategories? (y/n/quit): ").lower()
            if (response == 'q' or response == 'quit'):
                sys.exit(0)
            elif (response == 'y' or response == 'yes' or response == '1'):
                for subcat_url, (subcat_name, _) in subcategories.items():
                    subcat_links = process_category_page(subcat_url, processed_categories)
                    links.update(subcat_links)  # Using update() to merge sets
    
    return list(links)  # Convert back to list before returning

def process_results(page_links):
    section_counts = defaultdict(int)
    missing_sections = defaultdict(list)  # Track pages missing each section
    pages_with_no_content = []  # Track pages missing all sections
    pages_almost_no_content = []  # Track pages missing all sections except one
    pages_almost_completed = []  # Track pages missing only one section
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(check_sections, url): url for url in page_links}
        
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                title, found_sections_with_content, found_sections_with_no_content = future.result()
                if title:
                    # Track which sections are present and missing
                    required_section_count = 0
                    
                    for checked_section in SECTIONS_TO_CHECK:
                        # For all other required sections
                        required_section_count += 1
                        # check if the section is present on the list of sections with content
                        if checked_section in found_sections_with_content:
                            section_counts[checked_section] += 1
                        # check if the section is missing the content
                        elif checked_section in found_sections_with_no_content:
                            missing_sections[checked_section].append(title)

                    # additional groups of pages
                    if len(found_sections_with_no_content) > 0 and len(found_sections_with_content) == 0:
                        pages_with_no_content.append(title)
                    if len(found_sections_with_no_content) > 0 and len(found_sections_with_content) == 1:
                        pages_almost_no_content.append(title)
                    if len(found_sections_with_content) > 0 and len(found_sections_with_no_content) == 1:
                        pages_almost_completed.append(title)         
                
            except Exception as e:
                print(f"Error processing {url}: {e}")
    
    return section_counts, missing_sections, pages_with_no_content, pages_almost_completed, pages_almost_no_content

def get_links_to_analyze(url):
    """Get list of links to analyze - either from category page or single article"""
    content = get_page_content(url)
    if not content:
        return []
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Check if this is a direct article link
    if soup.find('div', class_='specs_card_main'):
        return [url]
    
    # Otherwise process as category
    return process_category_page(url)

def analyze_pages(url):
    """Analyze either a category of pages or single article page"""
    print(f"Analyzing: {url}")
    page_links = get_links_to_analyze(url)
    
    if not page_links:
        name = url.split('/')[-1].replace('_', ' ')
        print(f"Found 0 pages to analyze in {name}")
        return
    
    print(f"Found {len(page_links)} pages to analyze")
    
    section_counts, missing_sections, pages_with_no_content, pages_almost_completed, pages_almost_no_content = process_results(page_links)
    
    # Print statistics
    total_pages = len(page_links)
    print(f"\n=== Section Coverage Statistics for {total_pages} pages ===")
    for checked_section in SECTIONS_TO_CHECK:
        total_pages_in_section = (len(missing_sections[checked_section])+section_counts[checked_section])
        if (total_pages_in_section > 0):
            percentage = (section_counts[checked_section] / total_pages_in_section) * 100
            print(f"{checked_section}: {percentage:.1f}% ({section_counts[checked_section]} pages completed)")
    
    if len(pages_with_no_content) > 0:
        # Add statistics for pages with no content in any section
        no_content_percentage = (len(pages_with_no_content) / total_pages) * 100
        print(f"⚠ Pages with no content: {no_content_percentage:.1f}% ({len(pages_with_no_content)} pages missing content)")    
    if len(pages_almost_no_content) > 0:
        # Add statistics for pages with just 1 section completed
        almost_no_content_percentage = (len(pages_almost_no_content) / total_pages) * 100
        print(f"⚠ Pages with just 1 section completed: {almost_no_content_percentage:.1f}% ({len(pages_almost_no_content)} pages missing content)")    
        
    if len(pages_almost_completed) > 0:
        almost_completed_percentage = (len(pages_almost_completed) / total_pages) * 100
        print(f"⚠ Almost ready: {almost_completed_percentage:.1f}% ({len(pages_almost_completed)} pages missing just one section)")
    
    if (any(len(missing_sections[section]) > 0 for section in SECTIONS_TO_CHECK) or len(pages_almost_completed)>0 or len(pages_with_no_content)>0):
        # Print missing sections report
        print("\n=== Missing Section Content ===")
        for checked_section in SECTIONS_TO_CHECK:
            missing_count = len(missing_sections[checked_section])
            if missing_count > 0:
                print(f"\n{checked_section} (missing in {missing_count} pages):")
                for title in missing_sections[checked_section]:
                    print(f"- {title}")
        if pages_almost_completed:
            print("\nNearly complete, missing just one section:")
            for title in pages_almost_completed:
                print(f"- {title}")
        if pages_almost_no_content:
            print("\nPages with just 1 section completed:")
            for title in pages_almost_no_content:
                print(f"- {title}")
        if pages_with_no_content:
            print("\nPages with no content in any section:")
            for title in pages_with_no_content:
                print(f"- {title}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python wiki_check.articles.py <full URL to the category on War Thunder Wiki>")
        sys.exit(1)
    
    analyze_pages(sys.argv[1])