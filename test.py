import streamlit as st
import pandas as pd
from twilio.rest import Client

# Twilio Credentials (Replace with your own)
TWILIO_ACCOUNT_SID = "AC03317a823dc9a40846145faed70a917c"
TWILIO_AUTH_TOKEN = "805779ba489b82b8f301a362caa2ef34"
TWILIO_PHONE_NUMBER = "+19713977910"  # Replace with your Twilio phone number

# Load student data
@st.cache_data
def load_student_data():
    return pd.read_csv("students_data.csv")

students_df = load_student_data()

# Function to send SMS via Twilio
def send_sms(student_name, parent_name, parent_contact):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
    message_body = f"Dear Parent,\nYour child {student_name} has been marked absent today.\n -Birla Institute of Applied Sciences"
    
    try:
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=parent_contact
        )
        return f"✅ SMS sent successfully to {parent_name} ({parent_contact})!"
    except Exception as e:
        return f"❌ Error sending SMS: {e}"

# Streamlit UI
st.title("📢 Student Absence Notification System ")

# Dropdown to select student
student_name = st.selectbox("Select Student", students_df["Name"].tolist())

if st.button("Mark Absence & Notify Parent"):
    student_row = students_df[students_df["Name"] == student_name].iloc[0]
    parent_name = student_row["Parent_Name"]
    parent_contact = student_row["Parent_Contact"]
    
    st.success(f"✅ Absence Marked for {student_name}")
    
    # Send SMS Notification
    sms_status = send_sms(student_name, parent_name, parent_contact)
    st.info(sms_status)
