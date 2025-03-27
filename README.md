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

**Important Note:** If you're encountering indentation errors when running the workflow, make sure all Python code blocks in the YAML file are properly indented. Each line of Python code in the workflow file should be indented with the same number of spaces.

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