import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

def scrape_contacts(url):
    """
    Scrape contact information from a given URL
    """
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find emails
        emails = []
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        
        # Look for emails in text
        for text in soup.stripped_strings:
            found_emails = re.findall(email_pattern, text)
            emails.extend(found_emails)
        
        # Look for emails in href attributes
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if href.startswith('mailto:'):
                emails.append(href[7:])
        
        # Find phone numbers (simplified pattern)
        phones = []
        phone_pattern = r'(\+\d{1,3}[-\.\s]??)?\(?\d{3}\)?[-\.\s]?\d{3}[-\.\s]?\d{4}'
        
        for text in soup.stripped_strings:
            found_phones = re.findall(phone_pattern, text)
            phones.extend(found_phones)
        
        # Create a dataframe
        contacts = []
        
        # Combine emails and phones
        for email in emails:
            contacts.append({
                "Name": "Unknown",  # Would need more complex parsing to extract names
                "Email": email,
                "Phone": "",
                "WhatsApp": "",
                "Language": "en",  # Default language
                "Country": ""
            })
        
        for phone in phones:
            contacts.append({
                "Name": "Unknown",
                "Email": "",
                "Phone": phone,
                "WhatsApp": phone,  # Assuming phone can be used for WhatsApp
                "Language": "en",
                "Country": ""
            })
        
        return pd.DataFrame(contacts)
    
    except Exception as e:
        print(f"Error scraping website: {e}")
        return pd.DataFrame()