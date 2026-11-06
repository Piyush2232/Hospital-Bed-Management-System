"""Hospital Bed Management System – Flask Application."""
from flask import Flask, render_template, request, jsonify
from models import db, Ward, Bed, Patient, Admission, TransferLog, CleaningLog
from datetime import datetime
from seed import seed_database
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///hospital.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)


# ═══════════════════════════════════════════════════════════
#  PAGE ROUTES
# ═══════════════════════════════════════════════════════════

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/admit")
def admit_page():
    return render_template("admit.html")

@app.route("/patients")
def patients_page():
    return render_template("patients.html")


# ═══════════════════════════════════════════════════════════
#  API  –  DASHBOARD / STATS
# ═══════════════════════════════════════════════════════════

@app.route("/api/stats")
def api_stats():
    beds = Bed.query.all()
    total = len(beds)
    avail = sum(1 for b in beds if b.status == "Available")
    occ   = sum(1 for b in beds if b.status == "Occupied")
    cln   = sum(1 for b in beds if b.status == "Cleaning")
    res   = sum(1 for b in beds if b.status == "Reserved")
    mnt   = sum(1 for b in beds if b.status == "Maintenance")
    rate  = round((occ / total) * 100, 1) if total else 0
    return jsonify({
        "total": total, "available": avail, "occupied": occ,
        "cleaning": cln, "reserved": res, "maintenance": mnt,
        "occupancy_rate": rate,
        "admitted_patients": Patient.query.filter_by(status="Admitted").count(),
        "total_patients": Patient.query.count(),
    })


# ═══════════════════════════════════════════════════════════
#  API  –  WARDS & BEDS
# ═══════════════════════════════════════════════════════════

@app.route("/api/wards")
def api_wards():
    wards = Ward.query.order_by(Ward.floor, Ward.name).all()
    result = []
    for w in wards:
        wd = w.to_dict()
        wd["beds"] = [b.to_dict(include_patient=True) for b in w.beds]
        result.append(wd)
    return jsonify(result)


@app.route("/api/beds/recommend")
def api_recommend_bed():
    ward_type = request.args.get("ward_type", "")
    bed_type  = request.args.get("bed_type", "Standard")
    query = Bed.query.join(Ward).filter(Bed.status == "Available")
    if ward_type:
        query = query.filter(Ward.ward_type == ward_type)
    if bed_type:
        query = query.filter(Bed.bed_type == bed_type)
    beds = query.all()
    # Fallback: if no exact bed_type match, try any available in that ward
    if not beds and ward_type:
        beds = Bed.query.join(Ward).filter(
            Ward.ward_type == ward_type, Bed.status == "Available"
        ).all()
    return jsonify([b.to_dict() for b in beds])


# ═══════════════════════════════════════════════════════════
#  API  –  PATIENT ADMISSION
# ═══════════════════════════════════════════════════════════

@app.route("/api/patients/admit", methods=["POST"])
def api_admit():
    data = request.get_json()
    required = ["name", "age", "gender", "bed_id"]
    for f in required:
        if f not in data or data[f] is None or data[f] == "":
            return jsonify({"error": f"'{f}' is required"}), 400

    bed = Bed.query.get(data["bed_id"])
    if not bed:
        return jsonify({"error": "Bed not found"}), 404
    if bed.status != "Available":
        return jsonify({"error": f"Bed {bed.bed_number} is not available (status: {bed.status})"}), 409

    patient = Patient(
        name=data["name"],
        age=int(data["age"]),
        gender=data["gender"],
        contact=data.get("contact", ""),
        emergency_contact=data.get("emergency_contact", ""),
        medical_condition=data.get("medical_condition", ""),
        priority=data.get("priority", "Normal"),
        status="Admitted",
    )
    db.session.add(patient)
    db.session.flush()

    bed.status = "Occupied"
    admission = Admission(
        patient_id=patient.id,
        bed_id=bed.id,
        notes=data.get("notes", ""),
    )
    db.session.add(admission)
    db.session.commit()

    return jsonify({"message": f"Patient '{patient.name}' admitted to bed {bed.bed_number}.", "patient": patient.to_dict()}), 201


# ═══════════════════════════════════════════════════════════
#  API  –  DISCHARGE
# ═══════════════════════════════════════════════════════════

@app.route("/api/patients/<int:patient_id>/discharge", methods=["POST"])
def api_discharge(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    if patient.status != "Admitted":
        return jsonify({"error": "Patient is not currently admitted"}), 409

    admission = Admission.query.filter_by(patient_id=patient.id, discharge_date=None).first()
    if not admission:
        return jsonify({"error": "No active admission found"}), 404

    admission.discharge_date = datetime.utcnow()
    bed = admission.bed
    bed.status = "Cleaning"  # Bed goes to cleaning after discharge
    patient.status = "Discharged"

    cleaning = CleaningLog(bed_id=bed.id, status="Pending")
    db.session.add(cleaning)
    db.session.commit()

    return jsonify({"message": f"Patient '{patient.name}' discharged. Bed {bed.bed_number} sent for cleaning."})


# ═══════════════════════════════════════════════════════════
#  API  –  TRANSFER
# ═══════════════════════════════════════════════════════════

@app.route("/api/patients/<int:patient_id>/transfer", methods=["POST"])
def api_transfer(patient_id):
    data = request.get_json()
    to_bed_id = data.get("to_bed_id")
    if not to_bed_id:
        return jsonify({"error": "'to_bed_id' is required"}), 400

    patient = Patient.query.get(patient_id)
    if not patient or patient.status != "Admitted":
        return jsonify({"error": "Patient not found or not admitted"}), 404

    admission = Admission.query.filter_by(patient_id=patient.id, discharge_date=None).first()
    if not admission:
        return jsonify({"error": "No active admission"}), 404

    to_bed = Bed.query.get(to_bed_id)
    if not to_bed or to_bed.status != "Available":
        return jsonify({"error": "Target bed not available"}), 409

    from_bed = admission.bed
    # Log the transfer
    log = TransferLog(
        patient_id=patient.id,
        from_bed_id=from_bed.id,
        to_bed_id=to_bed.id,
        reason=data.get("reason", ""),
    )
    db.session.add(log)

    # Close old admission, open new one
    admission.discharge_date = datetime.utcnow()
    from_bed.status = "Cleaning"
    cleaning = CleaningLog(bed_id=from_bed.id, status="Pending")
    db.session.add(cleaning)

    to_bed.status = "Occupied"
    new_admission = Admission(
        patient_id=patient.id,
        bed_id=to_bed.id,
        notes=f"Transferred from {from_bed.bed_number}: {data.get('reason', '')}",
    )
    db.session.add(new_admission)
    db.session.commit()

    return jsonify({"message": f"Patient transferred from {from_bed.bed_number} to {to_bed.bed_number}."})


# ═══════════════════════════════════════════════════════════
#  API  –  CLEANING
# ═══════════════════════════════════════════════════════════

@app.route("/api/beds/<int:bed_id>/cleaning/complete", methods=["POST"])
def api_cleaning_complete(bed_id):
    bed = Bed.query.get(bed_id)
    if not bed:
        return jsonify({"error": "Bed not found"}), 404
    if bed.status != "Cleaning":
        return jsonify({"error": "Bed is not in cleaning status"}), 409

    bed.status = "Available"
    log = CleaningLog.query.filter_by(bed_id=bed.id, status="Pending").first()
    if log:
        log.status = "Completed"
        log.completed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": f"Bed {bed.bed_number} cleaned and now available."})


# ═══════════════════════════════════════════════════════════
#  API  –  MAINTENANCE TOGGLE
# ═══════════════════════════════════════════════════════════

@app.route("/api/beds/<int:bed_id>/maintenance", methods=["POST"])
def api_maintenance(bed_id):
    bed = Bed.query.get(bed_id)
    if not bed:
        return jsonify({"error": "Bed not found"}), 404
    if bed.status == "Maintenance":
        bed.status = "Available"
        msg = f"Bed {bed.bed_number} taken out of maintenance."
    elif bed.status == "Available":
        bed.status = "Maintenance"
        msg = f"Bed {bed.bed_number} marked for maintenance."
    else:
        return jsonify({"error": f"Cannot toggle maintenance; bed is '{bed.status}'."}), 409
    db.session.commit()
    return jsonify({"message": msg})


# ═══════════════════════════════════════════════════════════
#  API  –  PATIENTS LIST
# ═══════════════════════════════════════════════════════════

@app.route("/api/patients")
def api_patients():
    status = request.args.get("status", "")
    query = Patient.query.order_by(Patient.created_at.desc())
    if status:
        query = query.filter_by(status=status)
    return jsonify([p.to_dict() for p in query.all()])


# ═══════════════════════════════════════════════════════════
#  API  –  TRANSFER LOGS
# ═══════════════════════════════════════════════════════════

@app.route("/api/transfers")
def api_transfers():
    logs = TransferLog.query.order_by(TransferLog.timestamp.desc()).limit(20).all()
    return jsonify([l.to_dict() for l in logs])


# ═══════════════════════════════════════════════════════════
#  INIT & RUN
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        try:
            if Ward.query.first() is None:
                seed_database()
                print("Database initialized and seeded successfully!")
            else:
                print("Database already contains data.")
        except Exception:
            seed_database()
            print("Database re-seeded successfully!")
    app.run(debug=True, use_reloader=False, port=5000)
