
"""
Syner-Med Regulatory Classifier — v3 (Training App)
- Trainer Mode, Case Picker auto-fill, GB/NI pathway, Checklist Builder
- Session Log with CSV/JSON export
- PDF export
"""

import io, json
import datetime as dt
import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

st.set_page_config(page_title="Syner-Med Regulatory Classifier", layout="wide")

# ---------------- Session State ----------------
if "log" not in st.session_state:
    st.session_state.log = []  # list of dicts

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("Syner-Med")
    trainer_mode = st.toggle("Trainer Mode (show tips)", value=False)
    st.divider()
    st.subheader("Quick Links (SOPs)")
    st.markdown("- Device Classification SOP (internal)")
    st.markdown("- Importer Verification Checklist (internal)")
    st.markdown("- PMS & Vigilance SOP (internal)")
    st.markdown("- DORS Registration Work Instruction (internal)")
    st.caption("Replace with your internal links in code.")
    st.divider()
    st.caption("Training tool only — not a formal regulatory determination.")

# ---------------- Header ----------------
st.markdown(
    """
    <div style="background:#1E88E5; padding:10px 16px; border-radius:8px;">
      <h2 style="margin:0; color:white;">Regulatory Classifier (Training)</h2>
    </div>
    """,
    unsafe_allow_html=True,
)

if trainer_mode:
    with st.expander("Trainer tips"):
        st.markdown("""
        - Use the **Case Picker** to show how the logic changes.
        - Emphasise **intended purpose** and **primary mode of action**.
        - Remind teams that **CE in GB** is transitional; **UKCA** is the long-term route.
        - GB vs **NI**: NI follows **EU MDR/IVDR**; UKCA alone is not valid there.
        """)

# ---------------- Case Picker ----------------
st.subheader("Pick a case or start blank")
case = st.selectbox(
    "Example cases",
    [
        "Start blank",
        "D.B.M. C-LOCK — sterile sodium citrate (IIb)",
        "Hyacyst® — sodium hyaluronate (IIa)",
        "Syner-KINASE® — urokinase (Medicinal)",
    ],
    index=0,
)

prefill = dict(medical_purpose=None, pharmacological=None, sterile=None, invasive_long=None, active_high_risk=None)
auto_name = ""
auto_notes = ""

if case == "D.B.M. C-LOCK — sterile sodium citrate (IIb)":
    prefill.update(dict(medical_purpose=True, pharmacological=False, sterile=True, invasive_long=True, active_high_risk=False))
    auto_name = "D.B.M. C-LOCK — sterile sodium citrate"
    auto_notes = (
        "Catheter lock solution to maintain CVC patency; anticoagulant function. "
        "Risk: sterile substance-based device; infection prevention and occlusion reduction claims. "
        "Likely Class IIb; NB assessment; PMS focus on infection/occlusion trends. "
        "GB: CE accepted during transition; DORS registration; UK importer on label; plan UKCA."
    )
elif case == "Hyacyst® — sodium hyaluronate (IIa)":
    prefill.update(dict(medical_purpose=True, pharmacological=False, sterile=True, invasive_long=False, active_high_risk=False))
    auto_name = "Hyacyst® — sodium hyaluronate (PFS 40mg/50ml; 120mg/50ml)"
    auto_notes = (
        "Bladder instillation; temporary replenishment of GAG layer. "
        "Presentation: pre-filled syringes. Likely Class IIa; NB assessment, clinical evaluation & biocompatibility. "
        "GB: CE accepted during transition; verify DoC scope for both strengths; DORS; importer label; plan UKCA."
    )
elif case == "Syner-KINASE® — urokinase (Medicinal)":
    prefill.update(dict(medical_purpose=True, pharmacological=True, sterile=False, invasive_long=False, active_high_risk=False))
    auto_name = "Syner-KINASE® — urokinase"
    auto_notes = (
        "Thrombolytic enzyme for catheter thrombolysis and thromboembolic disease. "
        "Pharmacological MoA → Medicinal product: MHRA MA; GDP; QPPV/PSMF; QP release; recall readiness."
    )

# ---------------- Questionnaire ----------------
st.subheader("1) Product purpose & mode of action")
mp_default = 1 if prefill["medical_purpose"] else 0 if prefill["medical_purpose"] is not None else 0
medical_purpose = st.radio("Does the product have a medical purpose (diagnose, monitor, treat)?", ["No","Yes"], index=mp_default)

if medical_purpose == "No":
    therapy_claims = st.radio("Does it imply therapeutic effects (healing, prevention, treatment)?", ["No","Yes"])
    result = "Cosmetic (likely) — UK Cosmetics Regs: UK RP, PIF, SCPN, labelling." if therapy_claims == "No" else "Reassess: likely a medical device or medicinal product based on mode of action."
    st.info(f"**Provisional outcome:** {result}")
    outcome_text = result
    outcome_kind = "Cosmetic"
else:
    ph_default = 1 if prefill["pharmacological"] else 0 if prefill["pharmacological"] is not None else 0
    pharmacological = st.radio("Is the primary mode of action pharmacological/immunological/metabolic?", ["No","Yes"], index=ph_default)

    if pharmacological == "Yes":
        st.success("**Likely a Medicinal Product** → MHRA MA; GDP; QPPV/PSMF; MIA(IMP)/WDA(H).")
        outcome_text = "Outcome: Likely **Medicinal Product** → MHRA MA; GDP; QPPV/PSMF; MIA(IMP)/WDA(H)."
        outcome_kind = "Medicine"
    else:
        st.subheader("2) Device attributes (provisional class)")
        sterile = st.checkbox("Supplied sterile or measuring function", value=bool(prefill["sterile"]) if prefill["sterile"] is not None else False)
        invasive_long = st.checkbox("Invasive and intended for long-term use or critical anatomy", value=bool(prefill["invasive_long"]) if prefill["invasive_long"] is not None else False)
        active_high_risk = st.checkbox("Active device monitoring vital parameters where variation may be immediately dangerous", value=bool(prefill["active_high_risk"]) if prefill["active_high_risk"] is not None else False)

        if active_high_risk or invasive_long:
            device_class = "Class IIb/III (seek detailed rule assessment)"
        elif sterile:
            device_class = "Class Is/Im/Ir or IIa (depending on intended use)"
        else:
            device_class = "Class I (if non-sterile, non-measuring, non-reusable instrument)"

        st.success(f"**Likely a Medical Device** → Provisional class: **{device_class}**")
        outcome_text = f"Outcome: Likely **Medical Device** — provisional class: {device_class}"
        outcome_kind = "Device"

# ---------------- GB/NI Pathway Guidance + Checklist Builder ----------------
st.subheader("GB/NI Pathway & Checklist")

def checklist_for(kind, device_class=None):
    if kind == "Medicine":
        return [
            "MHRA Marketing Authorisation (MA) or Specials route",
            "QPPV & PSMF in place; PV system operational",
            "GDP-compliant wholesale: WDA(H); import: MIA(IMP) & QP release (if applicable)",
            "Labelling & SmPC compliance; serialization/falsified-medicine safeguards (as applicable)",
            "Recall plan & batch traceability",
        ]
    if kind == "Cosmetic":
        return [
            "Appoint UK Responsible Person (RP)",
            "Prepare Product Information File (PIF)",
            "Notify in SCPN before first supply",
            "INCI labelling, claims substantiation, and ingredient compliance",
            "Importer details on packaging; storage/transport controls",
        ]
    # Device
    base = [
        "Assign risk class & confirm intended purpose wording",
        "If manufacturer outside UK: appoint UK Responsible Person (UKRP)",
        "Register with MHRA (DORS) before supply in GB",
        "Add GB importer (Syner-Med) details to label/pack or accompanying doc",
        "Maintain PMS plan, vigilance reporting, complaints & CAPA",
    ]
    if device_class and ("IIb" in device_class or "III" in device_class or "Is" in device_class or "Im" in device_class or "Ir" in device_class or "IIa" in device_class):
        base.insert(1, "Engage Approved/Notified Body for conformity assessment")
    base.append("For NI: ensure CE (or CE+UKNI) — UKCA alone not valid in NI")
    return base

device_class_display = locals().get("device_class", None)
items = checklist_for(outcome_kind, device_class_display)

for i, item in enumerate(items, 1):
    st.markdown(f"- {i}. {item}")

# ---------------- PDF Export ----------------
st.subheader("Export your answers to PDF")

default_name = (auto_name if auto_name else (case if case != "Start blank" else ""))
product_name = st.text_input("Product name (header on PDF)", value=default_name)

default_notes = (auto_notes if auto_notes else "")
notes = st.text_area("Notes / rationale to include in the PDF", value=default_notes)

def make_pdf(name, outcome_text, notes_text, checklist_lines):
    buff = io.BytesIO()
    c = canvas.Canvas(buff, pagesize=A4)
    w, h = A4
    x, y = 20*mm, h - 20*mm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(x, y, "Syner-Med Regulatory Classifier — Training Summary")

    c.setFont("Helvetica", 10)
    c.drawString(x, y - 16, f"Date: {dt.datetime.now():%Y-%m-%d %H:%M}")
    c.drawString(x, y - 30, f"Product: {name or 'N/A'}")

    # Outcome
    text = c.beginText(x, y - 52)
    text.setFont("Helvetica", 11)
    for line in outcome_text.splitlines():
        text.textLine(line)
    c.drawText(text)

    # Checklist
    text3 = c.beginText(x, y - 100)
    text3.setFont("Helvetica-Bold", 11)
    text3.textLine("Checklist")
    text3.setFont("Helvetica", 10)
    for idx, line in enumerate(checklist_lines, 1):
        text3.textLine(f"{idx}. {line}")
    c.drawText(text3)

    # Notes
    if notes_text:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x, y - 250, "Notes / Rationale")
        text2 = c.beginText(x, y - 268)
        text2.setFont("Helvetica", 10)
        import textwrap
        for line in textwrap.wrap(notes_text, width=100):
            text2.textLine(line)
        c.drawText(text2)

    c.showPage()
    c.save()
    buff.seek(0)
    return buff

pdf_data = make_pdf(product_name, outcome_text, notes, items)
st.download_button("Download PDF summary", data=pdf_data, file_name="syner-med_training_summary.pdf", mime="application/pdf")

# ---------------- Session Log & Exports ----------------
st.subheader("Session log & exports")

def current_record():
    rec = {
        "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
        "product_name": product_name,
        "case": case,
        "outcome_kind": outcome_kind,
        "outcome_text": outcome_text,
        "device_class": device_class_display or "",
        "notes": notes,
    }
    return rec

colA, colB, colC = st.columns([1,1,1])
if colA.button("Add to session log"):
    st.session_state.log.append(current_record())

if colB.button("Export single record (CSV)"):
    import csv
    from io import StringIO
    rec = current_record()
    csvbuf = StringIO()
    writer = csv.DictWriter(csvbuf, fieldnames=list(rec.keys()))
    writer.writeheader()
    writer.writerow(rec)
    st.download_button("Download current.csv", data=csvbuf.getvalue(), file_name="current_record.csv", mime="text/csv")

if colC.button("Clear session log"):
    st.session_state.log.clear()

if st.session_state.log:
    df = pd.DataFrame(st.session_state.log)
    st.dataframe(df, use_container_width=True)
    csv_all = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download session log (CSV)", data=csv_all, file_name="session_log.csv", mime="text/csv")
    json_all = json.dumps(st.session_state.log, indent=2).encode("utf-8")
    st.download_button("Download session log (JSON)", data=json_all, file_name="session_log.json", mime="application/json")

# ---------------- Glossary ----------------
with st.expander("Glossary (quick reference)"):
    st.markdown("""
    - **UKRP** — UK Responsible Person (for non-UK manufacturers)
    - **DORS** — MHRA Device Online Registration System
    - **PMS** — Post-Market Surveillance
    - **FSCA** — Field Safety Corrective Action
    - **MA** — Marketing Authorisation (Medicines)
    - **QPPV/PSMF** — Qualified Person for PV / Pharmacovigilance System Master File
    - **WDA(H)/MIA(IMP)** — Wholesale Distribution Authorisation (Human) / Manufacturer’s Import Authorisation
    - **CE/UKCA/UKNI** — Conformity marks (EU/GB/NI contexts)
    """)

st.caption("© Syner-Med training — always consult current MHRA guidance and your Notified/Approved Body.")
