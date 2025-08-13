import streamlit as st
import requests
from tools.auth_utils import (
    create_user_table, add_user, authenticate_user, get_user
)
from streamlit_extras.switch_page_button import switch_page
from config import BACKEND_URL  # make sure this is imported

create_user_table()

# Validate JWT from session_state on page load
if "token" in st.session_state:
    response = requests.post(f"{BACKEND_URL}/validate-token", json={"token": st.session_state["token"]})
    if response.status_code == 200:
        switch_page("Home")  # Already logged in
    else:
        del st.session_state["token"]  # Remove invalid token

st.title("🔐 Login to Smart Career Tools")

form_type = st.radio("Select Option", ["Login", "Sign Up"])
email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Continue"):
    if form_type == "Sign Up":
        try:
            add_user(email, password)
            st.success("Account created. Please login.")
        except:
            st.error("Email already registered.")
    else:
        if authenticate_user(email, password):
            # Local DB lookup for usage/subscription
            usage, subscribed = get_user(email)
            st.session_state["email"] = email
            st.session_state["usage_count"] = usage
            st.session_state["subscribed"] = bool(subscribed)

            # 🔐 Request backend to issue JWT
            try:
                res = requests.post(f"{BACKEND_URL}/generate-token", json={
                    "email": email,
                    "subscribed": bool(subscribed)
                })
                if res.status_code == 200:
                    st.session_state["token"] = res.json()["token"]
                    switch_page("Home")
                else:
                    st.error("Login succeeded but token failed.")
            except Exception as e:
                st.error(f"Token error: {e}")
        else:
            st.error("Invalid credentials")
