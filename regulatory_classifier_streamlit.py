
"""
Syner-Med Regulatory Classifier — Enhanced Training App (Web-Ready)
Branding, Case Picker, Decision Tree, PDF export, SOP links.
Entry file for Streamlit Cloud: regulatory_classifier_streamlit.py
"""

import io
import datetime as dt
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import matplotlib.pyplot as plt

st.set_page_config(page_title="Syner-Med Regulatory Classifier", layout="wide")

# ---------- Sidebar (branding & SOP links) ----------
with st.sidebar:
    st.header("Syner-Med")
    logo = st.file_uploader("Upload logo (PNG, optional)", type=["png"])
    st.markdown("**UK Regulatory Training Suite**")
    st.caption("Medical Devices • Medicines • Cosmetics")
    st.divider()
    st.subheader("Quick Links (SOPs)")
    st.markdown("- Device Classification SOP (internal)")
    st.markdown("- Importer Verification Checklist (internal)")
    st.markdown("- PMS & Vigilance SOP (internal)")
    st.markdown("- DORS Registration Work Instruction (internal)")
    st.caption("Replace with real links in code.")
    st.divider()
    st.caption("Training tool only — not a formal regulatory determination.")

# ---------- Header ----------
c1, c2 = st.columns([1,4])
if logo:
    c1.image(logo, use_column_width=True)
else:
    c1.markdown("### Syner-Med")

c2.markdown("# Regulatory Classifier (Training)")
c2.write("Answer a few questions to get a training-level indication of classification and the GB market pathway.")

st.info("**Case Picker is right below.** Choose a product to auto-fill example answers, or leave as 'Start blank'.")

st.divider()

# ---------- Case Picker (prominent) ----------
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
    help="Use these preloaded cases to see how the logic behaves."
)

# Defaults
prefill = dict(medical_purpose=None, pharmacological=None, sterile=None, invasive_long=None, active_high_risk=None)
if case == "D.B.M. C-LOCK — sterile sodium citrate (IIb)":
    prefill.update(dict(medical_purpose=True, pharmacological=False, sterile=True, invasive_long=True, active_high_risk=False))
elif case == "Hyacyst® — sodium hyaluronate (IIa)":
    prefill.update(dict(medical_purpose=True, pharmacological=False, sterile=True, invasive_long=False, active_high_risk=False))
elif case == "Syner-KINASE® — urokinase (Medicinal)":
    prefill.update(dict(medical_purpose=True, pharmacological=True, sterile=False, invasive_long=False, active_high_risk=False))

# ---------- Questionnaire ----------
st.subheader("1) Product purpose & mode of action")
mp_default = 1 if prefill["medical_purpose"] else 0 if prefill["medical_purpose"] is not None else 0
medical_purpose = st.radio("Does the product have a medical purpose (diagnose, monitor, treat)?", ["No","Yes"], index=mp_default)

if medical_purpose == "No":
    therapy_claims = st.radio("Does it imply therapeutic effects (healing, prevention, treatment)?", ["No","Yes"])
    result = "Cosmetic (likely) — UK Cosmetics Regs: UK RP, PIF, SCPN, labelling." if therapy_claims == "No" else "Reassess: likely a medical device or medicinal product based on mode of action."
    st.info(f"**Provisional outcome:** {result}")
    st.stop()

ph_default = 1 if prefill["pharmacological"] else 0 if prefill["pharmacological"] is not None else 0
pharmacological = st.radio("Is the primary mode of action pharmacological/immunological/metabolic?", ["No","Yes"], index=ph_default)

if pharmacological == "Yes":
    st.success("**Likely a Medicinal Product** → MHRA MA; GDP; QPPV/PSMF; MIA(IMP)/WDA(H).")
    outcome_text = "Outcome: Likely **Medicinal Product** → MHRA MA; GDP; QPPV/PSMF; MIA(IMP)/WDA(H)."
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

# ---------- Decision Tree Visual ----------
st.subheader("Decision Tree (training visual)")
fig = plt.figure(figsize=(6,4))
plt.axis('off')
plt.text(0.05, 0.8, "Medical purpose?", fontsize=12, bbox=dict(boxstyle="round", fc="white"))
plt.text(0.5, 0.8, "No → Cosmetic (if no therapeutic claims)", fontsize=10)
plt.text(0.05, 0.6, "Pharmacological / immunological / metabolic MoA?", fontsize=12, bbox=dict(boxstyle="round", fc="white"))
plt.text(0.5, 0.6, "Yes → Medicine", fontsize=10)
plt.text(0.05, 0.4, "Device attributes", fontsize=12, bbox=dict(boxstyle="round", fc="white"))
plt.text(0.5, 0.4, "Sterile/Measuring? Invasive long-term? Active high-risk?\n→ Class I / Is/Im/Ir / IIa / IIb / III", fontsize=10)
st.pyplot(fig)

# ---------- GB Pathway Guidance ----------
st.subheader("GB Market Pathway (training)")
st.markdown("""
- **If CE-only**: MHRA DORS registration, appoint **UKRP** (if needed), **GB importer** on label, PMS; plan **UKCA**.
- **If no certification**: choose **UKCA/CE**, select Body, build **ISO 13485** technical file & clinical eval, **register before supply**.
- **If UKCA**: register with MHRA; for **NI**, **CE (or CE+UKNI)** still required.
- **MDD→MDR**: perform gap analysis, engage MDR-designated NB, update technical file & labels; maintain legacy route only if conditions met.
""")

# ---------- PDF Export ----------
st.subheader("Export your answers to PDF")
product_name = st.text_input("Product name (header on PDF)", value=case if case != "Start blank" else "")
notes = st.text_area("Notes / rationale to include in the PDF")

def make_pdf(name, outcome_text, notes_text):
    buff = io.BytesIO()
    c = canvas.Canvas(buff, pagesize=A4)
    w, h = A4
    x, y = 20*mm, h - 20*mm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(x, y, "Syner-Med Regulatory Classifier — Training Summary")

    c.setFont("Helvetica", 10)
    c.drawString(x, y - 16, f"Date: {dt.datetime.now():%Y-%m-%d %H:%M}")
    c.drawString(x, y - 30, f"Product: {name or 'N/A'}")

    text = c.beginText(x, y - 52)
    text.setFont("Helvetica", 11)
    for line in outcome_text.splitlines():
        text.textLine(line)
    c.drawText(text)

    if notes_text:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x, y - 140, "Notes / Rationale")
        text2 = c.beginText(x, y - 158)
        text2.setFont("Helvetica", 10)
        import textwrap
        for line in textwrap.wrap(notes_text, width=100):
            text2.textLine(line)
        c.drawText(text2)

    c.showPage()
    c.save()
    buff.seek(0)
    return buff

pdf_data = make_pdf(product_name, outcome_text, notes)
st.download_button("Download PDF summary", data=pdf_data, file_name="syner-med_training_summary.pdf", mime="application/pdf")

st.caption("Training tool only — always consult current MHRA guidance and your Notified/Approved Body.")
