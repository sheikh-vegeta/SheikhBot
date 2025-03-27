"""Common user agent strings for web crawlers and configuration."""

# Standard user agent strings for common web crawlers
USER_AGENTS = {
    "Googlebot": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Bingbot": "Mozilla/5.0 (compatible; bingbot/2.0; +https://www.bing.com/bingbot.htm)", 
    "YandexBot": "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)",
    "AppleBot": "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebkit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1 (Applebot/0.1)",
    "DuckDuckBot": "DuckDuckBot/1.0; (+http://duckduckgo.com/duckduckbot.html)",
    "BaiduSpider": "Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)",
    "SogouSpider": "sogou Pic Spider/3.0( http://www.sogou.com/docs/help/webmasters.htm#07)",
    "FacebookExternalHit": "facebookexternalhit/1.0 (+http://www.facebook.com/externalhit_uatext.php)",
    "Exabot": "Mozilla/5.0 (compatible; Exabot/3.0; +http://www.exabot.com/go/robot)",
    "Swiftbot": "Mozilla/5.0 (compatible; Swiftbot/1.0; UID/54e1c2ebd3b687d3c8000018; +http://swiftype.com/swiftbot)",
    "SlurpBot": "Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)",
    "CCBot": "CCBot/2.0 (https://commoncrawl.org/faq/)",
    "GoogleInspectionTool": "Mozilla/5.0 (compatible; Google-InspectionTool/1.0)",
    "AhrefsBot": "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)",
    "SemrushBot": "Mozilla/5.0 (compatible; SemrushBot/7~bl; +http://www.semrush.com/bot.html)",
    "Rogerbot": "rogerbot",
    "ScreamingFrog": "Screaming Frog SE Spider",
    "Lumar": "Lumar Crawler",
    "Majestic": "MJ12bot",
    "CognitiveSEO": "JamesBOT",
    "Oncrawl": "Oncrawl"
}

# Default user agent for SheikhBot
DEFAULT_USER_AGENT = "SheikhBot/1.0 (+https://github.com/sheikh-vegeta/SheikhBot)"

def get_user_agent(user_agent_key: str = None) -> str:
    """Get user agent string by key.
    
    Args:
        user_agent_key (str, optional): Key from USER_AGENTS dict. 
            If None or invalid, returns default user agent.
            
    Returns:
        str: User agent string
    """
    if not user_agent_key:
        return DEFAULT_USER_AGENT
        
    return USER_AGENTS.get(user_agent_key, DEFAULT_USER_AGENT)

def get_available_user_agents() -> list:
    """Get list of available user agent keys.
    
    Returns:
        list: List of user agent names
    """
    return list(USER_AGENTS.keys())
