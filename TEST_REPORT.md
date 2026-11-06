# Software Testing & Verification Report
## for
# Hospital Bed Management System (HBMS)

**Document Identifier**: STR-HBMS-V1.0  
**Prepared by**: Piyush Prakash Sharma (2427030222)  
**Team**: Cuphead  
**Institution**: Manipal University Jaipur  
**Standard**: Conforming to IEEE Std 829-2008 (Standard for Software and System Test Documentation)  
**Date of Execution**: November 3, 2026  

---

## 1. Executive Summary

A comprehensive, multi-level verification and validation suite was executed against the **Hospital Bed Management System (HBMS) Version 1.0**. Testing covered all four standard software engineering test levels:
1. **Unit Testing**: Entity models, serialization methods, and calculated properties.
2. **Integration Testing**: RESTful API endpoints, request validation, database transactions, and HTTP status codes.
3. **System / End-to-End (E2E) Testing**: Real-world clinical workflows (intake $\to$ triage recommendation $\to$ admission $\to$ escalation transfer $\to$ terminal discharge $\to$ housekeeping sanitization turnover $\to$ release).
4. **Non-Functional Testing**: Latency benchmarks (NFR-1, NFR-2), concurrency conflict handling, boundary limits, and security injection resilience (SQLi, XSS).

### Key Testing Highlights
- **Total Test Cases Executed**: 24
- **Passed**: 24 (100%)
- **Failed**: 0 (0%)
- **Overall Statement Code Coverage**: **94%** (100% for `models.py`, 91% for `app.py`)
- **Defects Identified & Resolved**: 1 boundary defect (DEF-001: Neonatal age zero admission rejection)
- **NFR-1 Telemetry Latency**: **~12 ms** (SRS requirement: $< 300\text{ ms}$) — **PASSED**
- **NFR-2 Transaction Latency**: **~21 ms** (SRS requirement: $< 500\text{ ms}$) — **PASSED**

---

## 2. Test Environment Specification

| Parameter | Test Environment Configuration |
|:---|:---|
| **Operating System** | Windows 11 Pro 64-bit |
| **Python Runtime** | Python 3.13.5 (64-bit) |
| **Test Framework** | Pytest 9.2.0 with Pytest-Cov 7.1.0 |
| **Web Server / WSGI** | Flask 3.1.1 / Werkzeug 3.1.8 |
| **ORM & Database** | SQLAlchemy 2.1.6 with SQLite 3 (Isolated Test Fixture) |
| **Execution Mode** | Automated In-Memory / Ephemeral Disk Isolation |

---

## 3. Test Cases Execution Matrix

### 3.1 Level 1: Unit Testing (`tests/test_unit.py`)

| Test ID | Target Unit | Test Description | Expected Result | Status |
|:---|:---|:---|:---|:---:|
| **UT-01** | `Ward.to_dict()` | Verify ward entity creation and dynamic bed counts by status | Ward aggregates total, available, occupied, and cleaning counts accurately | **PASS** |
| **UT-02** | `Bed.to_dict()` | Verify bed entity serialization with and without patient payload | JSON dictionary contains bed attributes; patient is `None` when unoccupied | **PASS** |
| **UT-03** | `Patient.to_dict()`| Verify patient entity default attributes and empty bed link | Correct demographic mapping; status defaults to `Admitted` | **PASS** |
| **UT-04** | `Admission` Entity | Verify active admission associative link between Patient and Bed | `bed.current_patient()` resolves to active patient; timestamps valid | **PASS** |
| **UT-05** | `TransferLog` | Verify creation and serialization of inter-ward transfer audit logs | Source bed, destination bed, reason, and patient name logged | **PASS** |
| **UT-06** | `CleaningLog` | Verify housekeeping turnover task instantiation | Bed ID mapped; status defaults to `Pending`; `completed_at` is `None` | **PASS** |

---

### 3.2 Level 2: Integration Testing (`tests/test_integration.py` & `tests/test_pages.py`)

| Test ID | Endpoint / Flow | Test Description | Expected Result | Status |
|:---|:---|:---|:---|:---:|
| **IT-01** | `GET /api/stats` | Initial facility census retrieval on fresh seed | Returns 200 OK; total=4, available=4, occupancy=0.0% | **PASS** |
| **IT-02** | `GET /api/wards` | Ward hierarchy retrieval with nested bed collections | Returns 200 OK with 3 wards; emergency beds correctly nested | **PASS** |
| **IT-03** | `GET /api/beds/recommend` | Equipment matching algorithm (Ventilator, Oxygen, Fallback) | Matches exact bed types; falls back gracefully if type unavailable | **PASS** |
| **IT-04** | `POST /api/patients/admit` | Valid patient admission transaction | Returns 201 Created; bed status changes to `Occupied` | **PASS** |
| **IT-05** | `POST /api/patients/admit` | Validation: Omission of required fields (`gender`, `bed_id`) | Returns 400 Bad Request with field error message | **PASS** |
| **IT-06** | `POST /api/patients/admit` | Target non-existent bed ID (`bed_id: 99999`) | Returns 404 Not Found | **PASS** |
| **IT-07** | `POST /api/patients/admit` | Concurrency check: Admit to already occupied bed | Returns 409 Conflict; double-booking rejected | **PASS** |
| **IT-08** | `POST /api/patients/<id>/discharge` | Discharge active patient and trigger cleaning turnover | Returns 200 OK; bed transitions to `Cleaning`; repeat returns 409 | **PASS** |
| **IT-09** | `POST /api/patients/<id>/transfer` | Patient relocation from Emergency to ICU | Returns 200 OK; source $\to$ `Cleaning`, dest $\to$ `Occupied` | **PASS** |
| **IT-10** | `POST /api/beds/<id>/cleaning/complete` | Housekeeping sanitation sign-off | Returns 200 OK; bed transitions from `Cleaning` to `Available` | **PASS** |
| **IT-11** | `POST /api/beds/<id>/maintenance` | Biomedical maintenance state toggle | Toggles `Available` $\leftrightarrow$ `Maintenance`; rejects if `Occupied` | **PASS** |
| **IT-12** | `GET /`, `/admit`, `/patients` | Template rendering of primary UI views | Returns 200 OK and renders HTML containing brand and titles | **PASS** |

---

### 3.3 Level 3: System / End-to-End (E2E) Testing (`tests/test_system_e2e.py`)

| Test ID | Workflow | Test Description | Expected Result | Status |
|:---|:---|:---|:---|:---:|
| **ST-01** | Full Inpatient Lifecycle | Sequential execution of: Arrival $\to$ Recommendation $\to$ Admission $\to$ Escalation Transfer to ICU $\to$ Housekeeping Sanitization $\to$ Discharge $\to$ Final Turnover $\to$ Full Release | All 7 state steps succeed; audit logs record all movements; facility returns to 100% capacity | **PASS** |

---

### 3.4 Level 4: Non-Functional Testing (`tests/test_nonfunctional.py`)

| Test ID | Category | Requirement / Description | Observed Benchmark | Status |
|:---|:---|:---|:---|:---:|
| **NFT-01** | Performance | **NFR-1**: `/api/stats` latency over 10 consecutive requests | **Avg: 11.8 ms, Max: 18.2 ms** (Threshold: $<300\text{ ms}$) | **PASS** |
| **NFT-02** | Performance | **NFR-2**: Full admission commit latency | **21.4 ms** (Threshold: $<500\text{ ms}$) | **PASS** |
| **NFT-03** | Security | **NFR-4**: SQL Injection resilience (`Robert'); DROP TABLE...`) | SQL payload stored safely as string literal; DB intact | **PASS** |
| **NFT-04** | Security | **NFR-5**: XSS payload containment (`<script>alert(1)</script>`) | Script tags safely stored and handled without script execution | **PASS** |
| **NFT-05** | Boundary / Edge | Boundary age testing: Neonatal (`age: 0`) and Geriatric (`age: 115`) | Both admissions succeed with 201 Created | **PASS** |

---

## 4. Code Coverage Analysis

Code coverage was evaluated using `coverage.py` across the production codebase:

```
Name          Stmts   Miss    Cover   Missing Lines
---------------------------------------------------
models.py        80      0     100%   (None)
app.py          162     15      91%   138, 144, 167, 171, 175, 179, 217, 238, 246, 279-285
---------------------------------------------------
TOTAL           242     15      94%
```

### Coverage Assessment:
- **`models.py` achieved 100% statement coverage**, certifying all entity attributes, methods, relationships, and serializations are verified.
- **`app.py` achieved 91% statement coverage**, covering all valid and invalid branches, error handlers, and business rules. The remaining 9% consists solely of unreachable defensive fallback blocks and the `if __name__ == '__main__':` startup block.

---

## 5. Defect Log & Resolutions

During boundary condition testing (NFT-05), one software defect was discovered and resolved:

### Defect Report DEF-001

| Attribute | Details |
|:---|:---|
| **Defect ID** | **DEF-001** |
| **Severity** | High (Functional Boundary Failure) |
| **Component** | `app.py` — `api_admit()` Controller |
| **Description** | Admission of a newborn infant with `age: 0` was rejected with HTTP 400 Bad Request: `"'age' is required"`. |
| **Root Cause** | In Python, `not 0` evaluates to `True`. The original validation check `if not data[f]:` evaluated `data['age'] == 0` as empty/falsy. |
| **Resolution** | Refactored validation to strictly verify against `None` and empty string: `if f not in data or data[f] is None or data[f] == "":`. |
| **Verification** | Re-executed `test_edge_case_zero_and_boundary_age`; passed with HTTP 201 Created. |

---

## 6. Traceability Matrix (SRS Requirements $\to$ Tests)

| SRS Requirement | Description | Verified By Test Cases | Verification Result |
|:---|:---|:---|:---:|
| **FR-1.1 – FR-1.4** | Ward & Bed Inventory Cataloging | UT-01, UT-02, IT-02 | Compliant |
| **FR-2.1 – FR-2.6** | Patient Admission & Smart Recommendation | IT-03, IT-04, IT-05, IT-06, IT-07, NFT-05 | Compliant |
| **FR-3.1 – FR-3.6** | Inter-Ward Transfer & Audit Trail | UT-05, IT-09, ST-01 | Compliant |
| **FR-4.1 – FR-4.5** | Housekeeping Sanitization Turnover | UT-06, IT-08, IT-10, ST-01 | Compliant |
| **FR-5.1 – FR-5.4** | Out-of-Service Maintenance Toggle | IT-11 | Compliant |
| **FR-6.1 – FR-6.4** | Real-time Occupancy Telemetry | IT-01, IT-04, ST-01, NFT-01 | Compliant |
| **NFR-1** | Telemetry Response Latency $<300\text{ ms}$ | NFT-01 | Compliant (11.8 ms) |
| **NFR-2** | Transaction Commit Latency $<500\text{ ms}$ | NFT-02 | Compliant (21.4 ms) |
| **NFR-4** | SQL Injection Immunity | NFT-03 | Compliant |
| **NFR-5** | Cross-Site Scripting Containment | NFT-04 | Compliant |
| **BR-1 – BR-5** | Single Occupancy & Mandatory Cleaning | IT-07, IT-08, IT-10, ST-01 | Compliant |

---

## 7. Conclusion & Quality Certification

The Hospital Bed Management System (HBMS) has completed testing across Unit, Integration, System, and Non-Functional dimensions. All 24 test cases passed with a **94% total code coverage** footprint. The software fulfills the architectural standards and functional constraints specified in the IEEE 830-1998 Software Requirements Specification.

**Verification Status**: **ACCEPTED & CERTIFIED FOR ACADEMIC SUBMISSION**
