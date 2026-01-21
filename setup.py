"""
Setup script for Secure Data Wiping System

Installation and packaging configuration for the secure data wiping system.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path, "r", encoding="utf-8") as f:
        requirements = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith("#") and not line.startswith("sqlite3")
        ]

setup(
    name="secure-data-wiping",
    version="1.0.0",
    author="Final Year Project Student",
    author_email="student@university.edu",
    description="Secure Data Wiping for Trustworthy IT Asset Recycling using Blockchain-Based Audit Trail",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/student/secure-data-wiping",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Topic :: Security :: Cryptography",
        "Topic :: System :: Systems Administration",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.4",
            "pytest-cov>=4.1.0",
            "black>=23.12.1",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
        ],
        "docs": [
            "sphinx>=7.2.6",
            "sphinx-rtd-theme>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "secure-wipe=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "secure_data_wiping": [
            "database/*.sql",
            "contracts/*.sol",
            "templates/*.html",
            "templates/*.pdf",
        ],
    },
    zip_safe=False,
    keywords="security, data-wiping, blockchain, audit-trail, nist, compliance",
    project_urls={
        "Bug Reports": "https://github.com/student/secure-data-wiping/issues",
        "Source": "https://github.com/student/secure-data-wiping",
        "Documentation": "https://secure-data-wiping.readthedocs.io/",
    },
)