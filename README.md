# Backend - Web Scraper Portal

Flask-based backend API for the Web Scraper Portal with web scraping capabilities.

## 📋 Requirements

- **Python** 3.8+
- **pip** (Python package manager)
- **Chrome/Chromium** (for Selenium, optional)

## 🚀 Installation

### Step 1: Create Virtual Environment

```bash or terminal
# Navigate to backend folder
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
# Install from requirements.txt
pip install -r requirements.txt
```

### Step 3: Run Backend

```bash
# Start Flask server
python app.py
```

Backend will run at: `http://localhost:5000`

## 📁 Project Structure

```
backend/
├── app.py                  # Flask app & API routes
├── scraper.py              # Web scraping logic
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 📦 Dependencies

### requirements.txt
```
Flask==3.0.0
flask-cors==4.0.0
requests==2.31.0
beautifulsoup4==4.12.2
google-auth==2.27.0
selenium==4.0.0
webdriver-manager==3.8.0
```

### Installation
```bash
pip install -r requirements.txt
```

## 🔧 Configuration

### Environment Variables (Optional)

Create `.env` file:
```
FLASK_ENV=development
FLASK_DEBUG=True
```

### Google OAuth Setup

Update `GOOGLE_CLIENT_ID` in `app.py`:
```python
GOOGLE_CLIENT_ID = "your_google_client_id_here"
```
NOTE: your google client id should within quotation

## 📡 API Endpoints

### GET `/scrape?url=website_url`

Scrapes a website and returns categorized data.

**Query Parameters:**
- `url` (required) - Website URL to scrape

**Example Request:**
```
GET http://localhost:5000/scrape?url=news.ycombinator.com
```

**Example Response:**
```json
{
  "AI": [
    {
      "title": "New AI Model Released",
      "company": "TechNews",
      "snippet": "A new AI model...",
      "link": "https://example.com"
    }
  ],
  "Tech": [...],
  "Startups": [...]
}
```

**Response Structure:**
```json
{
  "Category_Name": [
    {
      "title": "String - Article title",
      "company": "String - Source name",
      "snippet": "String - Content preview (100 chars)",
      "link": "String - Full URL to source",
      "score": "String - Optional: Points/likes",
      "comments": "String - Optional: Comment count"
    }
  ]
}
```

**Status Codes:**
- `200` - Success
- `400` - Bad request (missing URL)
- `500` - Server error

### POST `/verify-token`

Verifies Google OAuth token.

**Request Body:**
```json
{
  "token": "google_oauth_token_here"
}
```

**Response:**
```json
{
  "success": true,
  "user": {
    "name": "User Name",
    "email": "user@example.com",
    "picture": "https://..."
  }
}
```

## 🔍 Web Scraping Logic

### File: `scraper.py`

#### Main Function: `scrape_url(url)`

```python
def scrape_url(url):
    """
    Scrapes any given URL and categorizes the content
    """
    # Validates URL format
    # Detects site type (static or JS-heavy)
    # Calls appropriate scraper
    # Categorizes results
    # Returns organized data
```

#### Scraping Methods

##### 1. Static HTML Scraping (`extract_text_from_url`)
Uses BeautifulSoup to parse HTML from websites like:
- Hacker News
- GitHub
- Wikipedia
- Blogs

**Process:**
```python
1. Make HTTP request with User-Agent header
2. Parse HTML with BeautifulSoup
3. Try 4 extraction strategies:
   - Look for <article> tags
   - Search for divs with content classes
   - Find heading tags with content
   - Extract all links as fallback
4. Return extracted items
```

##### 2. JavaScript-Heavy Sites (`scrape_naukri`)
Uses Selenium for sites like:
- Naukri.com
- Medium.com
- Platforms with dynamic content

**Process:**
```python
1. Launch Chrome browser with Selenium
2. Navigate to URL
3. Wait for content to load (15 seconds max)
4. Parse rendered HTML with BeautifulSoup
5. Extract job listings or content
6. Close browser
7. Return extracted items
```

#### Auto-Categorization (`categorize_story`)

Automatically sorts data into 9 categories based on keywords:

```python
def categorize_story(title):
    """
    Analyzes title and assigns category based on keywords
    """
    # Check for AI keywords → 'AI'
    # Check for startup keywords → 'Startups'
    # Check for tutorial keywords → 'Tutorials'
    # etc.
    # Default: 'Other'
```

**Category Keywords:**

| Category | Keywords |
|----------|----------|
| **AI** | ai, machine learning, neural, gpt, llm, transformer, deep learning |
| **Startups** | startup, founder, funding, raised, series, vc, investment, acquisition |
| **Tutorials** | tutorial, guide, how to, learn, beginner, tips, best practices |
| **Open Source** | open source, github, repo, library, framework, package, tool |
| **Programming** | rust, python, javascript, go, java, c++, typescript, ruby |
| **Web** | react, vue, angular, html, css, tailwind, nextjs, web, frontend |
| **Security** | security, hack, breach, vulnerability, exploit, bug, ssl, crypto |
| **Jobs** | job, hiring, recruiter, developer, engineer, position, vacancy, opening |
| **Tech** | (Default category for technology news) |

## 🔐 Security Features

### 1. User Agent Spoofing
```python
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
```

Prevents websites from blocking automated requests.

### 2. Timeout Protection
```python
requests.get(url, timeout=10)
```

Prevents hanging on slow/unresponsive servers.

### 3. CORS Enabled
```python
CORS(app)
```

Allows requests from frontend on different port.

### 4. Error Handling
```python
try:
    # Scraping logic
except requests.RequestException as e:
    # Graceful error handling
    print(f"Error: {e}")
    return []
```

## 🧪 Testing the API

### Using cURL

```bash
# Test scraping endpoint
curl "http://localhost:5000/scrape?url=news.ycombinator.com"

# Test with encoded URL
curl "http://localhost:5000/scrape?url=https%3A%2F%2Fnews.ycombinator.com"
```

### Using Python

```python
import requests

url = "http://localhost:5000/scrape"
params = {"url": "news.ycombinator.com"}

response = requests.get(url, params=params)
data = response.json()

print(data)
```

### Using JavaScript/Fetch

```javascript
const url = 'http://localhost:5000/scrape?url=' + 
            encodeURIComponent('news.ycombinator.com');

fetch(url)
  .then(res => res.json())
  .then(data => console.log(data));
```

## 🚀 Running the Server

### Development Mode

```bash
# With debug enabled
python app.py
```

Server logs:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### Production Mode

```bash
# Disable debug mode (not recommended for production)
# Use production WSGI server instead:
pip install gunicorn
gunicorn app:app
```

## 🐛 Troubleshooting

### "Port 5000 already in use"
```bash
# Kill process on port 5000
# On Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# On macOS/Linux:
lsof -i :5000
kill -9 <PID>
```

### "No module named 'flask'"
```bash
# Activate virtual environment first
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Then install dependencies
pip install -r requirements.txt
```

### "Selenium ChromeDriver error"
```bash
# webdriver-manager will auto-download ChromeDriver
# If issue persists, manually install Chrome/Chromium
# Or clear cache:
rm -rf ~/.wdm/  # macOS/Linux
rmdir %USERPROFILE%\.wdm /s  # Windows
```

### "Website returns 403 Forbidden"
- Website may have advanced bot detection
- Try different User-Agent
- Add delay between requests
- Check if scraping is allowed in robots.txt

### "Timeout exceeded"
- Increase timeout in code:
  ```python
  requests.get(url, timeout=30)  # 30 seconds
  ```
- Website may be overloaded
- Check your internet connection

## 📊 Code Examples

### Basic Scraping

```python
from scraper import scrape_url

# Scrape and categorize
data = scrape_url("news.ycombinator.com")

# Data structure
for category, items in data.items():
    print(f"\n{category}:")
    for item in items:
        print(f"  - {item['title']}")
        print(f"    Source: {item['company']}")
```

### Flask API Route

```python
@app.route("/scrape", methods=["GET"])
def scrape():
    url = request.args.get('url')
    
    if not url:
        return jsonify({"error": "URL required"}), 400
    
    result = scrape_url(url)
    return jsonify(result)
```

## 🔄 How Scraping Works

```
1. Request arrives: GET /scrape?url=example.com
   ↓
2. URL validation: Add https:// if needed
   ↓
3. Site detection: Is it naukri.com? (needs Selenium)
   ↓
4. Scraping:
   ├─ Static: BeautifulSoup + Requests
   └─ Dynamic: Selenium + BeautifulSoup
   ↓
5. Extraction: Try 4 strategies to get content
   ↓
6. Categorization: Analyze keywords and sort
   ↓
7. Return: JSON response with categorized data
```

## 🚢 Deployment

### Deploy to Heroku

```bash or terminal
# Create Heroku app
heroku create your-app-name

# Add Procfile
echo "web: gunicorn app:app" > Procfile

# Deploy
git push heroku main
```

### Deploy to AWS

```bash
# Create EC2 instance
# Install Python and dependencies
# Run with Gunicorn + Nginx
```

### Environment Variables for Production

```
FLASK_ENV=production
GOOGLE_CLIENT_ID=production_client_id
```

## 📝 Code Comments

All functions have docstrings:

```python
def scrape_url(url):
    """
    Scrapes any given URL and categorizes the content
    
    Args:
        url (str): Website URL to scrape
    
    Returns:
        dict: Categorized data {category: [items]}
    """
```

## 🤝 Contributing

To extend scraping:

1. Add keywords to `categorize_story()`
2. Add scraping strategy to `extract_text_from_url()`
3. Add new selector patterns to fallback strategies
4. Test with different websites

## 📞 Support

For issues:
1. Check console logs
2. See Troubleshooting section
3. Check main README.md
4. Verify configuration

---

**Version:** 1.0.0
**Status:** ✅ Production Ready
**Last Updated:** December 2025