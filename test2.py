import streamlit as st
import cv2
import numpy as np
import face_recognition
import os
import pandas as pd
import time
from datetime import datetime
import qrcode
from pyzbar.pyzbar import decode

# Configuration
TRAINING_IMAGES_DIR = "Training_Images"
ATTENDANCE_FILE = "Attendance.csv"
QR_FOLDER = "QR_Codes"

os.makedirs(TRAINING_IMAGES_DIR, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)

# Function to generate QR Code for each student
def generate_qr(student_name):
    qr_data = f"{student_name}"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill="black", back_color="white")
    qr_path = f"{QR_FOLDER}/{student_name}_qr.png"
    qr_img.save(qr_path)
    return qr_path

# Function to mark attendance
def mark_attendance(student_name):
    now = datetime.now()
    dateString = now.strftime('%Y-%m-%d')
    timeString = now.strftime('%H:%M:%S')
    
    df = pd.DataFrame(columns=["Name", "Date", "Time"])
    if os.path.exists(ATTENDANCE_FILE):
        df = pd.read_csv(ATTENDANCE_FILE)
    
    if not ((df["Name"] == student_name) & (df["Date"] == dateString)).any():
        new_entry = pd.DataFrame([[student_name, dateString, timeString]], columns=["Name", "Date", "Time"])
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_csv(ATTENDANCE_FILE, index=False)
        return True
    return False

# Function to scan QR code
def scan_qr_code():
    cap = cv2.VideoCapture(0)
    st.write("Scanning QR Code...")

    # Streamlit image placeholder
    image_placeholder = st.empty()

    # Button to stop scanning
    if "stop_scanner" not in st.session_state:
        st.session_state.stop_scanner = False

    stop_button = st.button("Stop Scanner", key="stop_scanner_button")

    while not st.session_state.stop_scanner:
        success, frame = cap.read()
        if not success:
            st.error("Failed to access camera.")
            break

        # Convert frame to RGB and display in Streamlit
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_placeholder.image(frame, channels="RGB")

        decoded_objects = decode(frame)
        for obj in decoded_objects:
            student_name = obj.data.decode("utf-8")
            cap.release()
            cv2.destroyAllWindows()
            return student_name

        # Check if stop button is clicked
        if stop_button:
            st.session_state.stop_scanner = True

    cap.release()
    cv2.destroyAllWindows()
    return None


# Streamlit UI
st.title("QR Code Attendance System")
option = st.radio("Choose an option:", ("Register Student", "Scan QR for Attendance"))

if option == "Register Student":
    student_name = st.text_input("Enter Student Name:")
    if st.button("Generate QR Code"):
        if student_name:
            qr_path = generate_qr(student_name)
            st.image(qr_path, caption="Generated QR Code")
            st.success(f"QR Code generated for {student_name}.")
        else:
            st.warning("Please enter a student name.")

elif option == "Scan QR for Attendance":
    if st.button("Start Scanner"):
        student_name = scan_qr_code()
        if student_name:
            if mark_attendance(student_name):
                st.success(f"Attendance marked for {student_name}.")
            else:
                st.warning(f"{student_name} has already marked attendance today.")
        else:
            st.error("No valid QR code detected.")
