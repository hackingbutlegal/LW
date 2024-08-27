import os
import hmac
import hashlib
import string
import random
from flask import Flask, request, jsonify, abort
import chargebee
import requests
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = Flask(__name__)

# Configure Chargebee
chargebee.configure(os.getenv("CHARGEBEE_API_KEY"))
ANYTHING_LLM_API_BASE_URL = os.getenv("ANYTHING_LLM_API_BASE_URL")
ANYTHING_LLM_API_KEY = os.getenv("ANYTHING_LLM_API_KEY")
CHARGEBEE_WEBHOOK_SECRET = os.getenv("CHARGEBEE_WEBHOOK_SECRET")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")

def verify_webhook(webhook_payload, webhook_signature):
    computed_signature = hmac.new(
        CHARGEBEE_WEBHOOK_SECRET.encode('utf-8'),
        webhook_payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(computed_signature, webhook_signature)

def anything_llm_api_call(method, endpoint, json=None):
    headers = {
        "Authorization": f"Bearer {ANYTHING_LLM_API_KEY}",
        "Content-Type": "application/json"
    }
    url = f"{ANYTHING_LLM_API_BASE_URL}{endpoint}"
    response = requests.request(method, url, headers=headers, json=json)
    response.raise_for_status()
    return response.json()

@app.route('/chargebee-webhook', methods=['POST'])
def chargebee_webhook():
    webhook_payload = request.data
    webhook_signature = request.headers.get('X-Chargebee-Signature')

    if not verify_webhook(webhook_payload, webhook_signature):
        abort(400, 'Invalid signature')

    chargebee_event = chargebee.Event.deserialize(webhook_payload)
    
    if chargebee_event.event_type == "subscription_created":
        handle_subscription_created(chargebee_event.content)
    elif chargebee_event.event_type == "subscription_cancelled":
        handle_subscription_cancelled(chargebee_event.content)
    elif chargebee_event.event_type == "subscription_changed":
        handle_subscription_changed(chargebee_event.content)
    
    return jsonify(success=True), 200

def handle_subscription_created(content):
    subscription = content.subscription
    customer = content.customer
    
    password = generate_random_password()
    user_data = {
        "username": customer.email,
        "password": password,
        "role": determine_role_from_plan(subscription.plan_id),
        "suspended": 0
    }
    
    response = anything_llm_api_call("POST", "/v1/admin/users/new", json=user_data)
    
    if response.get("error") is None:
        user_id = response["user"]["id"]
        update_user_metadata(user_id, {"chargebee_customer_id": customer.id})
        send_welcome_email(customer.email, password)
    else:
        app.logger.error(f"Error creating user: {response.get('error')}")

def handle_subscription_cancelled(content):
    subscription = content.subscription
    
    users = anything_llm_api_call("GET", "/v1/admin/users")
    user = next((u for u in users.get("users", []) if u.get("metadata", {}).get("chargebee_customer_id") == subscription.customer_id), None)
    
    if user:
        update_data = {"suspended": 1}
        anything_llm_api_call("POST", f"/v1/admin/users/{user['id']}", json=update_data)

def handle_subscription_changed(content):
    subscription = content.subscription
    
    users = anything_llm_api_call("GET", "/v1/admin/users")
    user = next((u for u in users.get("users", []) if u.get("metadata", {}).get("chargebee_customer_id") == subscription.customer_id), None)
    
    if user:
        update_data = {
            "role": determine_role_from_plan(subscription.plan_id)
        }
        anything_llm_api_call("POST", f"/v1/admin/users/{user['id']}", json=update_data)

def determine_role_from_plan(plan_id):
    plan_to_role = {
        "basic-plan": "default",
        "pro-plan": "admin"
    }
    return plan_to_role.get(plan_id, "default")

def update_user_metadata(user_id, metadata):
    current_user = anything_llm_api_call("GET", f"/v1/admin/users/{user_id}")
    updated_metadata = {**current_user.get("metadata", {}), **metadata}
    update_data = {"metadata": updated_metadata}
    anything_llm_api_call("POST", f"/v1/admin/users/{user_id}", json=update_data)

def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(length))
    return password

def send_welcome_email(email, password):
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=email,
        subject='Welcome to AnythingLLM - Your Account Details',
        html_content=f'''
        <html>
            <body>
                <h2>Welcome to AnythingLLM!</h2>
                <p>Your account has been created successfully.</p>
                <p>Here are your login details:</p>
                <ul>
                    <li>Username: {email}</li>
                    <li>Password: {password}</li>
                </ul>
                <p>Please change your password after your first login.</p>
                <p>If you have any questions, please don't hesitate to contact our support team.</p>
            </body>
        </html>
        '''
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        app.logger.info(f"Welcome email sent to {email}. Status code: {response.status_code}")
    except Exception as e:
        app.logger.error(f"Error sending welcome email to {email}: {str(e)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
