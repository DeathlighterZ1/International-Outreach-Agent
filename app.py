import streamlit as st
import pandas as pd
import requests
import json
import os
from bs4 import BeautifulSoup
from datetime import datetime
import time
from messaging import send_whatsapp, send_sms, send_email

# Hardcoded API Keys
TEXTBEE_API_KEY = st.secrets["TEXTBEE_API_KEY"]
RESEND_API_KEY = st.secrets["RESEND_API_KEY"]
GREENAPI_INSTANCE_ID = st.secrets["GREENAPI_INSTANCE_ID"]
GREENAPI_API_TOKEN = st.secrets["GREENAPI_API_TOKEN"]
TWILIO_SID = st.secrets["TWILIO_SID"]
TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
TWILIO_PHONE_NUMBER = st.secrets["TWILIO_PHONE_NUMBER"]

# App title and description
st.title("International Outreach Agent")
st.write("Automatically send personalized multilingual greetings via WhatsApp, SMS, or Email")

# Sidebar for navigation
page = st.sidebar.selectbox("Select a page", ["Contact Collection", "Message Generation", "Send Messages", "Schedule"])

# Function to translate text
def translate_text(text, target_lang):
    url = "https://libretranslate.de/translate"
    data = {
        "q": text,
        "source": "auto",
        "target": target_lang
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        return response.json()["translatedText"]
    return text

# Contact Collection Page
if page == "Contact Collection":
    st.header("Contact Collection")
    
    # Option to upload contacts
    upload_option = st.radio("Choose an option", ["Upload CSV", "Manual Entry", "Web Scraping"])
    
    if upload_option == "Upload CSV":
        uploaded_file = st.file_uploader("Upload a CSV file with contacts", type=["csv"])
        if uploaded_file is not None:
            contacts_df = pd.read_csv(uploaded_file)
            st.session_state.contacts = contacts_df
            st.write(contacts_df)
            st.success("Contacts loaded successfully!")
    
    elif upload_option == "Manual Entry":
        st.subheader("Add Contact Manually")
        with st.form("contact_form"):
            name = st.text_input("Name")
            email = st.text_input("Email")
            phone = st.text_input("Phone (with country code)")
            whatsapp = st.text_input("WhatsApp Number (with country code)")
            language = st.selectbox("Preferred Language", ["en", "fr", "es", "de", "bn", "hi", "zh"])
            country = st.text_input("Country")
            
            submit = st.form_submit_button("Add Contact")
            
            if submit:
                if "contacts" not in st.session_state:
                    st.session_state.contacts = pd.DataFrame(columns=["Name", "Email", "Phone", "WhatsApp", "Language", "Country"])
                
                new_contact = pd.DataFrame({
                    "Name": [name],
                    "Email": [email],
                    "Phone": [phone],
                    "WhatsApp": [whatsapp],
                    "Language": [language],
                    "Country": [country]
                })
                
                st.session_state.contacts = pd.concat([st.session_state.contacts, new_contact], ignore_index=True)
                st.success(f"Contact {name} added successfully!")
        
        if "contacts" in st.session_state:
            st.write(st.session_state.contacts)
            
            if st.button("Save Contacts to CSV"):
                st.session_state.contacts.to_csv("contacts.csv", index=False)
                st.success("Contacts saved to contacts.csv")
    
    elif upload_option == "Web Scraping":
        st.subheader("Web Scraping")
        url = st.text_input("Enter URL to scrape")
        
        if st.button("Scrape Contacts") and url:
            try:
                response = requests.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # This is a simplified example - you'll need to customize based on the website structure
                emails = []
                for link in soup.find_all('a'):
                    href = link.get('href', '')
                    if href.startswith('mailto:'):
                        emails.append(href[7:])
                
                if emails:
                    st.write(f"Found {len(emails)} email addresses:")
                    st.write(emails)
                else:
                    st.warning("No email addresses found on this page.")
            except Exception as e:
                st.error(f"Error scraping website: {e}")

# Message Generation Page
elif page == "Message Generation":
    st.header("Message Generation")
    
    if "contacts" not in st.session_state:
        st.warning("Please add contacts first!")
    else:
        st.subheader("Create Greeting Template")
        greeting_template = st.text_area("Enter your greeting template", 
                                         "Dear {name}, Wishing you a joyous holiday season and a happy new year!")
        
        if st.button("Generate Multilingual Greetings"):
            if "messages" not in st.session_state:
                st.session_state.messages = []
            
            for _, contact in st.session_state.contacts.iterrows():
                personalized_greeting = greeting_template.replace("{name}", contact["Name"])
                
                # Translate the greeting
                if contact["Language"] != "en":
                    translated_greeting = translate_text(personalized_greeting, contact["Language"])
                else:
                    translated_greeting = personalized_greeting
                
                message = {
                    "name": contact["Name"],
                    "email": contact["Email"],
                    "phone": contact["Phone"],
                    "whatsapp": contact["WhatsApp"],
                    "language": contact["Language"],
                    "country": contact["Country"],
                    "greeting": translated_greeting
                }
                
                st.session_state.messages.append(message)
            
            st.success(f"Generated {len(st.session_state.messages)} personalized greetings!")
            
            # Display sample messages
            st.subheader("Sample Messages")
            for i, msg in enumerate(st.session_state.messages[:3]):
                st.write(f"**{msg['name']} ({msg['language']}):** {msg['greeting']}")

# Send Messages Page
elif page == "Send Messages":
    st.header("Send Messages")
    
    if "messages" not in st.session_state:
        st.warning("Please generate messages first!")
    else:
        st.write(f"Ready to send {len(st.session_state.messages)} messages")
        
        send_option = st.radio("Choose sending method", ["WhatsApp", "SMS", "Email"])
        
        # Add SMS service selection if SMS is chosen
        sms_service = None
        if send_option == "SMS":
            sms_service = st.selectbox("Select SMS service", ["TextBee", "Twilio", "TextBelt"])
            
            # Silently set Twilio credentials if Twilio is selected
            if sms_service == "Twilio":
                # Store credentials in session state without displaying input fields
                st.session_state.twilio_sid = TWILIO_SID
                st.session_state.twilio_token = TWILIO_AUTH_TOKEN
                st.session_state.twilio_number = TWILIO_PHONE_NUMBER
                st.info("Using configured Twilio credentials")
        
        if st.button("Send Messages"):
            sent_count = 0
            
            for message in st.session_state.messages:
                try:
                    if send_option == "WhatsApp" and message["whatsapp"]:
                        success, response_text = send_whatsapp(message["whatsapp"], message["greeting"])
                        st.write(f"WhatsApp API response: {success} - {response_text}")
                        if success:
                            sent_count += 1
                    elif send_option == "SMS" and message["phone"]:
                        if sms_service == "Twilio":
                            success, response_text = send_sms(
                                message["phone"], 
                                message["greeting"],
                                service="twilio",
                                twilio_sid=st.session_state.twilio_sid,
                                twilio_token=st.session_state.twilio_token,
                                twilio_number=st.session_state.twilio_number
                            )
                        else:
                            success, response_text = send_sms(
                                message["phone"], 
                                message["greeting"],
                                service=sms_service.lower()
                            )
                        st.write(f"SMS API response: {success} - {response_text}")
                        if success:
                            sent_count += 1
                    elif send_option == "Email" and message["email"]:
                        success, response_text = send_email(
                            message["email"], 
                            "Seasonal Greetings", 
                            message["greeting"]
                        )
                        st.write(f"Email API response: {success} - {response_text}")
                        if success:
                            sent_count += 1
                except Exception as e:
                    st.error(f"Error sending to {message['name']}: {str(e)}")
                # Add a small delay to avoid rate limiting
                time.sleep(1)
            
            if sent_count > 0:
                st.success(f"Successfully sent {sent_count} out of {len(st.session_state.messages)} messages!")
                st.balloons()  # Add a fun visual effect for successful sends
            else:
                st.error("No messages were sent successfully. Please check the errors above.")
            
            # Log successful messages
            if sent_count > 0:
                log_entry = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "method": send_option,
                    "sent_count": sent_count,
                    "total_count": len(st.session_state.messages)
                }
                
                if "message_logs" not in st.session_state:
                    st.session_state.message_logs = []
                
                st.session_state.message_logs.append(log_entry)

            # Save messages to JSON file
            with open("messages.json", "w") as f:
                json.dump(st.session_state.messages, f)

# Schedule Page
elif page == "Schedule":
    st.header("Schedule Messages")
    st.write("Set up automatic sending of your messages")
    
    # Check for trigger parameter in URL
    if st.query_params.get("trigger") == "1":
        try:
            with open("messages.json", "r") as f:
                st.session_state.messages = json.load(f)
            st.success("Loaded messages from file")
            # Send messages logic after loading
            send_option = "WhatsApp"  # Or choose dynamically as per your logic
            for message in st.session_state.messages:
                if send_option == "WhatsApp" and message["whatsapp"]:
                    success, response_text = send_whatsapp(message["whatsapp"], message["greeting"])
                    st.write(f"WhatsApp API response: {success} - {response_text}")
        except Exception as e:
            st.error(f"Error loading messages: {e}")

    st.subheader("Configure Schedule")
    schedule_date = st.date_input("Select date to send messages")
    schedule_time = st.time_input("Select time to send messages")

    if st.button("Schedule Messages"):
        scheduled_datetime = datetime.combine(schedule_date, schedule_time)
        st.success(f"Messages scheduled to be sent on {scheduled_datetime}")
        st.write("In a production environment, this would create a task on cron-job.org")
