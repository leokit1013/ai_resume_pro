import streamlit as st
from config import BACKEND_URL
import requests

st.set_page_config(page_title="Payment Cancelled", layout="centered")

if "token" not in st.session_state:
    st.switch_page("login.py")

res = requests.post(f"{BACKEND_URL}/validate-token", json={"token": st.session_state["token"]})
if res.status_code != 200:
    st.switch_page("login.py")




st.warning("⚠️ Payment Cancelled")

st.markdown("""
Your payment was cancelled. You can go back and try again if you wish to subscribe.

👉 [Go to Subscription Page](pages/payment_page.py)
""")
