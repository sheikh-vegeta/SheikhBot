# Central Search

A powerful web crawler and SEO analysis tool designed to help make your website discoverable to Search. Central (formerly Sheikh Webmasters) provides advanced crawling capabilities, content extraction, SEO insights, and a beautiful interface for improving your site's search presence.

## Features

- **SEO Analysis**: Get detailed insights on title tags, meta descriptions, headings, content quality, and more
- **Multi-Platform Testing**: Crawl your website from desktop, mobile, and image search perspectives
- **JavaScript Rendering**: Test how search engines see your JavaScript-heavy pages
- **Robots.txt Compliance**: Verify your robots.txt is correctly configured
- **HTTP Caching**: Check your site's ETag and If-Modified-Since headers for efficient crawling
- **Structured Data Analysis**: Validate schema markup and structured data
- **Content Optimization**: Get recommendations for improving content quality and relevance
- **Full-Text Search**: Index and search your site content to find optimization opportunities
- **IndexNow Integration**: Instantly notify search engines about new or updated content
- **Beautiful Reports**: Modern interface for browsing findings and recommendations
- **Automated Monitoring**: Schedule regular crawls with GitHub Actions

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/central.git
   cd central
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the crawler by editing `config.yml`

## Usage

### Basic SEO Analysis

To analyze a website for SEO opportunities, run:

```bash
python main.py crawl https://example.com
```

The results will be saved to the configured output directory (default: `data/`).

### GitHub Actions Workflow

The included GitHub Actions workflow allows you to automatically run Central Search on a schedule or manually:

1. The workflow is configured in `.github/workflows/crawl.yml`
2. It will run daily at midnight UTC by default
3. You can manually trigger a run from the Actions tab in your GitHub repository
4. When manually triggering, you can specify:
   - URLs to crawl (comma-separated)
   - Crawl depth
   - Which crawlers to use (desktop, mobile, image)

#### Troubleshooting GitHub Actions

If you encounter indentation errors in your GitHub Actions workflow:

1. We've restructured the workflow to use dedicated script files located in `scripts/github_actions/`:
   - `modify_config.py`: Creates a modified configuration based on input parameters
   - `run_crawler.py`: Runs the Central crawler with a specified URL and configuration
   - `build_index.py`: Builds an index of crawled results for GitHub Pages
   - `index_template.html`: Template for the GitHub Pages index

2. This approach avoids YAML indentation issues that often occur with multi-line Python scripts embedded in workflows.

3. If you need to modify the workflow scripts:
   - Edit the Python files directly in the `scripts/github_actions/` directory
   - Make sure to commit and push these changes to your repository

4. On Windows, make sure the script files are recognized as executable in git:
   ```bash
   git update-index --chmod=+x scripts/github_actions/*.py
   ```

### IndexNow Integration

Central Search includes full support for the [IndexNow](https://www.indexnow.org/) protocol, which allows websites to instantly inform search engines about content changes. This significantly improves discovery time from days or weeks to just seconds.

#### What is IndexNow?

IndexNow is a simple ping that instantly notifies search engines when URLs are added, updated, or deleted. It's supported by Microsoft Bing, Yandex, Naver, Seznam.cz, and Yep - with more search engines expected to join.

#### Setting Up IndexNow

1. Configure IndexNow in your `config.yml`:
   ```yaml
   indexnow:
     enabled: true
     api_key: "YOUR_INDEXNOW_API_KEY"  # Generate a key at indexnow.org
     key_location: ""  # Optional URL where your key file is hosted
     search_engines:
       - "default"  # Use the unified API (all participating engines)
     auto_submit: true  # Automatically submit URLs after crawling
     bulk_submit: true  # Submit URLs in bulk where possible
     generate_key_file: true  # Generate key file in export directory
   ```

2. Generate an IndexNow key file (required for verification):
   ```bash
   python main.py indexnow genkey
   ```
   This creates a key file (e.g., `cb7a0c39fe74468ba119283e95c08b00.txt`) that you need to host at the root of your website.

3. Verify your key file is accessible:
   ```
   https://www.example.com/cb7a0c39fe74468ba119283e95c08b00.txt
   ```
   The file should contain only your API key.

#### Submitting URLs with IndexNow

- **During crawling**: URLs are automatically submitted if `auto_submit` is enabled in your config:
  ```bash
  python main.py crawl https://example.com
  ```

- **Submit URLs manually**:
  ```bash
  # Submit a single URL
  python main.py indexnow submit https://example.com/new-page

  # Submit multiple URLs
  python main.py indexnow submit https://example.com/page1 https://example.com/page2

  # Submit URLs in bulk (more efficient, all URLs must be from same domain)
  python main.py indexnow submit --bulk https://example.com/page1 https://example.com/page2

  # Submit to a specific search engine
  python main.py indexnow submit --search-engine bing https://example.com/page
  ```

#### Benefits of IndexNow

- **Faster Indexing**: Get your content discovered and indexed in seconds instead of waiting for crawlers
- **Reduced Crawl Load**: Search engines can focus on crawling changes, reducing unnecessary hits to your server
- **Better Resource Utilization**: More efficient for both website owners and search engines
- **Broader Search Coverage**: Get discovered across multiple search engines with a single protocol

### Configuration Options

Edit `config.yml` to customize crawling behavior:

- Set crawl depth, delay, and timeouts
- Configure specialized crawlers (desktop, mobile, image)
- Define content extraction selectors
- Adjust SEO analysis parameters
- Configure storage and export settings

### Advanced Commands

View all available commands:

```bash
python main.py --help
```

Export analysis data:

```bash
python main.py export --output seo-report.json --format json
```

Generate SEO reports for viewing:

```bash
python main.py ghpages --directory docs
```

### Automated Monitoring with GitHub Actions

For regular SEO monitoring:

1. Fork this repository
2. Enable GitHub Actions
3. Configure the workflow in `.github/workflows/crawl.yml`
4. Push changes to your repository
5. Access your SEO reports on GitHub Pages

## Web Interface

After analyzing your site, you can browse the results using the built-in web interface:

1. Generate the report site:
   ```bash
   python main.py ghpages
   ```

2. Open `docs/index.html` in your browser or deploy to GitHub Pages

Features:
- SEO scores and recommendations
- Content analysis with improvement suggestions
- Mobile-friendliness metrics
- Structured data validation
- Dark mode support
- Mobile-friendly interface

## SEO Best Practices

Central Search helps you implement these critical SEO best practices:

- Optimize title tags and meta descriptions
- Create a logical heading structure (H1, H2, H3)
- Ensure content meets quality thresholds
- Optimize for mobile devices
- Implement schema markup correctly
- Ensure proper internal linking
- Optimize images with alt text
- Improve page load speed

## Requirements

- Python 3.8+
- Chrome/Chromium (for JavaScript rendering)
- Dependencies listed in requirements.txt

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 