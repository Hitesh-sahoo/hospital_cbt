import streamlit as st
import requests

st.set_page_config(page_title="🏥 Hospital Chatbot", page_icon="🤖", layout="centered")

API_URL = "https://diagnoverse-ai.onrender.com"

# ---------------- Session ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "patient_id" not in st.session_state:
    st.session_state.patient_id = None
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🏥 Hospital Appointment Chatbot")

# ---------------- Login/Register ----------------
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["🔑 Login", "🧍 Register"])

    # -------- LOGIN --------
    with tab1:
        st.subheader("Patient Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            try:
                response = requests.post(
                    f"{API_URL}/login",
                    data={"email": email, "password": password}
                )

                if response.status_code == 200 and response.text:
                    data = response.json()
                    st.session_state.logged_in = True
                    st.session_state.patient_id = data.get("patient_id")
                    st.session_state.user_name = data.get("name")
                    st.success(data.get("message"))
                    st.rerun()
                else:
                    st.error("Invalid login or server issue")

            except Exception as e:
                st.error(f"Error: {e}")

    # -------- REGISTER --------
    with tab2:
        st.subheader("Register New Patient")
        name = st.text_input("Full Name", key="reg_name")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        phone = st.text_input("Phone Number", key="reg_phone")

        if st.button("Register"):
            try:
                response = requests.post(
                    f"{API_URL}/register",
                    data={
                        "name": name,
                        "email": reg_email,
                        "password": reg_password,
                        "phone": phone
                    }
                )

                if response.status_code == 200:
                    st.success("Registration successful")
                else:
                    st.error("Registration failed")

            except Exception as e:
                st.error(f"Error: {e}")

# ---------------- CHAT ----------------
if st.session_state.logged_in:
    st.subheader(f"💬 Chat (User: {st.session_state.user_name})")

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.write(f"🧑: {msg['text']}")
        else:
            st.write(f"🤖: {msg['text']}")

    user_input = st.chat_input("Describe your symptoms...")

    if user_input:
        st.session_state.messages.append({"role": "user", "text": user_input})

        try:
            response = requests.post(
                f"{API_URL}/chatbot",
                data={
                    "symptoms": user_input,
                    "patient_id": st.session_state.patient_id
                }
            )

            if response.status_code == 200 and response.text:
                data = response.json()
                bot_reply = data.get("message", "No reply")
            else:
                bot_reply = "Server error or empty response"

        except Exception as e:
            bot_reply = f"Error: {e}"

        st.session_state.messages.append({"role": "bot", "text": bot_reply})
        st.rerun()

    # -------- APPOINTMENTS --------
    if st.button("Show Appointments"):
        try:
            response = requests.get(
                f"{API_URL}/appointments",
                params={"patient_id": st.session_state.patient_id}
            )

            if response.status_code == 200 and response.text:
                data = response.json()

                if "appointments" in data:
                    for appt in data["appointments"]:
                        st.write(
                            f"Dr. {appt['doctor_name']} | {appt['date']} {appt['time']}"
                        )
                else:
                    st.info("No appointments found")

            else:
                st.error("Error fetching appointments")

        except Exception as e:
            st.error(f"Error: {e}")

    # -------- LOGOUT --------
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()