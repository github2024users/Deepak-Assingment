import requests
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import json

def detect_login_required(url, html_content, status_code=200):
    """
    Detects if a page REQUIRES login (highly protected sites only)
    Returns True only for major protected sites, False for sites where scraping might still work
    """
    html_lower = html_content.lower()
    url_lower = url.lower()
    
    # Check HTTP status codes that indicate login required
    if status_code in [401, 403]:
        return True
    
    # List of HIGHLY protected websites that REQUIRE login
    # Only include major protected sites - not minor detection
    highly_protected_sites = [
        'linkedin.com',
        'facebook.com',
        'instagram.com',
        'netflix.com',
        'gmail.com',
        'outlook.com',
        'amazon.com/account',
        'amazon.com/gp/your-account',
        'dropbox.com/home',
        'slack.com/messages',
        'discord.com/channels',
        'twitter.com/home',
        'x.com/home',
        'github.com/settings',
        'github.com/login'
    ]
    
    # Check if URL matches highly protected sites (strict matching)
    for site in highly_protected_sites:
        if site in url_lower:
            return True
    
    # Only check HTML for VERY obvious login pages
    critical_login_keywords = [
        'password required',
        'not logged in',
        'access denied',
        'login first',
        '401',
        '403'
    ]
    
    for keyword in critical_login_keywords:
        if keyword in html_lower:
            return True
    
    # Don't be overly strict - most sites can be scraped without login
    return False


def get_login_page_url(url):
    """
    Tries to guess the login page URL for a website
    """
    from urllib.parse import urlparse
    
    parsed = urlparse(url)
    domain = f"{parsed.scheme}://{parsed.netloc}"
    
    # Common login page patterns
    common_login_paths = [
        '/login',
        '/signin',
        '/sign-in',
        '/auth',
        '/authenticate',
        '/account/login',
        '/user/login',
        '/users/login'
    ]
    
    for path in common_login_paths:
        login_url = domain + path
        try:
            response = requests.get(login_url, timeout=5)
            if response.status_code == 200:
                return login_url
        except:
            pass
    
    return domain  # Return domain as fallback


def extract_website_summary(soup, url):
    """
    Extracts a comprehensive summary/description of the website from meta tags and content
    This helps understand what the website is about before showing scraped data
    
    Args:
        soup: BeautifulSoup object of the webpage
        url: URL of the website
    
    Returns:
        dict: Contains detailed information about the website
    """
    from urllib.parse import urlparse
    
    summary = {
        'title': 'Unknown Website',
        'description': 'No description available',
        'url': url,
        'type': 'General Website',
        'domain': '',
        'language': 'Not specified',
        'author': 'Not specified',
        'publisher': 'Not specified',
        'favicon': None,
        'image': None,
        'theme_color': None
    }
    
    # Extract domain name from URL
    parsed_url = urlparse(url)
    summary['domain'] = parsed_url.netloc
    
    # Extract website title from <title> tag
    title_tag = soup.find('title')
    if title_tag:
        summary['title'] = title_tag.get_text(strip=True)
    
    # Extract description from meta tags (most websites have this)
    # Priority order: og:description > description > twitter:description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    og_desc = soup.find('meta', property='og:description')
    twitter_desc = soup.find('meta', attrs={'name': 'twitter:description'})
    
    if og_desc and og_desc.get('content'):
        summary['description'] = og_desc.get('content')
    elif meta_desc and meta_desc.get('content'):
        summary['description'] = meta_desc.get('content')
    elif twitter_desc and twitter_desc.get('content'):
        summary['description'] = twitter_desc.get('content')
    
    # If no meta description found, try to extract from first paragraph
    if summary['description'] == 'No description available':
        # Look for main content paragraphs
        paragraphs = soup.find_all('p', limit=5)
        for p in paragraphs:
            text = p.get_text(strip=True)
            # Only use paragraphs with substantial content
            if len(text) > 50 and len(text) < 500:
                summary['description'] = text[:300] + '...' if len(text) > 300 else text
                break
    
    # Extract language from html tag or meta tag
    html_tag = soup.find('html')
    if html_tag and html_tag.get('lang'):
        summary['language'] = html_tag.get('lang')
    else:
        lang_meta = soup.find('meta', attrs={'http-equiv': 'content-language'})
        if lang_meta and lang_meta.get('content'):
            summary['language'] = lang_meta.get('content')
    
    # Extract author information
    author_meta = soup.find('meta', attrs={'name': 'author'})
    og_author = soup.find('meta', property='article:author')
    if author_meta and author_meta.get('content'):
        summary['author'] = author_meta.get('content')
    elif og_author and og_author.get('content'):
        summary['author'] = og_author.get('content')
    
    # Extract publisher information
    og_publisher = soup.find('meta', property='article:publisher')
    if og_publisher and og_publisher.get('content'):
        summary['publisher'] = og_publisher.get('content')
    
    # Extract favicon
    favicon = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')
    if favicon and favicon.get('href'):
        favicon_url = favicon.get('href')
        # Make absolute URL if relative
        if favicon_url.startswith('//'):
            summary['favicon'] = 'https:' + favicon_url
        elif favicon_url.startswith('/'):
            summary['favicon'] = f"{parsed_url.scheme}://{parsed_url.netloc}{favicon_url}"
        elif favicon_url.startswith('http'):
            summary['favicon'] = favicon_url
    
    # Extract featured image (og:image or twitter:image)
    og_image = soup.find('meta', property='og:image')
    twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
    if og_image and og_image.get('content'):
        summary['image'] = og_image.get('content')
    elif twitter_image and twitter_image.get('content'):
        summary['image'] = twitter_image.get('content')
    
    # Extract theme color (used by some modern websites)
    theme_color = soup.find('meta', attrs={'name': 'theme-color'})
    if theme_color and theme_color.get('content'):
        summary['theme_color'] = theme_color.get('content')
    
    # Determine website type based on URL and content
    url_lower = url.lower()
    title_lower = summary['title'].lower()
    desc_lower = summary['description'].lower()
    
    # Categorize the website type
    if 'naukri.com' in url_lower or 'indeed.com' in url_lower or 'linkedin.com/jobs' in url_lower:
        summary['type'] = 'Job Portal'
    elif 'instagram.com' in url_lower or 'facebook.com' in url_lower or 'twitter.com' in url_lower or 'x.com' in url_lower:
        summary['type'] = 'Social Media Platform'
    elif 'news' in url_lower or 'news' in title_lower or 'bbc.com' in url_lower or 'cnn.com' in url_lower:
        summary['type'] = 'News Website'
    elif 'blog' in url_lower or 'medium.com' in url_lower or 'wordpress.com' in url_lower:
        summary['type'] = 'Blog/Article Platform'
    elif 'github.com' in url_lower or 'gitlab.com' in url_lower:
        summary['type'] = 'Code Repository'
    elif 'stackoverflow.com' in url_lower or 'stackexchange.com' in url_lower:
        summary['type'] = 'Q&A Platform'
    elif 'youtube.com' in url_lower or 'vimeo.com' in url_lower or 'video' in desc_lower:
        summary['type'] = 'Video Platform'
    elif any(word in desc_lower for word in ['shop', 'buy', 'product', 'store', 'cart', 'ecommerce']):
        summary['type'] = 'E-commerce'
    elif any(word in desc_lower for word in ['learn', 'course', 'tutorial', 'education', 'university', 'school']):
        summary['type'] = 'Educational Platform'
    elif any(word in desc_lower for word in ['tech', 'technology', 'developer', 'programming', 'code']):
        summary['type'] = 'Technology Website'
    elif 'wikipedia.org' in url_lower:
        summary['type'] = 'Encyclopedia'
    
    # Extract additional metadata
    # Get site name from Open Graph tags
    og_site_name = soup.find('meta', property='og:site_name')
    if og_site_name and og_site_name.get('content'):
        summary['site_name'] = og_site_name.get('content')
    else:
        # Use domain as site name if not found
        summary['site_name'] = summary['domain']
    
    # Get keywords if available
    meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
    if meta_keywords and meta_keywords.get('content'):
        summary['keywords'] = meta_keywords.get('content')
    
    # Extract copyright information if available
    copyright_meta = soup.find('meta', attrs={'name': 'copyright'})
    if copyright_meta and copyright_meta.get('content'):
        summary['copyright'] = copyright_meta.get('content')
    
    # Extract application name (for web apps)
    app_name = soup.find('meta', attrs={'name': 'application-name'})
    og_app_name = soup.find('meta', property='og:site_name')
    if app_name and app_name.get('content'):
        summary['app_name'] = app_name.get('content')
    
    return summary


def extract_text_from_url(url):
    """
    Generic function to extract text content from any URL
    Returns list of scraped items along with website summary
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        print(f"Successfully fetched {url}")
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return [], None  # Return empty list and None for summary
    
    soup = BeautifulSoup(r.text, "html.parser")
    
    # Extract website summary FIRST before scraping content
    website_summary = extract_website_summary(soup, url)
    print(f"Website Summary: {website_summary['title']} - {website_summary['type']}")
    
    results = []
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Extract page title
    page_title = soup.find("title")
    page_title_text = page_title.get_text(strip=True) if page_title else "Unknown"
    
    # Strategy 1: Look for article tags
    articles = soup.find_all("article")
    if articles:
        for article in articles[:10]:
            title_elem = article.find(["h1", "h2", "h3"])
            title = title_elem.get_text(strip=True) if title_elem else "No title"
            
            link_elem = article.find("a")
            link = link_elem.get("href", "#") if link_elem else "#"
            
            text = article.get_text(strip=True)
            snippet = text[:100] + "..." if len(text) > 100 else text
            
            if title and snippet:
                results.append({
                    "title": title,
                    "company": page_title_text,
                    "snippet": snippet,
                    "link": link if link.startswith("http") else url + link if link.startswith("/") else url
                })
    
    # Strategy 2: Look for divs with class containing "post", "article", "item"
    if not results:
        content_divs = soup.find_all("div", class_=re.compile(r"post|article|item|content|card", re.I))
        for div in content_divs[:10]:
            title_elem = div.find(["h1", "h2", "h3", "h4"])
            if title_elem:
                title = title_elem.get_text(strip=True)
                
                link_elem = div.find("a")
                link = link_elem.get("href", "#") if link_elem else "#"
                
                text = div.get_text(strip=True)
                snippet = text[:100] + "..." if len(text) > 100 else text
                
                if title and snippet:
                    results.append({
                        "title": title,
                        "company": page_title_text,
                        "snippet": snippet,
                        "link": link if link.startswith("http") else url + link if link.startswith("/") else url
                    })
    
    # Strategy 3: Look for all h2/h3 tags
    if not results:
        headings = soup.find_all(["h2", "h3"])
        for heading in headings[:15]:
            title = heading.get_text(strip=True)
            
            para = heading.find_next("p")
            snippet = para.get_text(strip=True)[:100] + "..." if para else "No description"
            
            link_elem = heading.find_parent().find("a") if heading.find_parent() else None
            link = link_elem.get("href", "#") if link_elem else "#"
            
            if title:
                results.append({
                    "title": title,
                    "company": page_title_text,
                    "snippet": snippet,
                    "link": link if link.startswith("http") else url + link if link.startswith("/") else url
                })
    
    # Strategy 4: Last resort - get all links
    if not results:
        links = soup.find_all("a", limit=20)
        for link_elem in links:
            title = link_elem.get_text(strip=True)
            link = link_elem.get("href", "#")
            
            if title and len(title) > 3:
                results.append({
                    "title": title,
                    "company": page_title_text,
                    "snippet": title[:100],
                    "link": link if link.startswith("http") else url + link if link.startswith("/") else url
                })
    
    print(f"Extracted {len(results)} items from {url}")
    return results, website_summary  # Return both items and summary


def scrape_naukri(url):
    """
    Scrapes Naukri.com using Selenium
    Returns list of jobs and website summary (automatically extracted)
    """
    print("Scraping Naukri.com with Selenium...")
    
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    results = []
    website_summary = None  # Will be extracted from the page
    
    try:
        print(f"Opening {url}...")
        driver.get(url)
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "jobTuple"))
        )
        
        print("Page loaded, extracting jobs...")
        time.sleep(2)
        
        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Extract website summary automatically from the loaded page
        website_summary = extract_website_summary(soup, url)
        print(f"Extracted website summary: {website_summary['title']}")
        
        # Now extract job listings
        jobs = soup.select("div.jobTuple") or soup.select("article.jobCard")
        print(f"Found {len(jobs)} job listings")
        
        for job in jobs[:20]:
            title_elem = job.select_one("h2.jobTitle, a.jobTitle, span.jobTitle")
            title = title_elem.get_text(strip=True) if title_elem else None
            
            company_elem = job.select_one("span.companyName, a.companyName")
            company = company_elem.get_text(strip=True) if company_elem else "Naukri.com"
            
            exp_elem = job.select_one("span.experience, span.exp")
            exp = exp_elem.get_text(strip=True) if exp_elem else "N/A"
            
            salary_elem = job.select_one("span.salary, span.salaryText")
            salary = salary_elem.get_text(strip=True) if salary_elem else "Not disclosed"
            
            link_elem = job.select_one("a.jobTitle, h2.jobTitle a")
            link = link_elem.get("href", "#") if link_elem else "#"
            if not link.startswith("http"):
                link = "https://www.naukri.com" + link if link.startswith("/") else "https://www.naukri.com/" + link
            
            if title:
                results.append({
                    "title": title,
                    "company": company,
                    "snippet": f"Experience: {exp} | Salary: {salary}",
                    "link": link
                })
        
        print(f"Successfully scraped {len(results)} jobs from Naukri.com")
        return results, website_summary  # Return both results and auto-extracted summary
        
    except Exception as e:
        print(f"Error scraping Naukri.com: {e}")
        # If error occurs, create a basic summary
        if not website_summary:
            website_summary = {
                'title': 'Unable to extract title',
                'description': 'Unable to extract description due to scraping error',
                'url': url,
                'type': 'Unknown'
            }
        return [], website_summary
    
    finally:
        driver.quit()


def categorize_story(title):
    """
    Categorizes a story based on keywords in the title
    Helps organize scraped content into relevant categories
    
    Args:
        title: Title of the article/content
    
    Returns:
        str: Category name (AI, Tech, Jobs, etc.)
    """
    title_lower = title.lower()
    
    # AI and Machine Learning related content
    ai_keywords = ['ai', 'machine learning', 'neural', 'gpt', 'llm', 'transformer', 'deep learning', 'nlp', 'chatgpt', 'claude', 'model', 'algorithm']
    if any(keyword in title_lower for keyword in ai_keywords):
        return 'AI'
    
    # Startup and business news
    startup_keywords = ['startup', 'founder', 'funding', 'raised', 'series', 'vc', 'investment', 'exit', 'acquisition', 'pivot', '$', 'million', 'billion', 'ipo']
    if any(keyword in title_lower for keyword in startup_keywords):
        return 'Startups'
    
    # Educational and tutorial content
    tutorial_keywords = ['tutorial', 'guide', 'how to', 'learn', 'beginner', 'tips', 'best practices', 'course', 'introduction', 'getting started']
    if any(keyword in title_lower for keyword in tutorial_keywords):
        return 'Tutorials'
    
    # Open source projects and tools
    opensource_keywords = ['open source', 'github', 'repo', 'library', 'framework', 'package', 'tool', 'project', 'release', 'version']
    if any(keyword in title_lower for keyword in opensource_keywords):
        return 'Open Source'
    
    # Programming languages
    lang_keywords = ['rust', 'python', 'javascript', 'go', 'java', 'c++', 'typescript', 'ruby', 'php', 'kotlin', 'swift', 'golang']
    if any(keyword in title_lower for keyword in lang_keywords):
        return 'Programming'
    
    # Web development
    web_keywords = ['react', 'vue', 'angular', 'html', 'css', 'tailwind', 'nextjs', 'svelte', 'web', 'frontend', 'browser']
    if any(keyword in title_lower for keyword in web_keywords):
        return 'Web'
    
    # Security related content
    security_keywords = ['security', 'hack', 'breach', 'vulnerability', 'exploit', 'bug', 'ssl', 'crypto', 'password', 'privacy']
    if any(keyword in title_lower for keyword in security_keywords):
        return 'Security'
    
    # Job listings and career content
    job_keywords = ['job', 'hiring', 'recruiter', 'developer', 'engineer', 'position', 'vacancy', 'role', 'opening', 'apply', 'fresher']
    if any(keyword in title_lower for keyword in job_keywords):
        return 'Jobs'
    
    # Default category for everything else
    return 'Other'


def search_web(query):
    """
    Searches the web for a given query and returns categorized results
    This function performs web search when user enters a question/sentence instead of URL
    
    Args:
        query: Search query string (e.g., "latest AI news", "python tutorials")
    
    Returns:
        dict: Contains search_summary and categorized search results
    """
    print(f"Performing web search for: {query}")
    
    # Use requests to search (you can integrate with Google Custom Search API, Bing API, or DuckDuckGo)
    # For now, we'll search using DuckDuckGo HTML (no API key needed)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        # DuckDuckGo HTML search (simple, no API key required)
        search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        
        # Parse DuckDuckGo search results
        search_results = soup.find_all('div', class_='result')
        
        for result in search_results[:15]:  # Get top 15 results
            # Extract title
            title_elem = result.find('a', class_='result__a')
            title = title_elem.get_text(strip=True) if title_elem else "No title"
            
            # Extract link
            link = title_elem.get('href', '#') if title_elem else '#'
            
            # Extract snippet/description
            snippet_elem = result.find('a', class_='result__snippet')
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else "No description available"
            
            # Extract source domain
            url_elem = result.find('span', class_='result__url')
            source = url_elem.get_text(strip=True) if url_elem else "Unknown source"
            
            if title and title != "No title":
                results.append({
                    "title": title,
                    "company": source,
                    "snippet": snippet,
                    "link": link
                })
        
        print(f"Found {len(results)} search results")
        
        # If no results found, try alternative: search for the query as keywords on a news site
        if len(results) == 0:
            print("No results from DuckDuckGo, trying alternative search...")
            # You could add fallback search methods here
            results = [{
                "title": f"No results found for '{query}'",
                "company": "Search Engine",
                "snippet": "Try rephrasing your search query or use more specific keywords.",
                "link": "#"
            }]
        
        # Create search summary
        search_summary = {
            'title': f"Search Results: {query}",
            'description': f"Found {len(results)} web results for your search query. Results are automatically categorized based on content.",
            'url': f"search:{query}",
            'type': 'Web Search Results',
            'domain': 'Web Search',
            'language': 'en',
            'author': 'Multiple Sources',
            'publisher': 'Search Engine',
            'site_name': 'AI-Powered Search'
        }
        
        # Categorize the search results
        categorized_data = {
            'Tech': [],
            'AI': [],
            'Startups': [],
            'Tutorials': [],
            'Open Source': [],
            'Programming': [],
            'Web': [],
            'Security': [],
            'Jobs': [],
            'Other': []
        }
        
        # Categorize each search result
        for item in results:
            category = categorize_story(item['title'])
            categorized_data[category].append(item)
        
        print(f"Categorized {len(results)} search results")
        
        # Return data with search_summary as the first key
        return {
            'search_summary': search_summary,
            **categorized_data
        }
        
    except Exception as e:
        print(f"Error during web search: {e}")
        # Return error info
        return {
            'search_summary': {
                'title': f"Search Error",
                'description': f"Unable to complete search for '{query}'. Error: {str(e)}",
                'url': f"search:{query}",
                'type': 'Error',
                'domain': 'Search',
                'language': 'en'
            },
            'Other': [{
                'title': 'Search failed',
                'company': 'Error',
                'snippet': str(e),
                'link': '#'
            }]
        }


def scrape_url(url):
    """
    Main scraping function that scrapes any given URL and categorizes the content
    Now includes website summary as the first piece of information
    
    Args:
        url: URL to scrape
    
    Returns:
        dict: Contains website_summary and categorized data
    """
    
    # Ensure URL has proper protocol
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Check if it's Naukri.com and use specialized scraper
    if 'naukri.com' in url.lower():
        items, website_summary = scrape_naukri(url)
    else:
        # Use generic scraper for other websites
        items, website_summary = extract_text_from_url(url)
    
    # Dictionary to store categorized data
    categorized_data = {
        'Tech': [],
        'AI': [],
        'Startups': [],
        'Tutorials': [],
        'Open Source': [],
        'Programming': [],
        'Web': [],
        'Security': [],
        'Jobs': [],
        'Other': []
    }
    
    # Categorize each scraped item into appropriate category
    for item in items:
        category = categorize_story(item['title'])
        categorized_data[category].append(item)
    
    print(f"Categorized {len(items)} items")
    
    # Return data with website summary as the first key
    # This ensures the frontend receives website info before the scraped content
    return {
        'website_summary': website_summary,  # NEW: Website information comes first
        **categorized_data  # Spread operator to include all categories
    }