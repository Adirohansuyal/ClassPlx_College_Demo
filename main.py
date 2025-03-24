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

# Folder for training images
path = 'Training_images'
if not os.path.exists(path):
    os.makedirs(path)

# Function to load images and encode them
def load_images_and_encodings():
    images = []
    classNames = []
    myList = os.listdir(path)

    for cl in myList:
        curImg = cv2.imread(f'{path}/{cl}')
        if curImg is None:
            continue
        images.append(curImg)
        classNames.append(os.path.splitext(cl)[0])

    encodeList = findEncodings(images)
    return encodeList, classNames

# Function to generate attendance report
def generate_attendance_report():
    df = pd.read_csv("Attendance.csv")
    
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


# Function to encode training images
def findEncodings(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodes = face_recognition.face_encodings(img)
        if encodes:
            encodeList.append(encodes[0])
    return encodeList

# Function to mark attendance
def markAttendance(name):
    filename = 'Attendance.csv'
    
    # Ensure file exists with headers
    if not os.path.exists(filename) or os.stat(filename).st_size == 0:
        df = pd.DataFrame(columns=["Name", "Date", "Time"])
        df.to_csv(filename, index=False)

    try:
        df = pd.read_csv(filename)
    except pd.errors.EmptyDataError:
        df = pd.DataFrame(columns=["Name", "Date", "Time"])

    now = datetime.now()
    dateString = now.strftime('%Y-%m-%d')  # Store attendance date
    timeString = now.strftime('%H:%M:%S')  # Store attendance time

    # Avoid duplicate entries per day
    if not ((df["Name"] == name) & (df["Date"] == dateString)).any():
        new_entry = pd.DataFrame([[name, dateString, timeString]], columns=["Name", "Date", "Time"])
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_csv(filename, index=False)
        print(f"✅ Attendance marked for {name} on {dateString} at {timeString}")
    else:
        print(f"⚠️ {name} is already marked present today.")



def analyze_attendance():
    filename = 'Attendance.csv'

    if not os.path.exists(filename) or os.stat(filename).st_size == 0:
        st.warning("⚠️ No attendance data found!")
        return

    df = pd.read_csv(filename)

    if "Date" not in df.columns:
        st.error("⚠️ Date column is missing in the attendance file!")
        return

    total_days = df["Date"].nunique()  # Count total unique days
    attendance_count = df.groupby("Name")["Date"].nunique()  # Count attendance per student

    attendance_percentage = (attendance_count / total_days) * 100
    low_attendance_students = attendance_percentage[attendance_percentage < 50]

    st.subheader("📊 Attendance Analysis")
    st.write(f"Total Recorded Days: {total_days}")

    # Display students with low attendance
    if not low_attendance_students.empty:
        st.warning("⚠️ Students with less than 50% attendance:")
        st.dataframe(low_attendance_students.reset_index().rename(columns={"Date": "Attendance %"}))
    else:
        st.success("✅ No students have less than 50% attendance!")

# Load and encode known faces
encodeListKnown, classNames = load_images_and_encodings()

# Streamlit UI
st.title("Face Recognition Attendance System")
st.sidebar.header("Controls")

# Webcam control variables
if "webcam_active" not in st.session_state:
    st.session_state["webcam_active"] = False

if st.sidebar.button("Start Webcam"):
    st.session_state["webcam_active"] = True

if st.sidebar.button("Stop Webcam"):
    st.session_state["webcam_active"] = False


if st.sidebar.button("Analyze Attendance"):
    analyze_attendance()


# Webcam capture logic
if st.session_state["webcam_active"]:
    cap = cv2.VideoCapture(0)
    FRAME_WINDOW = st.image([])

    while st.session_state["webcam_active"]:
        success, img = cap.read()
        if not success:
            st.error("⚠️ Failed to capture image from webcam!")
            break

        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        facesCurFrame = face_recognition.face_locations(imgS)
        encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

        for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
            matchIndex = np.argmin(faceDis)

            threshold = 0.5  # Adjust if needed (lower = stricter)
            if matches[matchIndex] and faceDis[matchIndex] < threshold:
                name = classNames[matchIndex].upper()
                markAttendance(name)
                color = (0, 255, 0)  # Green for known faces

                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)

        FRAME_WINDOW.image(img, channels="BGR")
    
    cap.release()

# Display attendance
if st.sidebar.button("Show Attendance"):
    df = pd.read_csv('Attendance.csv')
    st.write(df)

# Register New Face
if st.sidebar.button("Register New Face"):
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        st.error("⚠️ Unable to access the webcam. Make sure it's not being used by another application.")
    else:
        st.write("📸 Capturing Image... Please wait for 4 seconds.")

        start_time = time.time()
        last_frame = None

        while time.time() - start_time < 4:  # Capture frames for 4 seconds
            success, img = cap.read()
            if success:
                last_frame = img  # Keep updating the last captured frame

        cap.release()  # Release webcam after 4 seconds

        if last_frame is not None:
            st.session_state["captured_image"] = last_frame
            st.success("✅ Image Captured Successfully!")

# Show text input and save button only if an image is captured
if "captured_image" in st.session_state:
    name = st.text_input("Enter Your Name:", key="register_name")

    if st.button("Save Image"):
        if name:
            file_path = f'Training_images/{name}.jpg'
            cv2.imwrite(file_path, st.session_state["captured_image"])
            st.success(f"✅ {name} Registered Successfully!")
            del st.session_state["captured_image"]  # Clear session after saving
        else:
            st.warning("⚠️ Please enter a name before saving.")

# Generate Attendance Report
if st.sidebar.button("Download Attendance Report"):
    generate_attendance_report()
