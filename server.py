import hmac
import hashlib
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import stripe
import razorpay
import uuid
from flask import abort
import os
import json
import hmac
import hashlib
from config import STRIPE_SECRET_KEY, STRIPE_PRICE_IDS, RAZORPAY_KEY_ID, RAZORPAY_SECRET_KEY, FRONTEND_DOMAIN
from tools import create_payments_table, add_payment_record, generate_token, verify_token

create_payments_table()

app = Flask(__name__)
CORS(app)

# Stripe setup
stripe.api_key = STRIPE_SECRET_KEY

# Razorpay client
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_SECRET_KEY))

@app.route('/validate-token', methods=['POST'])
def validate_token():
    data = request.get_json()
    token = data.get("token")

    user_data = verify_token(token)
    if not user_data:
        return jsonify({"valid": False}), 401

    return jsonify({
        "valid": True,
        "email": user_data["email"],
        "subscribed": user_data["subscribed"]
    })

@app.route('/generate-token', methods=['POST'])
def generate_token_route():
    data = request.get_json()
    email = data.get("email")
    subscribed = data.get("subscribed", False)

    token = generate_token(email, subscribed)
    return jsonify({"token": token})


@app.route('/create-stripe-session', methods=['POST'])
def create_stripe_session():
    try:
        data = request.get_json()
        plan = data.get("plan")

        if plan not in STRIPE_PRICE_IDS:
            return jsonify({"error": "Invalid plan"}), 400

        session = stripe.checkout.Session.create(
            line_items=[{'price': STRIPE_PRICE_IDS[plan], 'quantity': 1}],
            mode='subscription',
            success_url=f"{FRONTEND_DOMAIN}/pages/payment_success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_DOMAIN}/pages/payment_cancelled"
        )
        return jsonify({'url': session.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/create-razorpay-order', methods=['POST'])
def create_razorpay_order():
    try:
        data = request.get_json()
        amount_inr = int(data.get("amount", 990))  # default ₹990
        email = data.get("email", "demo@example.com")

        order = razorpay_client.order.create({
            "amount": amount_inr * 100,  # in paise
            "currency": "INR",
            "receipt": f"receipt_{uuid.uuid4()}",
            "payment_capture": 1
        })

        return jsonify({
            "order_id": order["id"],
            "razorpay_key": RAZORPAY_KEY_ID,
            "amount": amount_inr * 100,
            "currency": "INR",
            "email": email
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400


STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")  # Add to .env

@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('stripe-signature')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        return jsonify({"error": "Invalid Stripe signature"}), 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session.get('customer_email')
        subscription_id = session.get('subscription')
        amount_total = session.get('amount_total', 0)

        # If using price_id-based plans
        line_items = session.get('display_items') or session.get('line_items')
        price_id = None
        if line_items:
            price_id = line_items[0].get('price', {}).get('id')

        # Fallback if plan can’t be determined
        plan = next((k for k, v in STRIPE_PRICE_IDS.items() if v == price_id), "unknown")

        print(f"✅ Stripe Payment Successful for {customer_email}, ₹{amount_total/100}, Plan: {plan}")

        # Save to DB
        add_payment_record(
            email=customer_email,
            gateway="stripe",
            amount=amount_total,
            status="completed",
            plan=plan,
            subscription_id=subscription_id
        )

    return jsonify({"status": "success"}), 200

RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")  # Add to .env

@app.route('/webhook/razorpay', methods=['POST'])
def razorpay_webhook():
    payload = request.data
    received_signature = request.headers.get('X-Razorpay-Signature')

    generated_signature = hmac.new(
        bytes(RAZORPAY_WEBHOOK_SECRET, 'utf-8'),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(received_signature, generated_signature):
        return jsonify({"error": "Invalid Razorpay signature"}), 400

    webhook_data = json.loads(payload)
    event = webhook_data.get('event')

    if event == "payment.captured":
        payment_entity = webhook_data['payload']['payment']['entity']
        email = payment_entity.get("email", "unknown")
        amount = payment_entity.get("amount", 0)
        payment_id = payment_entity.get("id")
        order_id = payment_entity.get("order_id")

        print(f"✅ Razorpay Payment Captured: {email} - ₹{amount/100}")

        # Save to DB
        add_payment_record(
            email=email,
            gateway="razorpay",
            amount=amount,
            status="captured",
            payment_id=payment_id,
            order_id=order_id
        )

    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    app.run(port=5000)
