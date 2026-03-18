import streamlit as st
import requests

st.set_page_config(page_title="🏥 Hospital Chatbot", page_icon="🤖", layout="centered")

API_URL = "http://127.0.0.1:8000"

st.sidebar.title("⚙️ Settings")
theme = st.sidebar.radio("Choose Theme", ["🌞 Light", "🌙 Dark"])

if theme == "🌞 Light":
    bg_color = "#ffffff"
    text_color = "#000000"
    user_bg = "#DCF8C6"
    bot_bg = "#F1F0F0"
else:
    bg_color = "#1e1e1e"
    text_color = "#f5f5f5"
    user_bg = "#00b4d8"
    bot_bg = "#333333"

st.markdown(
    f"""
    <style>
    body {{ background-color: {bg_color}; color: {text_color}; }}
    .stApp {{ background-color: {bg_color}; color: {text_color}; }}
    .stButton>button {{ background-color: #0d6efd; color: white; border-radius: 8px; padding: 0.5em 1em; }}
    </style>
    """,
    unsafe_allow_html=True
)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "patient_id" not in st.session_state:
    st.session_state.patient_id = None
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🏥 Hospital Appointment Chatbot")

if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["🔑 Login", "🧍 Register"])

    with tab1:
        st.subheader("Patient Login")
        email = st.text_input("Email", placeholder="Enter your registered email")
        password = st.text_input("Password", placeholder="Enter password", type="password")

        if st.button("Login"):
            if email and password:
                try:
                    response = requests.post(f"{API_URL}/login", data={"email": email, "password": password})
                    
                    if response.status_code == 200:
                        # FIX: Read JSON
                        data = response.json() 
                        st.session_state.logged_in = True
                        st.session_state.patient_id = data.get("patient_id") 
                        st.session_state.user_name = data.get("name")
                        
                        st.success(f"🎉 {data.get('message')}")
                        st.rerun()
                    else:
                        st.warning("⚠️ Invalid email or password.")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please enter both email and password.")

    with tab2:
        st.subheader("Register New Patient")
        name = st.text_input("Full Name")
        reg_email = st.text_input("Email")
        reg_password = st.text_input("Password", type="password")
        phone = st.text_input("Phone Number")

        if st.button("Register"):
            if name and reg_email and reg_password:
                try:
                    response = requests.post(
                        f"{API_URL}/register",
                        data={"name": name, "email": reg_email, "password": reg_password, "phone": phone}
                    )
                    if response.status_code == 200:
                        st.success("✅ Registration successful! You can now log in.")
                    else:
                        st.warning(response.json().get("message", "Registration failed."))
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please fill all required fields.")

if st.session_state.logged_in:
    st.subheader(f"💬 Chat with Hospital Bot (User: {st.session_state.user_name})")

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(
                f"<div style='text-align:right; background-color:{user_bg}; color:{text_color}; padding:10px; border-radius:10px; margin:5px 0; display:inline-block; float:right; clear:both;'>{msg['text']}</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div style='text-align:left; background-color:{bot_bg}; color:{text_color}; padding:10px; border-radius:10px; margin:5px 0; display:inline-block; float:left; clear:both;'>{msg['text']}</div>",
                unsafe_allow_html=True
            )

    user_input = st.chat_input("Describe your symptoms...")

    if user_input:
        st.session_state.messages.append({"role": "user", "text": user_input})
        try:
            response = requests.post(
                f"{API_URL}/chatbot",
                params={"symptoms": user_input, "patient_id": st.session_state.patient_id},
            )
            data = response.json()
            bot_reply = data.get("message", "No reply from bot.")
        except Exception as e:
            bot_reply = f"⚠️ Error: {e}"

        st.session_state.messages.append({"role": "bot", "text": bot_reply})
        st.rerun()

    st.subheader("📅 My Booked Appointments")
    if st.button("Show My Appointments"):
        try:
            response = requests.get(f"{API_URL}/appointments", params={"patient_id": st.session_state.patient_id})
            data = response.json()
            if "appointments" in data:
                for appt in data["appointments"]:
                    st.markdown(
                        f"**Dr. {appt['doctor_name']} ({appt['specialization']})** \n"
                        f"📅 Date: {appt['date']} | 🕒 Time: {appt['time']} \n"
                        f"📋 Status: {appt.get('status', 'Confirmed')}\n---"
                    )
            else:
                st.info(data.get("message", "No appointments found."))
        except Exception as e:
            st.error(f"⚠️ Error fetching appointments: {e}")

    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()