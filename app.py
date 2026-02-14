import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import cloudinary
import cloudinary.uploader

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="CREDITS FIN SYSTEM", layout="wide")

# =========================
# CLOUDINARY CONFIG
# =========================
cloudinary.config(
    cloud_name=st.secrets["cloudinary"]["cloud_name"],
    api_key=st.secrets["cloudinary"]["api_key"],
    api_secret=st.secrets["cloudinary"]["api_secret"],
    secure=True
)

# =========================
# THEME (HEADER FIXED)
# =========================
st.markdown("""
<style>
.stApp { background: white; }

.main-title {
    color: #7b1e2b;
    font-size: 30px;
    font-weight: 800;
    text-align: center;
    margin-bottom: 5px;
}

button {
    background: #7b1e2b !important;
    color: white !important;
    border-radius: 4px !important;
    padding: 2px 8px !important;
    font-size: 12px !important;
    height: 28px !important;
}
button:hover { background: #5a1420 !important; }

.blue-link {
    color: blue;
    text-decoration: none;
    font-size: 12px;
    font-weight: 500;
}

.header-text {
    font-size: 14px !important;
    font-weight: 700 !important;
    color: #7b1e2b !important;
}

div[data-testid="column"] {
    padding-left: 4px !important;
    padding-right: 4px !important;
}

hr {
    margin: 4px 0px !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# GOOGLE SHEETS
# =========================
@st.cache_resource
def connect_sheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(
        "service_account.json", scopes=scope
    )
    client = gspread.authorize(creds)
    return client.open_by_key("1KVQsImewzbcPt5xGGKZWRw2_amILgsuFmt-On58gyac")

ss = connect_sheets()
branches_sheet = ss.worksheet("BRANCHES")
master_sheet = ss.worksheet("MASTER")
bids_sheet = ss.worksheet("BRANCH_BIDS")

branches = branches_sheet.col_values(1)[1:]

# =========================
# SESSION
# =========================
if "mode" not in st.session_state:
    st.session_state.mode = None

# =========================
# HEADER
# =========================
colA, colB = st.columns([1,6])

with colA:
    if st.button("← Home"):
        st.session_state.mode = None

with colB:
    st.markdown("<div class='main-title'>CREDITS FIN SYSTEM</div>", unsafe_allow_html=True)

st.divider()

# =========================
# MAIN BUTTONS
# =========================
c1, c2 = st.columns(2)

with c1:
    if st.button("FIN-CLOSE", use_container_width=True):
        st.session_state.mode = "finclose"

with c2:
    if st.button("PLACE-BID / OPEN DEALS", use_container_width=True):
        st.session_state.mode = "placebid"

# =========================
# FIN CLOSE
# =========================
if st.session_state.mode == "finclose":

    st.subheader("FIN-CLOSE")

    with st.form("finclose_form", clear_on_submit=True):
        branch = st.selectbox("Branch", branches)
        cname = st.text_input("Customer Name")
        cid = st.text_input("Customer ID")
        acc = st.text_input("Account Number")
        amt = st.number_input("Amount", step=1)
        scheme = st.text_input("Scheme Code")
        roi = st.number_input("ROI", step=0.1)
        mat = st.date_input("Maturity Date")
        put = st.date_input("Put Option Date")
        file = st.file_uploader("Certificate", type=["png","jpg","jpeg","pdf"])

        save = st.form_submit_button("SAVE")

        if save:
            if not all([branch, cname, cid, acc, amt, scheme, roi, mat, put, file]):
                st.error("All fields mandatory")
            else:
                upload = cloudinary.uploader.upload(
                    file,
                    folder="credits_fin_system",
                    resource_type="auto"
                )

                master_sheet.append_row([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "FIN-CLOSE",
                    branch,
                    cname,
                    cid,
                    acc,
                    amt,
                    scheme,
                    roi,
                    mat.strftime("%d-%m-%Y"),
                    put.strftime("%d-%m-%Y"),
                    upload["secure_url"],
                    "OPEN"
                ])

                st.success("Saved Successfully")

# =========================
# OPEN DEALS (DIRECT UPLOAD)
# =========================
if st.session_state.mode == "placebid":

    st.subheader("Open Deals")

    search = st.text_input("🔍 Search Customer / Account / Branch")

    data = master_sheet.get_all_records()
    open_deals = [d for d in data if str(d.get("Status","")).upper() == "OPEN"]

    if search:
        open_deals = [d for d in open_deals if search.lower() in str(d).lower()]

    if not open_deals:
        st.info("No open deals available")
    else:

        # Hide default uploader UI text
        st.markdown("""
        <style>
        div[data-testid="stFileUploader"] > div {
            display: none;
        }
        </style>
        """, unsafe_allow_html=True)

        width_ratio = [1.5,1.6,0.8,0.8,0.8,1,1,1.2,1.2,0.7,0.7,0.7]

        # Header
        header = st.columns(width_ratio)
        titles = [
            "Customer","Account","Amt","Scheme",
            "ROI","Maturity","Put","Branch",
            "Bid Branch","View","Upload","Bid"
        ]

        for col, title in zip(header, titles):
            col.markdown(f"**{title}**")

        st.markdown("<hr>", unsafe_allow_html=True)

        for i, row in enumerate(open_deals):

            cols = st.columns(width_ratio)

            cols[0].write(row.get("Customer Name",""))
            cols[1].write(row.get("Account Number",""))
            cols[2].write(row.get("Amount",""))
            cols[3].write(row.get("Scheme Code",""))
            cols[4].write(row.get("ROI",""))
            cols[5].write(row.get("Maturity Date",""))
            cols[6].write(row.get("Put Option Date",""))
            cols[7].write(row.get("Branch",""))

            bid_branch = cols[8].selectbox(
                "",
                branches,
                key=f"bb{i}",
                label_visibility="collapsed"
            )

            # View
            file_url = row.get("File Name","")
            if file_url:
                cols[9].markdown(
                    f"<a href='{file_url}' target='_blank' class='blue-link'>View</a>",
                    unsafe_allow_html=True
                )
            else:
                cols[9].write("-")

            # Hidden File Uploader
            bid_file = cols[10].file_uploader(
                "",
                type=["png","jpg","jpeg","pdf"],
                key=f"bf{i}",
                label_visibility="collapsed"
            )

            # Small Upload Button (just triggers)
            if cols[10].button("Upload", key=f"upload{i}"):
                pass  # just UI trigger

            # BID
            if cols[11].button("BID", key=f"bid{i}"):

                if not bid_file:
                    st.error("Please select file after clicking Upload")
                    st.stop()

                upload = cloudinary.uploader.upload(
                    bid_file,
                    folder="credits_fin_bids",
                    resource_type="auto"
                )

                latest = master_sheet.get_all_records()

                for idx, r in enumerate(latest, start=2):
                    if r.get("Account Number") == row.get("Account Number"):
                        if str(r.get("Status")).upper() != "OPEN":
                            st.error("Already taken by another branch")
                            st.stop()
                        master_sheet.update_cell(idx, 12, "BOOKED")
                        break

                bids_sheet.append_row([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    row.get("Customer Name",""),
                    row.get("Account Number",""),
                    row.get("Amount",""),
                    row.get("Scheme Code",""),
                    row.get("ROI",""),
                    row.get("Maturity Date",""),
                    row.get("Put Option Date",""),
                    row.get("Branch",""),
                    bid_branch,
                    upload["secure_url"]
                ])

                st.success("Bid placed successfully")
                st.rerun()

            st.markdown("<hr>", unsafe_allow_html=True)
