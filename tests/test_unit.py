import pytest
from datetime import datetime
from models import db, Ward, Bed, Patient, Admission, TransferLog, CleaningLog

class TestUnitModels:
    """Level 1: Unit Testing of individual ORM models, methods, and dictionary serializations."""

    def test_ward_creation_and_aggregation(self, app):
        with app.app_context():
            ward = Ward(name="Pediatric Ward", ward_type="Pediatric", floor=3)
            db.session.add(ward)
            db.session.commit()

            assert ward.id is not None
            assert ward.name == "Pediatric Ward"
            assert ward.ward_type == "Pediatric"
            assert ward.floor == 3

            # Test aggregation with multiple beds in different states
            b1 = Bed(bed_number="PED-301", ward_id=ward.id, status="Available")
            b2 = Bed(bed_number="PED-302", ward_id=ward.id, status="Occupied")
            b3 = Bed(bed_number="PED-303", ward_id=ward.id, status="Cleaning")
            b4 = Bed(bed_number="PED-304", ward_id=ward.id, status="Reserved")
            b5 = Bed(bed_number="PED-305", ward_id=ward.id, status="Maintenance")
            db.session.add_all([b1, b2, b3, b4, b5])
            db.session.commit()

            d = ward.to_dict()
            assert d["total_beds"] == 5
            assert d["available"] == 1
            assert d["occupied"] == 1
            assert d["cleaning"] == 1
            assert d["reserved"] == 1
            assert d["maintenance"] == 1

    def test_bed_creation_and_to_dict(self, app):
        with app.app_context():
            ward = Ward(name="Surgical Ward", ward_type="Surgical_Recovery", floor=2)
            db.session.add(ward)
            db.session.commit()

            bed = Bed(bed_number="SUR-201", ward_id=ward.id, bed_type="Oxygen", status="Available")
            db.session.add(bed)
            db.session.commit()

            data = bed.to_dict()
            assert data["bed_number"] == "SUR-201"
            assert data["ward_name"] == "Surgical Ward"
            assert data["bed_type"] == "Oxygen"
            assert data["status"] == "Available"
            assert "patient" not in data

            # Include patient when bed is available (should be None)
            data_with_patient = bed.to_dict(include_patient=True)
            assert data_with_patient["patient"] is None

    def test_patient_creation_and_to_dict(self, app):
        with app.app_context():
            patient = Patient(
                name="Ananya Roy",
                age=29,
                gender="Female",
                contact="9876543210",
                emergency_contact="9876543219",
                medical_condition="Fractured arm",
                priority="Normal",
                status="Admitted"
            )
            db.session.add(patient)
            db.session.commit()

            d = patient.to_dict()
            assert d["id"] == patient.id
            assert d["name"] == "Ananya Roy"
            assert d["age"] == 29
            assert d["gender"] == "Female"
            assert d["priority"] == "Normal"
            assert d["status"] == "Admitted"
            assert d["bed_number"] is None

    def test_admission_and_bed_patient_link(self, app):
        with app.app_context():
            ward = Ward(name="Emergency", ward_type="Emergency", floor=1)
            db.session.add(ward)
            db.session.commit()

            bed = Bed(bed_number="EME-105", ward_id=ward.id, status="Occupied")
            patient = Patient(name="Rohan Verma", age=40, gender="Male")
            db.session.add_all([bed, patient])
            db.session.commit()

            admission = Admission(patient_id=patient.id, bed_id=bed.id, notes="Acute fever")
            db.session.add(admission)
            db.session.commit()

            # Verify bed.current_patient() returns rohan
            current = bed.current_patient()
            assert current is not None
            assert current["name"] == "Rohan Verma"

            # Verify patient.to_dict() now contains bed and ward
            p_dict = patient.to_dict()
            assert p_dict["bed_number"] == "EME-105"
            assert p_dict["ward_name"] == "Emergency"

            # Verify admission.to_dict()
            adm_dict = admission.to_dict()
            assert adm_dict["patient_name"] == "Rohan Verma"
            assert adm_dict["bed_number"] == "EME-105"
            assert adm_dict["discharge_date"] is None

    def test_transfer_log_creation(self, app):
        with app.app_context():
            ward = Ward(name="General", ward_type="General_Male", floor=1)
            db.session.add(ward)
            db.session.commit()

            b1 = Bed(bed_number="GEN-01", ward_id=ward.id)
            b2 = Bed(bed_number="GEN-02", ward_id=ward.id)
            p = Patient(name="Test Patient", age=50, gender="Male")
            db.session.add_all([b1, b2, p])
            db.session.commit()

            tlog = TransferLog(
                patient_id=p.id,
                from_bed_id=b1.id,
                to_bed_id=b2.id,
                reason="Routine relocation"
            )
            db.session.add(tlog)
            db.session.commit()

            d = tlog.to_dict()
            assert d["patient_name"] == "Test Patient"
            assert d["from_bed"] == "GEN-01"
            assert d["to_bed"] == "GEN-02"
            assert d["reason"] == "Routine relocation"

    def test_cleaning_log_creation(self, app):
        with app.app_context():
            ward = Ward(name="ICU", ward_type="ICU", floor=2)
            db.session.add(ward)
            db.session.commit()

            bed = Bed(bed_number="ICU-10", ward_id=ward.id)
            db.session.add(bed)
            db.session.commit()

            clog = CleaningLog(bed_id=bed.id, status="Pending")
            db.session.add(clog)
            db.session.commit()

            d = clog.to_dict()
            assert d["bed_number"] == "ICU-10"
            assert d["ward_name"] == "ICU"
            assert d["status"] == "Pending"
            assert d["completed_at"] is None
