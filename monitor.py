# Tournament Monitoring Logic

This script monitors tournaments and extracts relevant information from documents.

## Keyword Extraction

The following keywords are extracted from the tournament documents:
- 大会
- 要項
- 申込
- 案内

## File Detection

The script currently detects the following file types:
- PDF
- Excel

## Implementation

import os
import re

# Function to monitor files in a given directory

def monitor_directory(directory):
    for filename in os.listdir(directory):
        if filename.endswith('.pdf') or filename.endswith('.xls') or filename.endswith('.xlsx'):
            process_file(os.path.join(directory, filename))

# Function to process detected files

def process_file(filepath):
    with open(filepath, 'rb') as file:
        content = file.read()
        extract_keywords(content)

# Function to extract keywords

def extract_keywords(content):
    keywords = ['大会', '要項', '申込', '案内']
    for keyword in keywords:
        if re.search(keyword.encode('utf-8'), content):
            print(f'Keyword {keyword} found in document.')