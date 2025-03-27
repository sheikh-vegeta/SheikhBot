# Enhancing SheikhBot with User Agent Selection Feature

## Solution Overview

The goal is to enable SheikhBot to use different user agent strings, which are identifiers sent in HTTP requests to inform websites about the client making the request (e.g., a browser or a crawler). By allowing SheikhBot to mimic crawlers like Googlebot or Bingbot, you can test how websites respond to these bots or adapt crawling behavior as needed.

Here's how we'll approach it:

1. **Define User Agents**: Create a list of user agent strings for 21 specified crawlers.
2. **Selection Mechanism**: Implement a way for users to choose a user agent via a command-line argument.
3. **HTTP Integration**: Ensure the selected user agent is applied to all HTTP requests.
4. **Error Handling**: Manage invalid selections with clear error messages.
5. **Default Behavior**: Set a fallback user agent if none is specified.
6. **Documentation**: Update SheikhBot's documentation to explain the feature.
7. **Testing**: Verify the feature works as expected.

## User Agent List

The following user agents are provided for the 21 crawlers specified in the requirements:

- **Googlebot**: `Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)`
- **Bingbot**: `Mozilla/5.0 (compatible; bingbot/2.0; +https://www.bing.com/bingbot.htm)`
- **Yandex Bot**: `Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)`
- **Apple Bot**: `Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebkit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1 (Applebot/0.1)`
- **DuckDuck Bot**: `DuckDuckBot/1.0; (+http://duckduckgo.com/duckduckbot.html)`
- **Baidu Spider**: `Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)`
- **Sogou Spider**: `sogou Pic Spider/3.0( http://www.sogou.com/docs/help/webmasters.htm#07)`
- **Facebook External Hit**: `facebookexternalhit/1.0 (+http://www.facebook.com/externalhit_uatext.php)`
- **Exabot**: `Mozilla/5.0 (compatible; Exabot/3.0; +http://www.exabot.com/go/robot)`
- **Swiftbot**: `Mozilla/5.0 (compatible; Swiftbot/1.0; UID/54e1c2ebd3b687d3c8000018; +http://swiftype.com/swiftbot)`
- **Slurp Bot**: `Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)`
- **CCBot**: `CCBot/2.0 (https://commoncrawl.org/faq/)`
- **Google-InspectionTool**: `Mozilla/5.0 (compatible; Google-InspectionTool/1.0)`
- **Ahrefs Bot**: `Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)`
- **Semrush Bot**: `Mozilla/5.0 (compatible; SemrushBot/7~bl; +http://www.semrush.com/bot.html)`
- **Moz's Rogerbot**: `rogerbot`
- **Screaming Frog**: `Screaming Frog SE Spider`
- **Lumar**: `Lumar Crawler`
- **Majestic**: `MJ12bot`
- **Cognitive SEO**: `JamesBOT`
- **Oncrawl**: `Oncrawl`

## Implementation Prompt

### Requirements

1. **User Agent List**: Incorporate the 21 specified crawlers and their user agent strings.
2. **Selection Mechanism**: Add a command-line argument `--user-agent` to let users specify the crawler to mimic.
3. **HTTP Integration**: Ensure the selected user agent is set in the 'User-Agent' header for all HTTP requests.
4. **Error Handling**: If an invalid user agent is selected, display an error message listing available crawlers and exit.
5. **Default User Agent**: Use `SheikhBot/1.0 (+https://github.com/sheikh-vegeta/SheikhBot)` as the default if no user agent is specified.
6. **Documentation**: Update SheikhBot's README or help section with usage instructions.

## Example Code Structure

```python
import argparse
import requests

# User agent dictionary
USER_AGENTS = {
    "Googlebot": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    # ... (add all other user agents from the list above)
    "Oncrawl": "Oncrawl"
}
DEFAULT_USER_AGENT = "SheikhBot/1.0 (+https://github.com/sheikh-vegeta/SheikhBot)"

def get_user_agent(selected_crawler):
    if selected_crawler in USER_AGENTS:
        return USER_AGENTS[selected_crawler]
    else:
        print(f"Error: Invalid crawler. Available options: {', '.join(USER_AGENTS.keys())}")
        exit(1)

def main():
    parser = argparse.ArgumentParser(description="SheikhBot Web Crawler")
    parser.add_argument("--user-agent", type=str, help="Select user agent (e.g., 'Googlebot')")
    args = parser.parse_args()

    user_agent = get_user_agent(args.user_agent) if args.user_agent else DEFAULT_USER_AGENT
    headers = {"User-Agent": user_agent}

    # Example request (integrate with existing SheikhBot crawling logic)
    response = requests.get("https://example.com", headers=headers)
    print(f"Using User-Agent: {user_agent}")
    print(response.text)

if __name__ == "__main__":
    main()
```

## Testing

- **Valid Selection**: 
  - `python sheikhbot.py --user-agent "Googlebot"`
  - `python sheikhbot.py --user-agent "Bingbot"`
  - `python sheikhbot.py --user-agent "DuckDuck Bot"`
- **Invalid Selection**: 
  - `python sheikhbot.py --user-agent "InvalidBot"`
- **Default Case**: 
  - `python sheikhbot.py` (no argument)

## Documentation Update

### User Agent Selection

SheikhBot can mimic various web crawlers using the `--user-agent` flag. 

**Examples**:
- `python sheikhbot.py --user-agent "Googlebot"` (mimics Googlebot)

**Available Crawlers**: 
Googlebot, Bingbot, Yandex Bot, Apple Bot, DuckDuck Bot, Baidu Spider, Sogou Spider, Facebook External Hit, Exabot, Swiftbot, Slurp Bot, CCBot, Google-InspectionTool, Ahrefs Bot, Semrush Bot, Moz's Rogerbot, Screaming Frog, Lumar, Majestic, Cognitive SEO, Oncrawl

**Default**: SheikhBot/1.0 if no flag is provided.

## Notes

Please integrate this code into the existing SheikhBot project, ensuring it aligns with its current structure and HTTP request methods.

### Additional Requirements

If there are other tasks like using NVIDIA API secrets, Hugging Face tokens, creating datasets/models, or editing `index.html`, please provide more context to address those specific needs.
