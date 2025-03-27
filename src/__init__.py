"""
Central Search - Advanced web crawler and SEO analysis toolkit
=============================================================

A powerful web crawler and SEO analysis tool designed to help make your
website discoverable to Search.

:copyright: (c) 2023 by Sheikh
:license: MIT, see LICENSE for more details.
"""

__title__ = "Central Search"
__version__ = "1.1.0"
__author__ = "Sheikh"
__license__ = "MIT"
__copyright__ = "Copyright 2023 Sheikh"

# Import common modules for easier access
from src.crawlers import SheikhBot
from src.utils.indexnow import IndexNowClient

# Set default logging
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

from .crawlers import SheikhBot as Central 