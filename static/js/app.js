/* ═══════════════════════════════════════════════════════════
   Hospital Bed Management — Nothing Design Frontend JS
   ═══════════════════════════════════════════════════════════ */

// ─── Status Notifications (bracket-style) ───────────────────
function showToast(message, type = "success") {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => toast.classList.remove("show"), 3000);
}

// ─── Bed Detail Modal (Dashboard) ───────────────────────────
function openBedModal(bed) {
    const overlay = document.getElementById("modal-overlay");
    const modal   = document.getElementById("modal");
    const title   = document.getElementById("modal-title");
    const body    = document.getElementById("modal-body");

    title.textContent = bed.bed_number;

    let patientHTML = "";
    if (bed.patient) {
        const p = bed.patient;
        patientHTML = `
            <div style="border-top:1px solid var(--border);margin:16px 0;padding-top:16px;">
                <div style="font-family:'Space Mono',monospace;font-size:11px;letter-spacing:0.08em;text-transform:uppercase;color:var(--text-secondary);margin-bottom:12px;">CURRENT PATIENT</div>
                <div class="bed-detail-grid">
                    <div class="bed-detail-item"><label>NAME</label><p>${p.name}</p></div>
                    <div class="bed-detail-item"><label>AGE / GENDER</label><p>${p.age} / ${p.gender}</p></div>
                    <div class="bed-detail-item"><label>PRIORITY</label><p><span class="priority-badge ${p.priority.toLowerCase()}">${p.priority}</span></p></div>
                    <div class="bed-detail-item"><label>CONTACT</label><p>${p.contact || '—'}</p></div>
                </div>
                <div class="bed-detail-item" style="margin-top:8px;">
                    <label>CONDITION</label><p style="color:var(--text-secondary);">${p.medical_condition || '—'}</p>
                </div>
            </div>
        `;
    }

    let actionsHTML = '<div class="modal-actions">';
    if (bed.status === "Cleaning") {
        actionsHTML += `<button class="btn btn-primary" onclick="markCleaned(${bed.id})">MARK CLEANED</button>`;
    }
    if (bed.status === "Available") {
        actionsHTML += `<button class="btn" onclick="toggleMaintenance(${bed.id})">SET MAINTENANCE</button>`;
        actionsHTML += `<a href="/admit" class="btn btn-primary">ADMIT PATIENT</a>`;
    }
    if (bed.status === "Maintenance") {
        actionsHTML += `<button class="btn btn-primary" onclick="toggleMaintenance(${bed.id})">END MAINTENANCE</button>`;
    }
    if (bed.status === "Occupied" && bed.patient) {
        actionsHTML += `<button class="btn btn-danger" onclick="dischargeBed(${bed.patient.id}, '${bed.patient.name}')">DISCHARGE</button>`;
    }
    actionsHTML += '</div>';

    body.innerHTML = `
        <div class="bed-detail-grid">
            <div class="bed-detail-item"><label>WARD</label><p>${bed.ward_name}</p></div>
            <div class="bed-detail-item"><label>BED TYPE</label><p>${bed.bed_type}</p></div>
            <div class="bed-detail-item"><label>STATUS</label><p><span class="status-badge ${bed.status.toLowerCase()}">${bed.status}</span></p></div>
            <div class="bed-detail-item"><label>WARD TYPE</label><p>${bed.ward_type.replace('_',' ')}</p></div>
        </div>
        ${patientHTML}
        ${actionsHTML}
    `;

    overlay.style.display = "block";
    modal.style.display = "block";
}

function closeModal() {
    document.getElementById("modal-overlay").style.display = "none";
    document.getElementById("modal").style.display = "none";
}

// ─── Actions ────────────────────────────────────────────────
function markCleaned(bedId) {
    fetch(`/api/beds/${bedId}/cleaning/complete`, { method: "POST" })
    .then(r => r.json())
    .then(data => {
        showToast(data.error ? "[ERROR]" : "[CLEANED]", data.error ? "error" : "success");
        closeModal();
        if (typeof loadDashboard === "function") loadDashboard();
    });
}

function toggleMaintenance(bedId) {
    fetch(`/api/beds/${bedId}/maintenance`, { method: "POST" })
    .then(r => r.json())
    .then(data => {
        showToast(data.error ? "[ERROR]" : "[UPDATED]", data.error ? "error" : "success");
        closeModal();
        if (typeof loadDashboard === "function") loadDashboard();
    });
}

function dischargeBed(patientId, patientName) {
    if (!confirm('Discharge patient "' + patientName + '"? Bed will be sent for cleaning.')) return;
    fetch(`/api/patients/${patientId}/discharge`, { method: "POST" })
    .then(r => r.json())
    .then(data => {
        showToast(data.error ? "[ERROR]" : "[DISCHARGED]", data.error ? "error" : "success");
        closeModal();
        if (typeof loadDashboard === "function") loadDashboard();
    });
}
