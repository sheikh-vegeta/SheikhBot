# SheikhBot

SheikhBot is a web crawler inspired by Googlebot, designed to gather information from the web and build a searchable index. It is developed by Likhon Sheikh to efficiently crawl websites and extract valuable data.

## Features

- **Multi-Platform Crawling**: Specialized crawlers for desktop, mobile, news, images, and videos
- **Configurable Crawl Depth**: Control how deep the crawler should go
- **Rate Limiting**: Respectful crawling with configurable delays
- **Data Exporting**: Export crawled data in multiple formats (JSON, CSV)
- **Search Index**: Build a searchable index from crawled content
- **GitHub Pages Integration**: View crawl results on GitHub Pages
- **Automated Workflows**: GitHub Actions for scheduled crawling

## Project Structure

```
sheikhbot/
├── .github/
│   └── workflows/       # GitHub Actions workflow files
├── src/
│   ├── crawlers/        # Specialized crawlers
│   ├── parsers/         # Content parsers
│   ├── storage/         # Data storage modules
│   └── utils/           # Utility functions
├── data/                # Crawled data output
├── docs/                # Documentation and GitHub Pages
├── tests/               # Unit and integration tests
├── config.yml           # Configuration file
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/sheikhbot.git
   cd sheikhbot
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

```python
from sheikhbot import SheikhBot

# Initialize the crawler
bot = SheikhBot(config_file="config.yml")

# Start crawling
bot.crawl("https://example.com")

# Export data
bot.export_data("output.json")
```

### Configuration

Edit the `config.yml` file to customize the crawler's behavior:

```yaml
crawl_settings:
  user_agent: "SheikhBot/1.0"
  max_depth: 3
  delay: 1.0
  respect_robots_txt: true

specialized_crawlers:
  desktop: true
  mobile: true
  news: false
  images: true
  videos: false

export_settings:
  format: "json"
  pretty_print: true
```

## GitHub Actions Integration

SheikhBot uses GitHub Actions for automated crawling and index building. The crawled data is automatically published to GitHub Pages.

To set up your own scheduled crawling:

1. Fork this repository
2. Edit the URLs in `.github/workflows/crawl.yml`
3. Configure GitHub Pages in your repository settings
4. The results will be available at `https://yourusername.github.io/sheikhbot`

## License

MIT

## Author

Likhon Sheikh 