import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="secret.env")  # Load from secret.env file

# Stripe Keys
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PRICE_IDS = {
    "basic": os.getenv("STRIPE_BASIC_PRICE_ID", ""),
    "pro": os.getenv("STRIPE_PRO_PRICE_ID", ""),
    "premium": os.getenv("STRIPE_PREMIUM_PRICE_ID", "")
}

# Razorpay Keys
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_SECRET_KEY = os.getenv("RAZORPAY_SECRET_KEY", "")

# Domains
FRONTEND_DOMAIN = os.getenv("FRONTEND_DOMAIN", "http://localhost:8501")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")

# Plan label mapping
PLAN_MAP = {
    "Basic - ₹199/mo": "basic",
    "Pro - ₹499/mo": "pro",
    "Premium - ₹999/mo": "premium"
}

# config.py
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-jwt-key")
