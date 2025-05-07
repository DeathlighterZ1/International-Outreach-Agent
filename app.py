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
                emails = [link.get('href', '')[7:] for link in soup.find_all('a') if link.get('href', '').startswith('mailto:')]
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
        greeting_template = st.text_area("Enter your greeting template", "Dear {name}, Wishing you a joyous holiday season and a happy new year!")
        if st.button("Generate Multilingual Greetings"):
            if "messages" not in st.session_state:
                st.session_state.messages = []
            for _, contact in st.session_state.contacts.iterrows():
                personalized = greeting_template.replace("{name}", contact["Name"])
                translated = translate_text(personalized, contact["Language"]) if contact["Language"] != "en" else personalized
                st.session_state.messages.append({
                    "name": contact["Name"],
                    "email": contact["Email"],
                    "phone": contact["Phone"],
                    "whatsapp": contact["WhatsApp"],
                    "language": contact["Language"],
                    "country": contact["Country"],
                    "greeting": translated
                })
            st.success(f"Generated {len(st.session_state.messages)} personalized greetings!")
            st.subheader("Sample Messages")
            for msg in st.session_state.messages[:3]:
                st.write(f"**{msg['name']} ({msg['language']}):** {msg['greeting']}")

# Send Messages Page
elif page == "Send Messages":
    st.header("Send Messages")
    if "messages" not in st.session_state:
        st.warning("Please generate messages first!")
    else:
        st.write(f"Ready to send {len(st.session_state.messages)} messages")
        send_option = st.radio("Choose sending method", ["WhatsApp", "SMS", "Email"])
        sms_service = st.selectbox("Select SMS service", ["TextBee", "Twilio", "TextBelt"]) if send_option == "SMS" else None
        if sms_service == "Twilio":
            st.session_state.twilio_sid = TWILIO_SID
            st.session_state.twilio_token = TWILIO_AUTH_TOKEN
            st.session_state.twilio_number = TWILIO_PHONE_NUMBER
            st.info("Using configured Twilio credentials")
        if st.button("Send Messages"):
            sent_count = 0
            for message in st.session_state.messages:
                try:
                    if send_option == "WhatsApp" and message["whatsapp"]:
                        success, text = send_whatsapp(message["whatsapp"], message["greeting"])
                    elif send_option == "SMS" and message["phone"]:
                        if sms_service == "Twilio":
                            success, text = send_sms(message["phone"], message["greeting"], service="twilio",
                                twilio_sid=st.session_state.twilio_sid,
                                twilio_token=st.session_state.twilio_token,
                                twilio_number=st.session_state.twilio_number)
                        else:
                            success, text = send_sms(message["phone"], message["greeting"], service=sms_service.lower())
                    elif send_option == "Email" and message["email"]:
                        success, text = send_email(message["email"], "Seasonal Greetings", message["greeting"])
                    else:
                        success = False
                    if success:
                        sent_count += 1
                except Exception as e:
                    st.error(f"Error sending to {message['name']}: {str(e)}")
                time.sleep(1)
            if sent_count > 0:
                st.success(f"Successfully sent {sent_count} out of {len(st.session_state.messages)} messages!")
                st.balloons()
            else:
                st.error("No messages were sent successfully.")
            log_entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "method": send_option,
                "sent_count": sent_count,
                "total_count": len(st.session_state.messages)
            }
            if "message_logs" not in st.session_state:
                st.session_state.message_logs = []
            st.session_state.message_logs.append(log_entry)

# Schedule Page
elif page == "Schedule":
    st.header("Schedule Messages")
    st.write("Set up automatic sending of your messages")
    st.subheader("Configure Schedule")
    schedule_date = st.date_input("Select date to send messages")
    schedule_time = st.time_input("Select time to send messages")
    if st.button("Schedule Messages"):
        scheduled_datetime = datetime.combine(schedule_date, schedule_time)
        st.success(f"Messages scheduled to be sent on {scheduled_datetime}")
        st.write("In a production environment, this would create a task on cron-job.org")

# External Trigger Support for cron-job.org
query_params = st.experimental_get_query_params()
if query_params.get("trigger") == ["1"]:
    st.write("🔁 Triggered by external scheduler (cron-job.org)")
    if "messages" in st.session_state:
        sent_count = 0
        for message in st.session_state.messages:
            try:
                if message["email"]:
                    success, _ = send_email(message["email"], "Automated Greetings", message["greeting"])
                    if success:
                        sent_count += 1
            except Exception as e:
                st.error(f"Error sending to {message['name']}: {str(e)}")
            time.sleep(1)
        st.success(f"✅ Cronjob: Sent {sent_count} messages.")
    else:
        st.warning("⚠️ No messages found in session. Please preload messages.")
