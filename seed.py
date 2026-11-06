"""Seed the database with realistic hospital wards, beds, and sample patients."""
from models import db, Ward, Bed, Patient, Admission
from datetime import datetime, timedelta
import random

def seed_database():
    """Drop and recreate all tables, then populate with sample data."""
    db.drop_all()
    db.create_all()

    # ── Wards ──────────────────────────────────────────────
    wards_data = [
        ("Emergency Ward",        "Emergency",         1),
        ("ICU – Block A",         "ICU",               2),
        ("General Ward – Male",   "General_Male",      1),
        ("General Ward – Female", "General_Female",    1),
        ("Pediatric Ward",        "Pediatric",         3),
        ("Surgical Recovery",     "Surgical_Recovery", 2),
    ]
    wards = []
    for name, wtype, floor in wards_data:
        w = Ward(name=name, ward_type=wtype, floor=floor)
        db.session.add(w)
        wards.append(w)
    db.session.flush()

    # ── Beds ───────────────────────────────────────────────
    bed_configs = {
        "Emergency":         (6,  ["Standard", "Oxygen", "Ventilator", "Standard", "Oxygen", "Standard"]),
        "ICU":               (5,  ["Ventilator", "Ventilator", "Oxygen", "Ventilator", "Isolation"]),
        "General_Male":      (8,  ["Standard"] * 8),
        "General_Female":    (8,  ["Standard"] * 8),
        "Pediatric":         (6,  ["Standard", "Standard", "Oxygen", "Standard", "Isolation", "Standard"]),
        "Surgical_Recovery": (5,  ["Standard", "Oxygen", "Standard", "Standard", "Oxygen"]),
    }

    all_beds = []
    for ward in wards:
        count, types = bed_configs[ward.ward_type]
        for i in range(count):
            prefix = ward.ward_type[:3].upper()
            bed = Bed(
                bed_number=f"{prefix}-{ward.floor}{i+1:02d}",
                ward_id=ward.id,
                bed_type=types[i],
                status="Available",
            )
            db.session.add(bed)
            all_beds.append(bed)
    db.session.flush()

    # ── Sample Patients (pre-admitted) ─────────────────────
    patients_data = [
        ("Rajesh Kumar",      45, "Male",   "9876543210", "Chest pain, cardiac monitoring",     "Critical"),
        ("Priya Sharma",      32, "Female", "9876543211", "Post-operative recovery – appendix", "Normal"),
        ("Amit Verma",        58, "Male",   "9876543212", "Severe pneumonia, oxygen support",   "High"),
        ("Sunita Devi",       67, "Female", "9876543213", "Hip replacement recovery",           "Normal"),
        ("Arjun Singh",       12, "Male",   "9876543214", "Acute asthma attack",                "High"),
        ("Meera Patel",       28, "Female", "9876543215", "Complicated delivery monitoring",    "Critical"),
        ("Vikram Reddy",      50, "Male",   "9876543216", "Diabetic ketoacidosis",              "High"),
        ("Kavita Nair",       41, "Female", "9876543217", "Road accident – multiple fractures", "Critical"),
        ("Rahul Gupta",       35, "Male",   "9876543218", "Dengue fever observation",           "Normal"),
        ("Deepika Joshi",     22, "Female", "9876543219", "Severe dehydration",                 "Normal"),
        ("Suresh Yadav",      70, "Male",   "9876543220", "Stroke – ICU monitoring",            "Critical"),
        ("Ananya Iyer",        8, "Female", "9876543221", "High fever & seizures",              "High"),
    ]

    # Assign patients to beds across different wards
    admit_targets = [
        (0, "Emergency"),          # Rajesh → Emergency
        (1, "Surgical_Recovery"),   # Priya → Surgical Recovery
        (2, "General_Male"),        # Amit → General Male
        (3, "Surgical_Recovery"),   # Sunita → Surgical Recovery
        (4, "Pediatric"),           # Arjun → Pediatric
        (5, "General_Female"),      # Meera → General Female
        (6, "ICU"),                 # Vikram → ICU
        (7, "Emergency"),           # Kavita → Emergency
        (8, "General_Male"),        # Rahul → General Male
        (9, "General_Female"),      # Deepika → General Female
        (10, "ICU"),                # Suresh → ICU
        (11, "Pediatric"),          # Ananya → Pediatric
    ]

    for idx, (p_idx, ward_type) in enumerate(admit_targets):
        pdata = patients_data[p_idx]
        patient = Patient(
            name=pdata[0], age=pdata[1], gender=pdata[2],
            contact=pdata[3], medical_condition=pdata[4],
            priority=pdata[5], status="Admitted",
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 7)),
        )
        db.session.add(patient)
        db.session.flush()

        # Find the first available bed in the target ward
        target_bed = Bed.query.join(Ward).filter(
            Ward.ward_type == ward_type,
            Bed.status == "Available"
        ).first()

        if target_bed:
            target_bed.status = "Occupied"
            admission = Admission(
                patient_id=patient.id,
                bed_id=target_bed.id,
                admission_date=patient.created_at,
                notes=f"Admitted for: {pdata[4]}",
            )
            db.session.add(admission)

    # ── Mark a couple of beds as Cleaning and Maintenance ──
    cleaning_beds = Bed.query.filter_by(status="Available").limit(2).all()
    if len(cleaning_beds) >= 2:
        cleaning_beds[0].status = "Cleaning"
        cleaning_beds[1].status = "Maintenance"

    db.session.commit()
    print(f"[OK] Seeded {len(wards)} wards, {len(all_beds)} beds, {len(patients_data)} patients.")
