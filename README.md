
# SpiderBot - Modern Web Crawler

A feature-rich web crawler with modern GUI, multi-threaded architecture, and data persistence capabilities.

## Features

- **Modern Dark Theme UI** with real-time statistics
- **Multi-threaded crawling** with configurable worker threads
- **Domain restriction** to stay on target website
- **Politeness control** with adjustable delay between requests
- **CSV storage** of crawled URLs with timestamps
- **Resume capability** through persistent data storage
- **Error handling** with detailed logging
- **Responsive table** with sorting capabilities
- **Cross-platform** compatibility

## Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Steps
1. Clone the repository
   
Install dependencies:

pip install -r requirements.txt

Run the application:

python spiderbot.py

Usage
Configure Settings:

Start URL: Initial website to crawl (e.g., https://example.com)

Max Threads: Number of concurrent workers (2-16 recommended)

Delay: Seconds between requests (≥0)

Storage File: CSV filename for results

Stay on Domain: Restrict to initial domain

Controls:

▶ Start: Begin crawling process

⏹ Stop: Gracefully stop active crawl

🧹 Clear: Delete all stored data

Monitor Progress:

Real-time statistics (queued/visited URLs)

Live logging panel

Scrollable results table

Configuration
Setting	Default Value	Description
Start URL	https://example.com	Initial website to crawl
Max Threads	CPU core count	Concurrent workers (1-16)
Politeness Delay	1.0 second	Delay between requests
Storage File	crawled_urls.csv	CSV file for results storage
Stay on Domain	Enabled	Restrict crawling to initial domain
Technical Details
Architecture
Producer-Consumer Pattern with thread-safe queue

Multi-threaded Workers for parallel processing

Synchronized URL Tracking using Lock mechanisms

MVC-like Structure separating UI and logic

Libraries Used
requests for HTTP handling

BeautifulSoup4 for HTML parsing

tkinter for GUI implementation

threading for concurrent execution

Data Storage
CSV format with columns:

URL: Full crawled URL

Timestamp: ISO 8601 format

Status: HTTP status code

Limitations
No JavaScript rendering

Limited depth control

No robots.txt compliance

Basic duplicate detection

Memory-bound URL storage

Development
Extending Features
Add depth-limited crawling:

python
def crawl_page(self, url, current_depth):
    if current_depth > max_depth:
        return
    # Existing logic
Implement robots.txt handling using robotparser

Add database support for large-scale crawling

Testing
Run basic validation:

bash
python -m unittest discover tests/


Disclaimer: Use responsibly. Respect website terms of service and robots.txt directives.




T
