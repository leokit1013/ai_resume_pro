import streamlit as st
from config import BACKEND_URL
import requests

st.set_page_config(page_title="Payment Successful", layout="centered")

if "token" not in st.session_state:
    st.switch_page("login.py")

res = requests.post(f"{BACKEND_URL}/validate-token", json={"token": st.session_state["token"]})
if res.status_code != 200:
    st.switch_page("login.py")




st.success("🎉 Payment Successful!")

st.markdown("""
Thank you for subscribing! You now have full access to all Smart Career Tools features.

👉 Use the sidebar to explore your unlocked tools.
""")

# Optional: Set a session variable
st.session_state['is_subscribed'] = True
