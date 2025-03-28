import streamlit as st
import cv2
import numpy as np
import face_recognition
import os
import pandas as pd
import time
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import qrcode
import requests
from PIL import Image

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

# -------------------------
# Fixed Email Credentials
# -------------------------
SENDER_EMAIL = "adityasuyal0001@gmail.com"         # Replace with your Gmail address
SENDER_PASSWORD = "ibqw bipb petk lcvu"             # Replace with your Gmail App Password
ADMIN_EMAIL = "adityasuyal1000@gmail.com"           # Replace with admin's email address

# -------------------------
# Configuration
# -------------------------
TRAINING_IMAGES_DIR = "Training_Images"             # Directory for training images
TOLERANCE = 0.6                                     # Face recognition matching threshold
MODEL = "hog"                                       # Use 'hog' for CPU and 'cnn' for GPU
REWARDS_FILE = "rewards.csv"                        # File to track attendance rewards
ATTENDANCE_FILE = "Attendance.csv"                  # File to track attendance records
qr_folder = "QR_Codes"                              # Folder for QR codes

os.makedirs(TRAINING_IMAGES_DIR, exist_ok=True)
os.makedirs(qr_folder, exist_ok=True)

# -------------------------
# QR Code & Registration Functions
# -------------------------
def upload_to_imgur(image_path):
    CLIENT_ID = "865c3e5bfc8ef5d"  # Replace with your Imgur API client ID
    headers = {"Authorization": f"Client-ID {CLIENT_ID}"}
    with open(image_path, "rb") as img:
        response = requests.post("https://api.imgur.com/3/upload", headers=headers, files={"image": img})
    if response.status_code == 200:
        return response.json()["data"]["link"]
    else:
        st.error("⚠️ Image upload failed!")
        return None

def generate_qr_with_image_url(name, img_path):
    image_url = upload_to_imgur(img_path)
    if image_url:
        qr_data = f"Name: {name}\nStudent at Birla Institute of Applied Sciences\nPhoto: {image_url}"
        qr = qrcode.QRCode(version=4, box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill="black", back_color="white")
        qr_path = f"{qr_folder}/{name}_qr.png"
        qr_img.save(qr_path)
        return qr_path, image_url
    return None, None

# -------------------------
# Cached Function: Load Known Faces
# -------------------------
@st.cache_data
def get_known_faces():
    known_faces = []
    known_names = []
    for filename in os.listdir(TRAINING_IMAGES_DIR):
        if not filename.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
            continue
        img_path = os.path.join(TRAINING_IMAGES_DIR, filename)
        image = face_recognition.load_image_file(img_path)
        encoding = face_recognition.face_encodings(image)
        if encoding:
            known_faces.append(encoding[0])
            known_names.append(os.path.splitext(filename)[0])
    return known_faces, known_names

# -------------------------
# Function: Recognize Face
# -------------------------
def recognize_face(unknown_image):
    known_faces, known_names = get_known_faces()
    unknown_encoding = face_recognition.face_encodings(unknown_image)
    if unknown_encoding:
        matches = face_recognition.compare_faces(known_faces, unknown_encoding[0], TOLERANCE)
        if True in matches:
            matched_index = matches.index(True)
            return known_names[matched_index]
    return None

# -------------------------
# Function: Update Rewards
# -------------------------
def update_rewards(student_name):
    if os.path.exists(REWARDS_FILE) and os.path.getsize(REWARDS_FILE) > 0:
        try:
            df = pd.read_csv(REWARDS_FILE)
        except Exception as e:
            st.error(f"Error reading {REWARDS_FILE}: {e}")
            df = pd.DataFrame(columns=["Name", "AttendanceCount", "Badge"])
    else:
        df = pd.DataFrame(columns=["Name", "AttendanceCount", "Badge"])
    
    if student_name in df["Name"].values:
        df.loc[df["Name"] == student_name, "AttendanceCount"] += 1
    else:
        new_entry = pd.DataFrame({"Name": [student_name], "AttendanceCount": [1], "Badge": [""]})
        df = pd.concat([df, new_entry], ignore_index=True)
    
    def get_badge(count):
        if count >= 10:
            return "Gold"
        elif count >= 5:
            return "Silver"
        elif count >= 4:
            return "Bronze"
        else:
            return "No Badge"
    
    df["Badge"] = df["AttendanceCount"].apply(get_badge)
    df.to_csv(REWARDS_FILE, index=False)
    return df[df["Name"] == student_name].iloc[0]

# -------------------------
# Function: Mark Attendance & Update Rewards, then Send Email
# -------------------------
def mark_attendance_and_reward(student_name, frame):
    # Load or create attendance CSV
    if not os.path.exists(ATTENDANCE_FILE) or os.stat(ATTENDANCE_FILE).st_size == 0:
        df = pd.DataFrame(columns=["Name", "Date", "Time"])
        df.to_csv(ATTENDANCE_FILE, index=False)
    else:
        try:
            df = pd.read_csv(ATTENDANCE_FILE)
        except pd.errors.EmptyDataError:
            df = pd.DataFrame(columns=["Name", "Date", "Time"])
    
    now = datetime.now()
    dateString = now.strftime('%Y-%m-%d')
    timeString = now.strftime('%H:%M:%S')
    
    # Check if attendance for this student is already marked today
    if ((df["Name"] == student_name) & (df["Date"] == dateString)).any():
        return None, None, None
    else:
        new_entry = pd.DataFrame([[student_name, dateString, timeString]], columns=["Name", "Date", "Time"])
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_csv(ATTENDANCE_FILE, index=False)
    
        reward_info = update_rewards(student_name)
        send_email(student_name, frame, f"{dateString} {timeString}", reward_info['Badge'])
        return dateString, timeString, reward_info

# -------------------------
# Function: Send Email Notification with Image and Timestamp
# -------------------------
def send_email(student_name, captured_img, timestamp, badge):
    subject = "Attendance Marked Notification"
    body = f"Attendance for {student_name} has been marked at {timestamp}.\nCurrent Badge: {badge}"
    
    msg = MIMEMultipart()
    msg["From"] = "GateAttend <{}>".format(SENDER_EMAIL)
    msg["To"] = ADMIN_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    
    retval, buffer = cv2.imencode('.jpg', captured_img)
    if retval:
        image_bytes = buffer.tobytes()
        image_mime = MIMEImage(image_bytes, name="attendance.jpg")
        msg.attach(image_mime)
    else:
        st.error("❌ Failed to encode image for attachment.")
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, ADMIN_EMAIL, msg.as_string())
        server.quit()
        st.success(f"✅ Email sent to Admin@BIAS for {student_name} at {timestamp}!")
    except Exception as e:
        st.error(f"❌ Error sending email: {e}")

# -------------------------
# Function: Generate Attendance Report (Optional)
# -------------------------
def generate_attendance_report():
    df = pd.read_csv(ATTENDANCE_FILE)
    if df.empty:
        st.warning("⚠️ No attendance records found.")
        return
    unique_dates = df["Date"].unique()
    for date in unique_dates:
        date_df = df[df["Date"] == date]
        filename = f"Attendance_Report_{date}.pdf"
        c = canvas.Canvas(filename, pagesize=letter)
        c.drawString(100, 750, f"Attendance Report - {date}")
        y_position = 720
        for index, row in date_df.iterrows():
            c.drawString(100, y_position, f"{row['Name']} - {row['Time']}")
            y_position -= 20
        c.save()
        st.success(f"✅ Attendance Report Generated for {date}: {filename}")

# -------------------------
# Streamlit UI
# -------------------------
st.title("Face Recognition Attendance System with Rewards")

st.sidebar.header("Controls")
if st.sidebar.button("Download Attendance Report"):
    generate_attendance_report()

# Initialize webcam control, last recognized face, and last marked time in session state
if "webcam_active" not in st.session_state:
    st.session_state["webcam_active"] = False
if "last_recognized" not in st.session_state:
    st.session_state["last_recognized"] = None
if "last_marked_time" not in st.session_state:
    st.session_state["last_marked_time"] = 0

if st.sidebar.button("Start Webcam"):
    st.session_state["webcam_active"] = True
if st.sidebar.button("Stop Webcam"):
    st.session_state["webcam_active"] = False

# Face Registration (Optional)
if st.sidebar.button("Register New Face"):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error("⚠️ Unable to access the webcam.")
    else:
        st.write("📸 Capturing Image... Please wait for 4 seconds.")
        start_time = time.time()
        last_frame = None
        while time.time() - start_time < 4:
            success, frame = cap.read()
            if success:
                last_frame = frame
        cap.release()
        if last_frame is not None:
            st.session_state["captured_image"] = last_frame
            st.success("✅ Image Captured Successfully!")

if "captured_image" in st.session_state:
    name = st.text_input("Enter Your Name:")
    if st.button("Save Image"):
        if name:
            file_path = f"{TRAINING_IMAGES_DIR}/{name}.jpg"
            cv2.imwrite(file_path, st.session_state["captured_image"])
            qr_path, image_url = generate_qr_with_image_url(name, file_path)
            if qr_path:
                st.image(qr_path, caption="Generated QR Code")
                st.success(f"✅ {name} Registered Successfully!")
                st.write(f"📷 **Student Image URL:** [{image_url}]({image_url})")
            del st.session_state["captured_image"]
        else:
            st.warning("⚠️ Please enter a name before saving.")

# -------------------------
# Live Webcam Capture for Attendance with Frame Skipping, Duplicate Prevention, and 5-Second Delay
# -------------------------
if st.session_state.get("webcam_active"):
    cap = cv2.VideoCapture(0)
    FRAME_WINDOW = st.image([])
    frame_count = 0
    frame_skip_rate = 3  # Process every 3rd frame

    while st.session_state.get("webcam_active"):
        success, frame = cap.read()
        if not success:
            st.error("⚠️ Failed to capture image from webcam!")
            break

        frame_count += 1
        current_time = time.time()

        # Process every nth frame only
        if frame_count % frame_skip_rate == 0:
            # Downscale for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            facesCurFrame = face_recognition.face_locations(rgb_small_frame, model=MODEL)
            encodesCurFrame = face_recognition.face_encodings(rgb_small_frame, facesCurFrame)
            known_faces, known_names = get_known_faces()

            for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
                matches = face_recognition.compare_faces(known_faces, encodeFace, TOLERANCE)
                faceDis = face_recognition.face_distance(known_faces, encodeFace)
                matchIndex = np.argmin(faceDis) if len(faceDis) > 0 else None
                threshold = 0.5

                if matchIndex is not None and matches[matchIndex] and faceDis[matchIndex] < threshold:
                    current_name = known_names[matchIndex].upper()
                    
                    # If the same face was previously recognized
                    if st.session_state.get("last_recognized") == current_name:
                        # Check if 5 seconds have elapsed since last attendance marking
                        elapsed = current_time - st.session_state["last_marked_time"]
                        if elapsed < 5:
                            wait_time = 5 - elapsed
                            cv2.putText(frame, f"Please wait {wait_time:.1f}s", (50, 50),
                                        cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
                        else:
                            # Enough time has passed; mark attendance again (if needed)
                            result = mark_attendance_and_reward(current_name, frame)
                            if result[0] is not None:
                                st.session_state["last_marked_time"] = current_time
                    else:
                        # Different face detected, mark attendance immediately.
                        result = mark_attendance_and_reward(current_name, frame)
                        if result[0] is not None:
                            st.session_state["last_recognized"] = current_name
                            st.session_state["last_marked_time"] = current_time

                    # Draw rectangle and label around the face (scaling coordinates back)
                    y1, x2, y2, x1 = faceLoc
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, current_name, (x1 + 6, y2 - 6),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)

        FRAME_WINDOW.image(frame, channels="BGR")
        time.sleep(0.03)  # Small delay to yield CPU time
    cap.release()
if st.sidebar.button("Show Attendance"):
    df = pd.read_csv(ATTENDANCE_FILE)
    st.write(df)
