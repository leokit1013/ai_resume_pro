import streamlit as st
from tools import update_usage, get_user
from config import BACKEND_URL
import requests

st.set_page_config(page_title="Smart Career Tools", layout="wide")

if "token" not in st.session_state:
    st.switch_page("login.py")

res = requests.post(f"{BACKEND_URL}/validate-token", json={"token": st.session_state["token"]})
if res.status_code != 200:
    st.switch_page("login.py")


# hide navbar and footer
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)



# --- Require Login ---
if "email" not in st.session_state:
    st.warning("Please login to access this page.")
    st.switch_page("app.py" )

# --- Sync user state from DB ---
if "usage_count" not in st.session_state or "subscribed" not in st.session_state:
    user_info = get_user(st.session_state.email)
    if user_info:
        st.session_state.usage_count = user_info[0]
        st.session_state.subscribed = bool(user_info[1])
    else:
        st.error("User not found. Please login again.")
        st.switch_page("pages/login.py")

# --- Gatekeeper Function ---
def usage_gate():
    return True  # For now, always allow access

    # if st.session_state.subscribed:
    #     return True
    # elif st.session_state.usage_count < 2:
    #     update_usage(st.session_state.email)
    #     st.session_state.usage_count += 1
    #     return True
    # else:
    #     return False

# --- CSS Styling ---
st.markdown(
    """
    <style>
        .title {
            font-size: 3em;
            text-align: center;
            font-weight: bold;
            margin-bottom: 0;
        }
        .subtitle {
            text-align: center;
            font-size: 1.3em;
            color: #555;
        }
        .tool-card {
            background-color: #f8f9fa;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            transition: transform 0.2s ease-in-out;
        }
        .tool-card:hover {
            transform: scale(1.03);
            box-shadow: 0 6px 16px rgba(0,0,0,0.08);
        }
        .tool-title {
            font-size: 1.2em;
            font-weight: 600;
            margin-top: 15px;
        }
        .tool-desc {
            font-size: 0.95em;
            color: #555;
            margin-bottom: 15px;
        }
        .tool-button {
            background-color: #ff4b4b;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 0.95em;
            cursor: pointer;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(f"<div class='title'>🚀 Welcome to Smart Career Tools {st.session_state.email.split('@')[0].title()}!</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Your personalized suite for career growth and productivity</div>", unsafe_allow_html=True)
st.write("")  # spacing


col1, col2, col3 = st.columns(3)

# --- Tool Cards ---
with col1:
    st.markdown("<div style='text-align: center; font-size: 50px;'>📝</div>", unsafe_allow_html=True)
    st.markdown("<div class='tool-title'>Create Resume From Scratch</div>", unsafe_allow_html=True)
    st.markdown("<div class='tool-desc'>Craft professional resumes from zero using AI-enhanced insights.</div>", unsafe_allow_html=True)
    if st.button("Open Tool 1 ➡️", key="tool1"):
        if usage_gate():
            st.switch_page("pages/1_Create_Resume_From_Scratch.py")
        else:
            st.warning("You've used your 2 free accesses. Please subscribe to continue.")
            st.switch_page("payment_page.py")

with col2:
    st.markdown("<div style='text-align: center; font-size: 50px;'>✨</div>", unsafe_allow_html=True)
    st.markdown("<div class='tool-title'>Enhance Existing Resume</div>", unsafe_allow_html=True)
    st.markdown("<div class='tool-desc'>Improve your existing resume for better ATS ranking.</div>", unsafe_allow_html=True)
    if st.button("Open Tool 2 ➡️", key="tool2"):
        if usage_gate():
            st.switch_page("pages/2_Enhance_Existing_Resume.py")
        else:
            st.warning("You've used your 2 free accesses. Please subscribe to continue.")
            st.switch_page("payment_page.py")

with col3:
    st.markdown("<div style='text-align: center; font-size: 50px;'>📄</div>", unsafe_allow_html=True)
    st.markdown("<div class='tool-title'>Check & Fix Against JD</div>", unsafe_allow_html=True)
    st.markdown("<div class='tool-desc'>Optimize your resume against a specific job description.</div>", unsafe_allow_html=True)
    if st.button("Open Tool 3 ➡️", key="tool3"):
        if usage_gate():
            st.switch_page("pages/3_Check_And_Fix_Against_JD.py")
        else:
            st.warning("You've used your 2 free accesses. Please subscribe to continue.")
            st.switch_page("payment_page.py")