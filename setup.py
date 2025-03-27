#!/usr/bin/env python3
"""
Setup script for Central Search - Advanced Web Crawler and SEO Analysis Tool
"""

import os
import re
from setuptools import setup, find_packages


# Get version from __init__.py
def get_version():
    init_py = open(os.path.join("src", "__init__.py")).read()
    return re.search(r"""__version__ = ['"]([^'"]*)['"]""", init_py).group(1)


# Read the long description from README.md
def get_long_description():
    with open("README.md", encoding="utf-8") as f:
        return f.read()


setup(
    name="central-search",
    version=get_version(),
    description="Advanced web crawler and SEO analysis toolkit",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Sheikh",
    author_email="sheikh@example.com",
    url="https://github.com/sheikh-vegeta/SheikhBot",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
        "beautifulsoup4>=4.9.0",
        "pyyaml>=5.1",
        "selenium>=4.0.0",
        "webdriver-manager>=3.5.0",
        "lxml>=4.6.0",
        "tqdm>=4.50.0",
        "colorama>=0.4.4",
        "html5lib>=1.1",
        "pyppeteer>=1.0.0",
        "validators>=0.18.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.10.0",
            "black>=21.5b2",
            "isort>=5.9.0",
            "pylint>=2.8.0",
            "mypy>=0.812",
        ],
        "mongodb": [
            "pymongo>=3.11.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "central=central:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
    ],
    keywords="web crawler, seo, search, indexing, indexnow",
    project_urls={
        "Documentation": "https://github.com/sheikh-vegeta/SheikhBot/wiki",
        "Source": "https://github.com/sheikh-vegeta/SheikhBot",
        "Tracker": "https://github.com/sheikh-vegeta/SheikhBot/issues",
    },
) 