import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_email(to_email, subject, body):
    """Send an email using Gmail SMTP with proper error handling."""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("⚠️ EMAIL NOT SENT: Missing EMAIL_ADDRESS or EMAIL_PASSWORD in .env")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Connect and send
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"✅ Email sent successfully to {to_email}")
        return True

    except Exception as e:
        print(f"❌ Email Error: {e}")
        return False


def send_registration_confirmation(name, email, phone, patient_id):
    """Send a welcome message to the new patient."""
    subject = "🎉 Welcome to Hospital Chatbot!"
    body = f"""
    Hello {name},

    ✅ Your registration is successful!
    Your Patient ID: {patient_id}

    Thank you for choosing our Hospital Appointment System.
    """
    send_email(email, subject, body)


def send_appointment_confirmation(patient_email, patient_phone, doctor_name, date, time):
    """Send a confirmation message for booked appointments."""
    subject = "✅ Appointment Confirmed"
    body = f"""
    Dear Patient,

    Your appointment has been confirmed.

    👨‍⚕️ Doctor: {doctor_name}
    📅 Date: {date}
    🕒 Time: {time}

    Please arrive 10 minutes early for your consultation.
    """
    if patient_email:
        send_email(patient_email, subject, body)
