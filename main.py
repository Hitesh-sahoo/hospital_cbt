from fastapi import FastAPI, HTTPException, Query, Form
from fastapi.responses import JSONResponse
from database import get_db_connection, create_tables
import google.generativeai as genai
from dotenv import load_dotenv
import os
from datetime import date
from automation import send_registration_confirmation, send_appointment_confirmation
from difflib import get_close_matches

app = FastAPI(title="🏥 Hospital Appointment Chatbot API")

# Initialize DB
create_tables()

# Load Google Gemini API Key
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("❌ FATAL ERROR: GOOGLE_API_KEY not found in .env file")
else:
    genai.configure(api_key=GOOGLE_API_KEY)

llm = genai.GenerativeModel('gemini-pro')

# In-memory session store
active_sessions = {}


@app.get("/", response_class=JSONResponse, include_in_schema=False)
def home():
    return {"message": "Welcome to Hospital Chatbot API. Connect via Streamlit."}


@app.get("/register", response_class=JSONResponse, include_in_schema=False)
def register_page():
    return {"message": "Please register via the Streamlit frontend."}


@app.post("/register")
def register_patient(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone: str = Form("")
):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO patients (name, email, password, phone) VALUES (?, ?, ?, ?)",
            (name, email, password, phone)
        )
        conn.commit()
        patient_id = c.lastrowid

        send_registration_confirmation(name, email, phone, patient_id)
        return JSONResponse(content={"message": f"Patient {name} registered successfully!"}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"message": f"Registration failed: {str(e)}"}, status_code=400)
    finally:
        conn.close()


@app.post("/login")
def login_patient(email: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    c = conn.cursor()
    patient = c.execute(
        "SELECT * FROM patients WHERE email=? AND password=?",
        (email, password)
    ).fetchone()
    conn.close()

    if patient:
        return JSONResponse(content={
            "message": f"Welcome back, {patient['name']}!",
            "patient_id": patient['patient_id'],
            "name": patient['name']
        }, status_code=200)
    else:
        return JSONResponse(content={"message": "Invalid email or password"}, status_code=401)


@app.post("/doctor/add")
def add_doctor(name: str, specialization: str, available_days: str, available_times: str):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO doctors (name, specialization, available_days, available_times) VALUES (?, ?, ?, ?)",
        (name, specialization, available_days, available_times)
    )
    conn.commit()
    conn.close()
    return {"message": f"Doctor {name} added successfully!"}


@app.get("/doctors")
def get_doctors():
    conn = get_db_connection()
    doctors = conn.execute("SELECT * FROM doctors").fetchall()
    conn.close()
    return {"doctors": [dict(d) for d in doctors]}


@app.get("/patients")
def get_patients():
    conn = get_db_connection()
    patients = conn.execute("SELECT * FROM patients").fetchall()
    conn.close()
    return {"patients": [dict(p) for p in patients]}


# 🔥 Updated core function
def get_specialization_from_ai(symptoms_text: str):
    specialty_keywords = {
        "Cardiologist": ["chest pain", "chest", "heart", "bp", "pressure", "breath"],
        "Gastroenterologist": ["stomach", "vomit", "diarrhea", "gas", "abdomen"],
        "Neurologist": ["seizure", "migraine", "dizziness", "numb", "headache"],
        "Dermatologist": ["skin", "rash", "itch", "acne"],
        "Orthopedic": ["joint", "knee", "back", "bone", "shoulder"],
        "Pediatrician": ["child", "baby", "kid"],
        "Ophthalmologist": ["eye", "vision", "blur"],
        "ENT Specialist": ["ear", "nose", "throat", "sinus"],
        "Gynecologist": ["pregnancy", "period", "uterus"],
        "Endocrinologist": ["diabetes", "thyroid", "hormone"],
        "Nephrologist": ["kidney", "urine"],
        "General Physician": ["fever", "cold", "cough", "weakness"]
    }
    text = (symptoms_text or "").lower().strip()
    print("🩺 Input:", text)

    # 🔥 STEP 1: scoring
    scores={}
    for spec, keywords in specialty_keywords.items():
        score=0
        for kw in keywords:
            if kw in text:
                score+=1
        scores[spec]=score

    print("🧠 Scores:", scores)

    best_spec = max(scores, key=scores.get)

    if scores[best_spec] >0:
        print(f"✅ Selected -> {best_spec}")
        return best_spec
    
    try:
        prompt=f"""
Choose ONLY ONE specialization:

Cardiologist
Gastroenterologist
Neurologist
Dermatologist
Orthopedic
Pediatrician
Ophthalmologist
ENT Specialist
Gynecologist
Endocrinologist
Nephrologist
General Physician
Reply ONLY with the exact name.
Symptoms: {symptoms_text}
"""
        response = llm.generate_content(prompt)
        if hasattr(response, "text"):
            result = response.text.strip()
        else:
            result = str(response)
        print("🧠 AI:", result)
        return result
    except Exception as e:
        print("❌ AI Error:", e)
        return "General Physician"
    


@app.post("/chatbot")
def chatbot(symptoms: str = Query(...), patient_id: int = Query(...)):
    conn = get_db_connection()
    c = conn.cursor()

    greetings = ["hi", "hello", "hey", "good morning", "morning"]

    if any(greet in symptoms.lower() for greet in greetings):
        conn.close()
        return {"message": "👋 Hello! I'm your AI Hospital Assistant. Please describe your symptoms."}

    if patient_id in active_sessions and active_sessions[patient_id].get("awaiting_confirmation"):
        session = active_sessions[patient_id]

        if symptoms.lower() in ["yes", "y", "ok", "sure", "book", "confirm"]:
            c.execute(
                "INSERT INTO appointments (doctor_id, patient_id, date, time) VALUES (?, ?, ?, ?)",
                (session["doctor_id"], patient_id, session["date"], session["time"])
            )
            conn.commit()

            send_appointment_confirmation(
                patient_email=session.get("patient_email", ""),
                patient_phone=session.get("patient_phone", ""),
                doctor_name=session["doctor_name"],
                date=session["date"],
                time=session["time"]
            )

            del active_sessions[patient_id]
            conn.close()
            return {"message": f"✅ Booking Confirmed with {session['doctor_name']} at {session['time']}!"}

        elif symptoms.lower() in ["no", "n", "cancel"]:
            del active_sessions[patient_id]
            conn.close()
            return {"message": "❌ Booking cancelled. Describe your symptoms to start over."}

    try:
        specialization = get_specialization_from_ai(symptoms)
        c.execute("SELECT * FROM doctors WHERE LOWER(specialization) LIKE ? LIMIT 1", (f"%{specialization.lower()}%",))
        doctor = c.fetchone()

        if not doctor:
            conn.close()
            return {"message": f"⚠️ I recommend a {specialization}, but no doctors are available."}

        available_times = [t.strip() for t in doctor["available_times"].split(",")]
        today = str(date.today())
        booked_times = [row["time"] for row in c.execute(
            "SELECT time FROM appointments WHERE doctor_id=? AND date=?",
            (doctor["doctor_id"], today)
        ).fetchall()]

        free_time = next((t for t in available_times if t not in booked_times), None)
        if not free_time:
            conn.close()
            return {"message": f"⚠️ {doctor['name']} is fully booked today."}

        patient_data = c.execute("SELECT email, phone FROM patients WHERE patient_id=?", (patient_id,)).fetchone()
        active_sessions[patient_id] = {
            "awaiting_confirmation": True,
            "doctor_id": doctor["doctor_id"],
            "doctor_name": doctor["name"],
            "specialization": doctor["specialization"],
            "date": today,
            "time": free_time,
            "patient_email": patient_data["email"] if patient_data else "",
            "patient_phone": patient_data["phone"] if patient_data else ""
        }

        conn.close()
        return {
            "message": (
                f"🩺 Recommendation: **{specialization}**\n"
                f"👨‍⚕️ Doctor: **{doctor['name']}**\n"
                f"🕒 Slot: **{free_time}**\n\n"
                f"Shall I book this? (Yes/No)"
            )
        }

    except Exception as e:
        conn.close()
        return {"message": f"Error: {str(e)}"}


@app.get("/appointments")
def get_appointments(patient_id: int = Query(...)):
    conn = get_db_connection()
    appointments = conn.execute(
        """
        SELECT a.appointment_id, a.date, a.time, a.status, 
               d.name AS doctor_name, d.specialization
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.doctor_id
        WHERE a.patient_id = ?
        ORDER BY a.date, a.time
        """,
        (patient_id,)
    ).fetchall()
    conn.close()

    if not appointments:
        return {"message": "You have no booked appointments."}

    return {"appointments": [dict(appt) for appt in appointments]}

@app.delete("/patients/delete")
def delete_patient(patient_id: int = Query(...)):
    conn = get_db_connection()
    c = conn.cursor()

    # Check if patient exists
    patient = c.execute(
        "SELECT * FROM patients WHERE patient_id=?",
        (patient_id,)
    ).fetchone()

    if not patient:
        conn.close()
        raise HTTPException(status_code=404, detail="Patient not found")

    # Delete appointments first
    c.execute(
        "DELETE FROM appointments WHERE patient_id=?",
        (patient_id,)
    )

    # Delete patient
    c.execute(
        "DELETE FROM patients WHERE patient_id=?",
        (patient_id,)
    )

    conn.commit()
    conn.close()

    return {"message": f"🗑️ Patient ID {patient_id} deleted successfully!"}

@app.delete("/appointments/delete")
def delete_appointment(appointment_id: int = Query(...)):
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM appointments WHERE appointment_id=?", (appointment_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Appointment not found")

    c.execute("DELETE FROM appointments WHERE appointment_id=?", (appointment_id,))
    conn.commit()
    conn.close()

    return {"message": f"🗑️ Appointment ID {appointment_id} deleted successfully!"}
