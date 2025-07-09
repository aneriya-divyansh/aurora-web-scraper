from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="aurora-scraper",
    version="1.0.0",
    author="Aurora Scraper Team",
    author_email="contact@aurora-scraper.com",
    description="A comprehensive web scraping solution with OpenAI integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/aurora-scraper",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup :: HTML",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "aurora-scraper=main_scraper:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.json"],
    },
    keywords=[
        "web-scraping",
        "playwright",
        "selenium",
        "openai",
        "javascript",
        "pagination",
        "infinite-scroll",
        "anti-detection",
        "data-extraction",
        "content-analysis",
    ],
    project_urls={
        "Bug Reports": "https://github.com/your-username/aurora-scraper/issues",
        "Source": "https://github.com/your-username/aurora-scraper",
        "Documentation": "https://aurora-scraper.readthedocs.io/",
    },
) 