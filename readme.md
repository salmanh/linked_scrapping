# LinkedIn Group Scraping

An auto-scraping tool for LinkedIn groups.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)

## Installation

### Prerequisites
- Python 3.x
- `python-dotenv` library
- `selenium` library

### Steps
1. Install the required libraries by running:
   ```bash
   pip install python-dotenv selenium
   ```
2. Set up your LinkedIn credentials as environment variables USERNAME and PASSWORD.
3. Clone the repository and navigate to the project directory.
### Usage
#### Examples
1. Run the script by executing:
    ```bash 
    Copy code 
   python main.py
   ```

The script will perform login, visit the LinkedIn group page, and engage with posts using the comments listed in comments.txt.

### Features
1. Automates login to LinkedIn using Selenium.
2. Visits the LinkedIn group page and engages with posts using pre-defined comments.
3. Uses python-dotenv to load environment variables for LinkedIn credentials.