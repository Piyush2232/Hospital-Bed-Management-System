# Hospital Bed Management System (HBMS)

> A 3-Tier MVC Web Application engineered for real-time hospital bed tracking, patient admission, inter-ward transfers, and automated sanitization turnover workflows.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask%203.1-green.svg)](https://flask.palletsprojects.com/)
[![Tests](https://img.shields.io/badge/Tests-24%20Passed-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/Coverage-94%25-success.svg)]()
[![Standard](https://img.shields.io/badge/SRS-IEEE%20Std%20830--1998-orange.svg)]()

---

## 📌 Project Overview

In healthcare facilities, bed-blocking, delayed discharge reporting, and communication gaps between clinical wards and housekeeping result in emergency department boarding and suboptimal bed utilization.

The **Hospital Bed Management System (HBMS)** provides:
- **Interactive Visual Bed Grid**: Color-coded, real-time bed status matrix across 6 clinical departments.
- **Finite State Machine Lifecycle**: Enforced transition: `Available` ➔ `Occupied` ➔ `Cleaning` ➔ `Available` (with optional `Maintenance`). Direct jumps from `Occupied` to `Available` are prohibited as an infection-control barrier.
- **Smart Triage Bed Recommendation**: Algorithmic matching based on clinical equipment requirements (Ventilator, Oxygen, Isolation, Standard).
- **Inter-Ward Patient Relocation**: One-click transfer workflow with automated audit logging.
- **Terminal Sanitization Sign-off**: Housekeeping turnover tracking before re-certifying beds as available.

---

## 🏛️ Architecture

The system implements a **3-Tier Model-View-Controller (MVC)** architecture:

```
[Presentation Tier / View]  <--->  [Application Tier / Controller]  <--->  [Data Tier / Model]
HTML5 + CSS + JavaScript           Python Flask (RESTful API)              SQLAlchemy ORM + SQLite
(Asynchronous Fetch DOM)           (State validation & routing)            (Relational schema)
```

- **Model Layer (`models.py`)**: 6 relational tables (`Ward`, `Bed`, `Patient`, `Admission`, `TransferLog`, `CleaningLog`) using SQLAlchemy ORM.
- **Controller Layer (`app.py`)**: Flask route handlers exposing RESTful endpoints with HTTP status codes (`200`, `201`, `400`, `404`, `409`).
- **View Layer (`templates/`, `static/`)**: Browser interface styled with Nothing-inspired design principles (monochrome surfaces, high contrast, Space Grotesk / Space Mono typography, zero shadows).

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/Piyush2232/Hospital-Bed-Management-System.git
cd Hospital-Bed-Management-System
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the application
```bash
python app.py
```
*Or on Windows, simply double-click `start_app.bat`.*

Open your browser at: **`http://127.0.0.1:5000`**

The database will be automatically created and pre-seeded with 6 wards, 38 beds, and 12 sample patients.

---

## 🧪 Testing & Verification

The project includes an automated test suite covering all four software engineering testing levels:
- **Unit Testing**: Entity models and serialization
- **Integration Testing**: All REST endpoints and HTTP status codes
- **System / E2E Testing**: Full inpatient lifecycle
- **Non-Functional Testing**: Latency benchmarks (NFR-1, NFR-2), SQL injection resilience, and boundary testing

### Run Tests:
```bash
pytest -v --cov=models --cov=app
```

**Results**:
- **Total Tests**: 24/24 Passed (100%)
- **Code Coverage**: 94% Total (100% `models.py`, 91% `app.py`)
- **Telemetry Latency (NFR-1)**: ~11.8 ms (SRS target: < 300 ms)
- **Transaction Latency (NFR-2)**: ~21.4 ms (SRS target: < 500 ms)

See [TEST_REPORT.md](TEST_REPORT.md) for the complete IEEE Std 829-2008 verification report.

---

## 📄 Documentation

- **Software Requirements Specification (SRS)**: See [SRS_Hospital_Bed_Management_System.md](SRS_Hospital_Bed_Management_System.md) conforming to IEEE Std 830-1998, complete with all 11 UML/analysis diagrams (Use Case, Class, Object, Package, Activity, Sequence, State Chart, Component, Deployment, DFD Level 0/1, ERD).
- **Software Test Documentation**: See [TEST_REPORT.md](TEST_REPORT.md) conforming to IEEE Std 829-2008.

---

## 👥 Authors
- **Piyush Prakash Sharma** (2427030222)
- **Ankur Rathi** (247030014)
- Team: **Cuphead**
- **Manipal University Jaipur**
