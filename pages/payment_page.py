import streamlit as st
import requests
from config import FRONTEND_DOMAIN, PLAN_MAP, BACKEND_URL
from config import BACKEND_URL
import requests

st.set_page_config(page_title="Subscribe Now", layout="centered")

if "token" not in st.session_state:
    st.switch_page("login.py")

res = requests.post(f"{BACKEND_URL}/validate-token", json={"token": st.session_state["token"]})
if res.status_code != 200:
    st.switch_page("login.py")

# --- Hide navbar and footer ---
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- Page Setup ---

st.title("💳 Subscribe to Unlock Full Access")
st.markdown(
    "You've reached your free usage limit. Choose a subscription plan and payment method to continue using all Smart Career Tools features."
)

# --- Plan Selection ---
plan_label = st.radio("Choose your plan:", list(PLAN_MAP.keys()))
selected_plan = PLAN_MAP[plan_label]

# --- Payment Method Selection ---
payment_method = st.radio("Select payment method:", ["Stripe", "Razorpay"])

# --- Payment Action ---
if st.button("Proceed to Payment 💳"):
    try:
        # Prepare API URL based on payment method
        endpoint = (
            f"{BACKEND_URL}/create-checkout-session"
            if payment_method == "Stripe"
            else f"{BACKEND_URL}/create-razorpay-session"
        )

        # Call backend
        response = requests.post(endpoint, json={"plan": selected_plan})

        # Handle response
        if response.status_code == 200:
            checkout_url = response.json().get("url")
            if checkout_url:
                st.success(f"Redirecting to {payment_method}...")
                st.markdown(
                    f'<meta http-equiv="refresh" content="0; URL={checkout_url}" />',
                    unsafe_allow_html=True,
                )
            else:
                st.error("No checkout URL returned by server.")
        else:
            st.error(f"Failed to create payment session: {response.text}")
    except Exception as e:
        st.error(f"An error occurred: {e}")
