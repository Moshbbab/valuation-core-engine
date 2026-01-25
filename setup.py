"""
Setup configuration for Valuation Core Engine
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="valuation-core-engine",
    version="1.0.0",
    author="Hemmah Valuation Systems",
    author_email="info@hemmah.com",
    description="Enterprise-grade valuation engine implementing IVS/IFRS 13 standards",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Moshbbab/valuation-core-engine",
    project_urls={
        "Bug Tracker": "https://github.com/Moshbbab/valuation-core-engine/issues",
        "Documentation": "https://github.com/Moshbbab/valuation-core-engine/docs",
        "Source Code": "https://github.com/Moshbbab/valuation-core-engine",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
        ],
        "docs": [
            "sphinx>=7.1.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
        "api": [
            "fastapi>=0.103.0",
            "uvicorn>=0.23.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "valuation-engine=valuation_core.cli:main",
        ],
    },
)
