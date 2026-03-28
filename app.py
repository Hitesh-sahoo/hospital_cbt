import streamlit as st
import requests

st.set_page_config(page_title="🏥 Hospital Chatbot", page_icon="🤖", layout="centered")

API_URL = "https://diagnoverse-ai.onrender.com"

# ---------------- Sidebar ----------------
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

    with tab1:
        st.subheader("Patient Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            try:
                response = requests.post(
                    f"{API_URL}/login",
                    data={"email": email, "password": password}
                )

                print(response.status_code, response.text)

                if response.status_code == 200 and response.text:
                    data = response.json()
                    st.session_state.logged_in = True
                    st.session_state.patient_id = data.get("patient_id")
                    st.session_state.user_name = data.get("name")
                    st.success(f"🎉 {data.get('message')}")
                    st.rerun()
                else:
                    st.error("⚠️ Invalid login or server issue.")

            except Exception as e:
                st.error(f"Error: {e}")

    with tab2:
        st.subheader("Register New Patient")
        name = st.text_input("Full Name")
        reg_email = st.text_input("Email")
        reg_password = st.text_input("Password", type="password")
        phone = st.text_input("Phone Number")

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
                    st.success("✅ Registration successful!")
                else:
                    st.error("Registration failed")

            except Exception as e:
                st.error(f"Error: {e}")

# ---------------- Chat ----------------
if st.session_state.logged_in:
    st.subheader(f"💬 Chat (User: {st.session_state.user_name})")

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(
                f"<div style='text-align:right; background:{user_bg}; padding:10px; border-radius:10px;'>{msg['text']}</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div style='text-align:left; background:{bot_bg}; padding:10px; border-radius:10px;'>{msg['text']}</div>",
                unsafe_allow_html=True
            )

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

            print(response.status_code, response.text)

            if response.status_code == 200 and response.text:
                data = response.json()
                bot_reply = data.get("message", "No reply")
            else:
                bot_reply = "⏳ Server waking up or error occurred. Try again."

        except Exception as e:
            bot_reply = f"⚠️ Error: {e}"

        st.session_state.messages.append({"role": "bot", "text": bot_reply})
        st.rerun()

    # ---------------- Appointments ----------------
    st.subheader("📅 My Appointments")

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
                            f"Dr. {appt['doctor_name']} ({appt['specialization']}) | "
                            f"{appt['date']} {appt['time']} | {appt.get('status','Confirmed')}"
                        )
                else:
                    st.info("No appointments found")

            else:
                st.error("Error fetching appointments")

        except Exception as e:
            st.error(f"Error: {e}")

    # ---------------- Logout ----------------
    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()