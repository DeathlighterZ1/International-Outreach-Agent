import requests
import pandas as pd
import os
from dotenv import load_dotenv
from messaging import send_whatsapp, send_sms, send_email
import json
from datetime import datetime

# Load environment variables
load_dotenv()

def send_scheduled_messages(method="all"):
    """
    Send scheduled messages - this function can be called by a cron job
    """
    try:
        # Load contacts and messages
        if os.path.exists("contacts.csv") and os.path.exists("messages.json"):
            contacts_df = pd.read_csv("contacts.csv")
            with open("messages.json", "r") as f:
                messages = json.load(f)
            
            sent_count = 0
            
            for message in messages:
                try:
                    if (method == "whatsapp" or method == "all") and message.get("whatsapp"):
                        success, _ = send_whatsapp(message["whatsapp"], message["greeting"])
                        if success:
                            sent_count += 1
                    
                    if (method == "sms" or method == "all") and message.get("phone"):
                        success, _ = send_sms(message["phone"], message["greeting"])
                        if success:
                            sent_count += 1
                    
                    if (method == "email" or method == "all") and message.get("email"):
                        success, _ = send_email(
                            message["email"], 
                            "Seasonal Greetings", 
                            message["greeting"]
                        )
                        if success:
                            sent_count += 1
                
                except Exception as e:
                    print(f"Error sending to {message.get('name', 'unknown')}: {str(e)}")
            
            # Log the results
            with open("send_log.txt", "a") as f:
                f.write(f"{datetime.now()}: Sent {sent_count} out of {len(messages)} messages via {method}\n")
            
            return {"success": True, "sent": sent_count, "total": len(messages)}
        else:
            return {"success": False, "error": "Contact or message files not found"}
    
    except Exception as e:
        with open("error_log.txt", "a") as f:
            f.write(f"{datetime.now()}: Error: {str(e)}\n")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # This can be called directly by a cron job
    result = send_scheduled_messages()
    print(json.dumps(result))