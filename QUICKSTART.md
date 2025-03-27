# Central Search Quick Start Guide

This guide will help you get up and running with Central Search quickly to improve your website's discoverability and SEO performance.

## 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/central.git
cd central

# Install dependencies
pip install -r requirements.txt
```

## 2. Basic SEO Analysis

```bash
# Analyze a single site
python main.py crawl https://example.com

# Analyze multiple sites
python main.py crawl https://example.com https://example.org

# Analyze with greater depth
python main.py crawl --depth 5 https://example.com
```

## 3. Configuring the SEO Analyzer

The `config.yml` file contains all configuration options for Central Search. Here are the most important settings:

### Crawler Types

```yaml
specialized_crawlers:
  desktop:
    enabled: true    # Enable/disable desktop crawler
  mobile:
    enabled: true    # Enable/disable mobile crawler (important for mobile SEO)
  images:
    enabled: true    # Enable/disable image crawler (for image SEO)
```

### Crawl Settings

```yaml
crawl_settings:
  max_depth: 3       # How deep to analyze your site
  delay: 1.0         # Delay between requests in seconds
  respect_robots_txt: true  # Whether to respect robots.txt rules
  follow_redirects: true    # Whether to follow redirects
  max_pages: 1000    # Maximum pages to analyze (0 for unlimited)
```

### SEO Analysis

```yaml
seo_analysis:
  enabled: true
  factors:
    title_length:
      min: 30        # Minimum recommended title length
      max: 60        # Maximum recommended title length
      weight: 5      # How important this factor is in the overall score
    meta_description_length:
      min: 120       # Minimum recommended description length
      max: 160       # Maximum recommended description length
    # ... other SEO factors
```

## 4. Running Advanced Commands

```bash
# Export SEO analysis in different formats
python main.py export --output seo-report.json --format json

# Generate SEO report website
python main.py ghpages

# Show version information
python main.py version
```

## 5. Setting Up Automated SEO Monitoring

1. Fork this repository to your GitHub account
2. Go to your forked repository's Settings > Pages
3. Set Source to "GitHub Actions"
4. Edit `.github/workflows/crawl.yml` to customize:
   - Schedule (cron expression) for regular monitoring
   - URLs of your websites to monitor
   - Analysis depth
   - Which aspects to check (desktop, mobile, images)

Once set up, Central Search will automatically analyze your site according to your schedule, and results will be accessible via GitHub Pages.

## 6. Viewing SEO Results

After analysis, you can view the results in several ways:

- **JSON files** in the `data/` directory contain raw analysis data
- **Web Interface**: Run `python main.py ghpages` and open `docs/index.html`
- **GitHub Pages**: If you've set up GitHub Actions, visit `https://yourusername.github.io/central`

## 7. Search Engine

The search interface helps you explore your site's content and find SEO opportunities:

1. Open `docs/search.html` in your browser
2. Enter keywords to find relevant content on your site
3. Use filters to focus on specific types of content
4. Review SEO recommendations for each page

## 8. Improving Your SEO

Central Search focuses on these key areas to help improve your search visibility:

- **Technical SEO**: Site structure, mobile-friendliness, page speed
- **On-page SEO**: Title tags, meta descriptions, headings, content quality
- **Content SEO**: Word count, keyword usage, readability
- **Structured Data**: Schema markup validation
- **Image SEO**: Alt text, image optimization

## Need Help?

- Check the full documentation in the `docs/` directory
- Create an issue on GitHub if you encounter problems
- Contribute improvements via pull requests 