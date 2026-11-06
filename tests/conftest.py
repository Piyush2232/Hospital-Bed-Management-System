import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app as flask_app
from models import db, Ward, Bed, Patient, Admission, TransferLog, CleaningLog

TEST_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_hospital.db"))

@pytest.fixture
def app():
    # Configure dedicated test database
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{TEST_DB_PATH}",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    })
    
    with flask_app.app_context():
        db.engine.dispose()
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()
        db.engine.dispose()

    # Clean up test database file
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def seeded_db(app):
    with app.app_context():
        w1 = Ward(name="Emergency Ward", ward_type="Emergency", floor=1)
        w2 = Ward(name="ICU - Block A", ward_type="ICU", floor=2)
        w3 = Ward(name="General Ward - Male", ward_type="General_Male", floor=1)
        db.session.add_all([w1, w2, w3])
        db.session.commit()

        b1 = Bed(bed_number="EME-101", ward_id=w1.id, bed_type="Standard", status="Available")
        b2 = Bed(bed_number="EME-102", ward_id=w1.id, bed_type="Oxygen", status="Available")
        b3 = Bed(bed_number="ICU-201", ward_id=w2.id, bed_type="Ventilator", status="Available")
        b4 = Bed(bed_number="GEN-101", ward_id=w3.id, bed_type="Standard", status="Available")
        db.session.add_all([b1, b2, b3, b4])
        db.session.commit()

        return {
            "ward_ids": [w1.id, w2.id, w3.id],
            "bed_ids": [b1.id, b2.id, b3.id, b4.id],
            "beds_data": [b1.to_dict(), b2.to_dict(), b3.to_dict(), b4.to_dict()]
        }
