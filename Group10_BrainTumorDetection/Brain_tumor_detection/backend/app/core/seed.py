"""Seeds a DEMO doctor directory on first start. Names, phone numbers and
addresses are fictional placeholders (is_demo=True) -- replace them with
real, verified doctors before any real-world use."""
from app.core.database import SessionLocal
from app.models.models import Doctor

DEMO_DOCTORS = [
    ("Dr. Anjali Rao", "MBBS, MD (Medicine), DM (Neurology)", "Neurologist", "Demo Neuro Care Clinic", "Pune", "Sample Road, Shivajinagar, Pune", "+91 00000 00001"),
    ("Dr. Rohan Mehta", "MBBS, MS (General Surgery), MCh (Neurosurgery)", "Neurosurgeon", "Demo Brain & Spine Centre", "Pune", "Sample Lane, Kothrud, Pune", "+91 00000 00002"),
    ("Dr. Kavita Joshi", "MBBS, MD, DM (Medical Oncology)", "Neuro-oncologist", "Demo Cancer Institute", "Pune", "Sample Marg, Aundh, Pune", "+91 00000 00003"),
    ("Dr. Sameer Patil", "MBBS, MD (Medicine), DM (Endocrinology)", "Endocrinologist", "Demo Endocrine Clinic", "Pune", "Sample Chowk, Baner, Pune", "+91 00000 00004"),
    ("Dr. Neha Kulkarni", "MBBS, MD (Medicine), DM (Neurology)", "Neurologist", "Demo Neuro Hospital", "Mumbai", "Sample Street, Andheri, Mumbai", "+91 00000 00005"),
    ("Dr. Vikram Shah", "MBBS, MS (General Surgery), MCh (Neurosurgery)", "Neurosurgeon", "Demo Neurosciences Centre", "Mumbai", "Sample Road, Dadar, Mumbai", "+91 00000 00006"),
    ("Dr. Priya Nair", "MBBS, MD, DM (Medical Oncology)", "Neuro-oncologist", "Demo Oncology Centre", "Mumbai", "Sample Nagar, Powai, Mumbai", "+91 00000 00007"),
    ("Dr. Arjun Deshmukh", "MBBS, MD (Medicine), DM (Neurology)", "Neurologist", "Demo Neuro Clinic", "Nashik", "Sample Path, College Road, Nashik", "+91 00000 00008"),
]


def seed_demo_doctors():
    db = SessionLocal()
    try:
        if db.query(Doctor).count() == 0:
            for name, degree, spec, hosp, city, addr, phone in DEMO_DOCTORS:
                db.add(Doctor(full_name=name, degree=degree, specialization=spec, hospital=hosp,
                              city=city, address=addr, phone=phone, is_demo=True))
            db.commit()
    finally:
        db.close()
