# Face Recognition Attendance System

This is a **Face Recognition Attendance System** built using **Streamlit, OpenCV, Face Recognition API, Pandas, and SMTP Email Notifications**. The system allows users to mark attendance through facial recognition, generate QR codes for registration, track rewards based on attendance, and send email notifications to an admin.

## Features
- **Face Registration:** Capture and register new faces with QR code generation.
- **Face Recognition:** Identify and mark attendance for registered faces.
- **Attendance Tracking:** Store attendance records with timestamps.
- **Rewards System:** Assign badges (Gold, Silver, Bronze) based on attendance count.
- **Email Notifications:** Send attendance details with an image to the admin.
- **Attendance Reports:** Generate PDF reports for attendance logs.
- **Webcam Support:** Real-time face recognition via webcam.

## Requirements
### Install Dependencies
Ensure you have Python installed, then install the required libraries:
```sh
pip install streamlit opencv-python numpy face-recognition pandas requests qrcode reportlab pillow
```

## Usage
### 1. Run the Application
```sh
streamlit run app.py
```
### 2. Register a New Face
1. Click **Register New Face**.
2. Capture an image and enter your name.
3. The image will be stored, and a QR code will be generated.

### 3. Start Attendance System
1. Click **Start Webcam**.
2. The system will detect and recognize registered faces.
3. Attendance will be marked, rewards will be updated, and an email notification will be sent.

### 4. Download Attendance Reports
1. Click **Download Attendance Report** to generate a PDF report.

## Configuration
Modify the following variables in `app.py` as needed:
- `SENDER_EMAIL`: Admin email for notifications.
- `SENDER_PASSWORD`: App password for SMTP authentication.
- `TRAINING_IMAGES_DIR`: Directory for storing registered images.
- `TOLERANCE`: Face recognition threshold (default: 0.6).
- `MODEL`: Face recognition model (`hog` for CPU, `cnn` for GPU).
- `QR_FOLDER`: Directory for storing QR codes.

## Notes
- **Email Notifications** require a Gmail App Password (not your regular password). Enable **Less Secure Apps** or use **App Passwords** in Gmail settings.
- **Face Recognition** works best in well-lit environments.
- **Reward System** assigns badges based on attendance count.

## License
This project is **open-source** and free to use.





# 📢 Student Absence Notification System

## 🚀 Overview
This is a **Streamlit-based web application** that allows educational institutions to mark student absences and send notifications to parents via **SMS and WhatsApp**. The app integrates with **Twilio** for message delivery.

---

## 📌 Features
✅ **Student Selection** – Choose a student from the dropdown menu.
✅ **Absence Marking** – Mark a student as absent with a single click.
✅ **SMS Notification** – Sends an automated message to the parent's phone.
✅ **WhatsApp Integration** – Notify parents via WhatsApp using Twilio's API.
✅ **CSV-Based Student Database** – Load student details from a CSV file.

---

## 🛠️ Installation
### 1️⃣ Clone the Repository
```sh
git clone https://github.com/Adirohansuyal/FaceA.git
cd FaceA
```

### 2️⃣ Install Dependencies
Ensure you have Python installed, then run:
```sh
pip install streamlit pandas twilio
```

### 3️⃣ Set Up Twilio Credentials
Replace the placeholders in the script with your **Twilio Account SID, Auth Token, and Phone Number**.

---

## 🏃‍♂️ Usage
Run the application with:
```sh
streamlit run app.py
```
Then, open the local Streamlit URL in your browser.




