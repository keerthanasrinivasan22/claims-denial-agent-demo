import streamlit as st
import pandas as pd
import plotly.express as px
from utils.parser import parse_835_file

if st.button("Refresh Dashboard"):
    st.cache_data.clear()
    st.rerun()

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Claims Denial Agent",
    page_icon="🏥",
    layout="wide"
)

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    return pd.read_excel("data/claims.xlsx")

def save_claim_to_excel(new_claim):
    excel_path = "data/claims.xlsx"

    existing_df = pd.read_excel(excel_path)

    # Remove extra parser-only fields before saving
    claim_to_save = {
        "claim_id": new_claim["claim_id"],
        "patient_name": new_claim["patient_name"],
        "payer": new_claim["payer"],
        "denial_type": new_claim["denial_type"],
        "amount": new_claim["amount"],
        "priority": new_claim["priority"],
        "assigned_team": new_claim["assigned_team"],
        "status": new_claim["status"],
        "date_received": new_claim["date_received"],
        "potential_recovery": new_claim["potential_recovery"],
    }

    new_row = pd.DataFrame([claim_to_save])

    # Avoid duplicate claim_id
    existing_df["claim_id"] = existing_df["claim_id"].astype(str)
    claim_id = str(new_claim["claim_id"])

    if claim_id in existing_df["claim_id"].values:
        return False

    updated_df = pd.concat([existing_df, new_row], ignore_index=True)

    updated_df.to_excel(excel_path, index=False)

    return True

df = load_data()

# ---------------- CUSTOM STYLE ----------------
st.markdown("""
<style>
.main-title {
    font-size: 42px;
    font-weight: 800;
    color: #0B1F3A;
}
.subtitle {
    font-size: 18px;
    color: #5A6473;
    margin-bottom: 25px;
}
.metric-card {
    background: linear-gradient(135deg, #ffffff, #f3f7fb);
    padding: 22px;
    border-radius: 18px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}
.metric-label {
    font-size: 15px;
    color: #64748B;
    font-weight: 600;
}
.metric-value {
    font-size: 30px;
    color: #0B1F3A;
    font-weight: 800;
}
.section-header {
    font-size: 24px;
    font-weight: 750;
    color: #0B1F3A;
    margin-top: 25px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown('<div class="main-title">Claims Denial Agent</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">AI-powered revenue recovery dashboard for identifying, prioritizing, routing, and tracking denied claims.</div>',
    unsafe_allow_html=True
)

# ---------------- UPLOAD CENTER ----------------
st.markdown('<div class="section-header">Upload Center</div>', unsafe_allow_html=True)

st.info("Upload a sample 835 remittance file to simulate automatic denial intake.")

uploaded_file = st.file_uploader(
    "Upload 835 EDI File",
    type=["txt", "edi"]
)

if uploaded_file is not None:
    file_content = uploaded_file.read().decode("utf-8", errors="ignore")

    st.success("835 file uploaded successfully.")

    with st.expander("View uploaded file content"):
        st.text(file_content[:3000])

    st.markdown("### Parsed Claim Preview")

    new_claim = parse_835_file(file_content)
    saved = save_claim_to_excel(new_claim)

    if saved:
        st.success("Claim saved to Excel successfully. Dashboard is refreshing now.")
        st.cache_data.clear()
        st.rerun()
    else:
        st.warning("This claim already exists in Excel, so it was not added again.")

    st.dataframe(
        pd.DataFrame([new_claim]),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### AI Recommendation")

    st.success(f"""
    Denial Type: {new_claim["denial_type"]}  
    CARC Code: {new_claim["carc_code"]}  
    RARC Code: {new_claim["rarc_code"]}  
    Priority: {new_claim["priority"]}  
    Recommended Action: {new_claim["recommended_action"]}
    Assigned Team: {new_claim["assigned_team"]}  
    Potential Recovery: ${new_claim["potential_recovery"]:,.0f}
    """)

# ---------------- METRICS ----------------
total_claims = len(df)
total_denied_amount = df["amount"].sum()
potential_recovery = df["potential_recovery"].sum()
high_priority = len(df[df["priority"] == "High"])
open_claims = len(df[df["status"] != "Closed"])

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total Claims</div>
        <div class="metric-value">{total_claims}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Open Denials</div>
        <div class="metric-value">{open_claims}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Denied Amount</div>
        <div class="metric-value">${total_denied_amount:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Potential Recovery</div>
        <div class="metric-value">${potential_recovery:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">High Priority</div>
        <div class="metric-value">{high_priority}</div>
    </div>
    """, unsafe_allow_html=True)

# ---------------- CHARTS ----------------
st.markdown('<div class="section-header">Executive Insights</div>', unsafe_allow_html=True)

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    denial_counts = df.groupby("denial_type").size().reset_index(name="count")
    fig1 = px.pie(
        denial_counts,
        names="denial_type",
        values="count",
        title="Denials by Category",
        hole=0.45
    )
    st.plotly_chart(fig1, use_container_width=True)

with chart_col2:
    payer_amount = df.groupby("payer")["amount"].sum().reset_index()
    fig2 = px.bar(
        payer_amount,
        x="payer",
        y="amount",
        title="Denied Amount by Payer",
        text_auto=True
    )
    st.plotly_chart(fig2, use_container_width=True)

# ---------------- CLAIMS TABLE ----------------
st.markdown('<div class="section-header">Claims Work Queue</div>', unsafe_allow_html=True)

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)
