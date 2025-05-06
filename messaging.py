import requests
import streamlit as st

# Hardcoded API Keys
TEXTBEE_API_KEY = st.secrets["TEXTBEE_API_KEY"]
RESEND_API_KEY = st.secrets["RESEND_API_KEY"]
GREENAPI_INSTANCE_ID = st.secrets["GREENAPI_INSTANCE_ID"]
GREENAPI_API_TOKEN = st.secrets["GREENAPI_API_TOKEN"]
TWILIO_SID = st.secrets["TWILIO_SID"]
TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
TWILIO_PHONE_NUMBER = st.secrets["TWILIO_PHONE_NUMBER"]

def send_whatsapp(phone_number, message):
    """
    Send WhatsApp message using GreenAPI
    """
    try:
        # Ensure phone number is in the correct format
        whatsapp_number = phone_number.replace("+", "")
        
        # Use the correct API endpoint
        url = f"https://api.green-api.com/waInstance{GREENAPI_INSTANCE_ID}/sendMessage/{GREENAPI_API_TOKEN}"
        
        payload = {
            "chatId": f"{whatsapp_number}@c.us",
            "message": message
        }
        
        response = requests.post(url, json=payload)
        return response.status_code == 200, response.text
    except Exception as e:
        return False, str(e)

def send_sms(phone_number, message, service="textbelt", **kwargs):
    """
    Send SMS using various services
    
    Parameters:
    - phone_number (str): Recipient's phone number in international format (e.g., +1234567890)
    - message (str): The text message to send
    - service (str): SMS service to use ("textbelt", "twilio", "textbee")
    - **kwargs: Additional parameters for specific services
    
    Returns:
    - tuple: (success_boolean, response_message)
    """
    try:
        # Ensure phone number is in the correct format
        if not phone_number.startswith('+'):
            phone_number = f"+{phone_number}"
        
        # TextBelt service
        if service.lower() == "textbelt":
            textbelt_url = "https://textbelt.com/text"
            textbelt_payload = {
                "phone": phone_number,
                "message": message,
                "key": "textbelt"  # Free test key - one message per day
            }
            
            response = requests.post(textbelt_url, data=textbelt_payload)
            response_data = response.json()
            
            if response_data.get("success"):
                return True, f"Message sent successfully. Quota remaining: {response_data.get('quotaRemaining', 'unknown')}"
            else:
                return False, f"SMS service failed. Error: {response_data.get('error', 'Unknown error')}"
        
        # Twilio service
        elif service.lower() == "twilio":
            from twilio.rest import Client
            
            # Get Twilio credentials from kwargs
            account_sid = kwargs.get('twilio_sid')
            auth_token = kwargs.get('twilio_token')
            from_number = kwargs.get('twilio_number')
            
            if not all([account_sid, auth_token, from_number]):
                return False, "Missing Twilio credentials"
            
            client = Client(account_sid, auth_token)
            
            message = client.messages.create(
                body=message,
                from_=from_number,
                to=phone_number
            )
            
            return True, f"Message sent with Twilio SID: {message.sid}"
        
        # TextBee service
        elif service.lower() == "textbee":
            # Implement TextBee API here
            return False, "TextBee service not implemented yet"
        
        else:
            return False, f"Unknown SMS service: {service}"
    
    except Exception as e:
        return False, f"Exception: {str(e)}"

def send_email(email, subject, message):
    """
    Send email using Resend
    """
    try:
        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "from": "onboarding@resend.dev",  # Use Resend's default verified sender
            "to": email,
            "subject": subject,
            "html": f"<p>{message}</p>"
        }
        response = requests.post(url, headers=headers, json=payload)
        return response.status_code == 200, response.text
    except Exception as e:
        return False, str(e)













