from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pumpfun-api",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python client for the Pump.fun API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pumpfun-api",
    packages=find_packages(exclude=["tests", "examples"]),
    package_data={"pumpfun": ["py.typed"]},
    install_requires=[
        "requests>=2.25.0",
        "pydantic>=1.8.0",
        "python-dotenv>=0.15.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.0.0",
            "black>=21.0",
            "isort>=5.0.0",
            "mypy>=0.9.0",
            "types-requests>=2.25.0",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=0.5.0",
            "sphinx-autodoc-typehints>=1.12.0",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/pumpfun-api/issues",
        "Source": "https://github.com/yourusername/pumpfun-api",
    },
)
