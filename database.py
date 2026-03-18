import sqlite3

DB_PATH = "hospital.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    c = conn.cursor()

    # --- Schema (No Changes) ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        doctor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specialization TEXT NOT NULL,
        available_days TEXT,
        available_times TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        phone TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id INTEGER NOT NULL,
        patient_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        status TEXT DEFAULT 'booked',
        FOREIGN KEY(doctor_id) REFERENCES doctors(doctor_id),
        FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
    )
    """)

    c.execute('SELECT count(*) FROM doctors')
    if c.fetchone()[0] == 0:
        doctors = [
            ("Dr. Singh", "General Physician", "Mon,Tue,Wed,Thu,Fri", "10:00 AM, 11:00 AM, 05:00 PM"),
            ("Dr. Sharma", "Cardiologist", "Mon,Tue,Wed", "10:00 AM, 02:00 PM"),
            ("Dr. Verma", "Dermatologist", "Mon,Fri", "09:00 AM, 04:00 PM"),
            ("Dr. Iyer", "Orthopedic", "Tue,Thu", "11:00 AM, 03:00 PM"),
            ("Dr. Gupta", "Pediatrician", "Mon,Fri", "09:30 AM, 02:30 PM"),
            ("Dr. Patel", "Nephrologist", "Mon,Wed", "09:00 AM, 01:00 PM"),         
            ("Dr. Khan", "Gastroenterologist", "Tue,Thu", "11:00 AM, 03:00 PM"),   
            ("Dr. Rao", "Neurologist", "Fri", "10:00 AM, 02:00 PM, 04:00 PM"),   
            ("Dr. Reddy", "Gynecologist", "Mon,Wed,Fri", "09:00 AM, 11:00 AM"), 
            ("Dr. Lee", "Ophthalmologist", "Tue", "09:00 AM, 01:00 PM"),        
            ("Dr. Bose", "ENT Specialist", "Thu", "10:00 AM, 03:00 PM"),      
            ("Dr. Ahmed", "Endocrinologist", "Mon,Thu", "09:30 AM, 02:30 PM") 
        ]
        c.executemany('INSERT INTO doctors (name, specialization, available_days, available_times) VALUES (?,?,?,?)', doctors)
        print("✅ Database initialized with 12 dummy doctors.")

    conn.commit()
    conn.close()