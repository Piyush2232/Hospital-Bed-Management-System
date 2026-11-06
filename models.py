from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ─────────────────────────── Ward ───────────────────────────
class Ward(db.Model):
    __tablename__ = "wards"
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    ward_type   = db.Column(db.String(50), nullable=False)   # ICU, Emergency, General_Male, General_Female, Pediatric, Surgical_Recovery
    floor       = db.Column(db.Integer, default=1)
    beds        = db.relationship("Bed", backref="ward", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "ward_type": self.ward_type,
            "floor": self.floor,
            "total_beds": len(self.beds),
            "available": sum(1 for b in self.beds if b.status == "Available"),
            "occupied":  sum(1 for b in self.beds if b.status == "Occupied"),
            "cleaning":  sum(1 for b in self.beds if b.status == "Cleaning"),
            "reserved":  sum(1 for b in self.beds if b.status == "Reserved"),
            "maintenance": sum(1 for b in self.beds if b.status == "Maintenance"),
        }


# ─────────────────────────── Bed ────────────────────────────
class Bed(db.Model):
    __tablename__ = "beds"
    id          = db.Column(db.Integer, primary_key=True)
    bed_number  = db.Column(db.String(20), nullable=False)
    ward_id     = db.Column(db.Integer, db.ForeignKey("wards.id"), nullable=False)
    bed_type    = db.Column(db.String(30), nullable=False, default="Standard")  # Standard, Oxygen, Ventilator, Isolation
    status      = db.Column(db.String(20), nullable=False, default="Available") # Available, Reserved, Occupied, Cleaning, Maintenance
    admissions  = db.relationship("Admission", backref="bed", lazy=True)

    def current_patient(self):
        if self.status == "Occupied":
            adm = Admission.query.filter_by(bed_id=self.id, discharge_date=None).first()
            if adm:
                return adm.patient.to_dict()
        return None

    def to_dict(self, include_patient=False):
        d = {
            "id": self.id,
            "bed_number": self.bed_number,
            "ward_id": self.ward_id,
            "ward_name": self.ward.name if self.ward else None,
            "ward_type": self.ward.ward_type if self.ward else None,
            "bed_type": self.bed_type,
            "status": self.status,
        }
        if include_patient:
            d["patient"] = self.current_patient()
        return d


# ──────────────────────────── Patient ───────────────────────
class Patient(db.Model):
    __tablename__ = "patients"
    id                = db.Column(db.Integer, primary_key=True)
    name              = db.Column(db.String(150), nullable=False)
    age               = db.Column(db.Integer, nullable=False)
    gender            = db.Column(db.String(10), nullable=False)
    contact           = db.Column(db.String(15))
    emergency_contact = db.Column(db.String(15))
    medical_condition = db.Column(db.Text)
    priority          = db.Column(db.String(20), default="Normal")  # Critical, High, Normal
    status            = db.Column(db.String(20), default="Admitted") # Admitted, Discharged
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)
    admissions        = db.relationship("Admission", backref="patient", lazy=True)

    def to_dict(self):
        active = Admission.query.filter_by(patient_id=self.id, discharge_date=None).first()
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "contact": self.contact,
            "emergency_contact": self.emergency_contact,
            "medical_condition": self.medical_condition,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "bed_number": active.bed.bed_number if active else None,
            "ward_name": active.bed.ward.name if active else None,
        }


# ──────────────────────── Admission ─────────────────────────
class Admission(db.Model):
    __tablename__ = "admissions"
    id              = db.Column(db.Integer, primary_key=True)
    patient_id      = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    bed_id          = db.Column(db.Integer, db.ForeignKey("beds.id"), nullable=False)
    admission_date  = db.Column(db.DateTime, default=datetime.utcnow)
    discharge_date  = db.Column(db.DateTime, nullable=True)
    notes           = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "patient_name": self.patient.name,
            "bed_id": self.bed_id,
            "bed_number": self.bed.bed_number,
            "ward_name": self.bed.ward.name,
            "admission_date": self.admission_date.isoformat(),
            "discharge_date": self.discharge_date.isoformat() if self.discharge_date else None,
            "notes": self.notes,
        }


# ─────────────────────── Transfer Log ──────────────────────
class TransferLog(db.Model):
    __tablename__ = "transfer_logs"
    id           = db.Column(db.Integer, primary_key=True)
    patient_id   = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    from_bed_id  = db.Column(db.Integer, db.ForeignKey("beds.id"), nullable=False)
    to_bed_id    = db.Column(db.Integer, db.ForeignKey("beds.id"), nullable=False)
    reason       = db.Column(db.Text)
    timestamp    = db.Column(db.DateTime, default=datetime.utcnow)

    patient  = db.relationship("Patient")
    from_bed = db.relationship("Bed", foreign_keys=[from_bed_id])
    to_bed   = db.relationship("Bed", foreign_keys=[to_bed_id])

    def to_dict(self):
        return {
            "id": self.id,
            "patient_name": self.patient.name,
            "from_bed": self.from_bed.bed_number,
            "from_ward": self.from_bed.ward.name,
            "to_bed": self.to_bed.bed_number,
            "to_ward": self.to_bed.ward.name,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
        }


# ────────────────────── Cleaning Log ───────────────────────
class CleaningLog(db.Model):
    __tablename__ = "cleaning_logs"
    id           = db.Column(db.Integer, primary_key=True)
    bed_id       = db.Column(db.Integer, db.ForeignKey("beds.id"), nullable=False)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    status       = db.Column(db.String(20), default="Pending")  # Pending, InProgress, Completed

    bed = db.relationship("Bed")

    def to_dict(self):
        return {
            "id": self.id,
            "bed_number": self.bed.bed_number,
            "ward_name": self.bed.ward.name,
            "requested_at": self.requested_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
        }
