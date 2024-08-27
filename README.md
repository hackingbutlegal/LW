# Chargebee Webhook Handler for AnythingLLM

This project implements a webhook handler for Chargebee events, integrating with AnythingLLM for user management. It's designed to be deployed on Railway.app.

## Features

- Handles Chargebee subscription events (created, cancelled, changed)
- Creates and manages users in AnythingLLM based on Chargebee subscriptions
- Sends welcome emails to new users using SendGrid
- Implements webhook signature verification for security

## Prerequisites

- Python 3.7+
- A Chargebee account with API access
- An AnythingLLM instance with API access
- A SendGrid account for sending emails
- A Railway.app account for deployment

## Setup

1. Clone this repository to your local machine.

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up the following environment variables:
   - `CHARGEBEE_API_KEY`: Your Chargebee API key
   - `ANYTHING_LLM_API_BASE_URL`: The base URL of your AnythingLLM API
   - `ANYTHING_LLM_API_KEY`: Your AnythingLLM API key
   - `CHARGEBEE_WEBHOOK_SECRET`: Your Chargebee webhook secret
   - `SENDGRID_API_KEY`: Your SendGrid API key
   - `FROM_EMAIL`: The email address to use as the sender for welcome emails

## Deployment on Railway

1. Push your code to a GitHub repository.

2. Create a new project on Railway.app and connect it to your GitHub repository.

3. Railway should automatically detect that it's a Python app and use the `Procfile`.

4. Set the required environment variables in Railway's dashboard.

5. Deploy the application.

6. Once deployed, Railway will provide you with a URL for your application. Use this URL to configure your Chargebee webhook:
   - In your Chargebee dashboard, go to Settings > API & Webhooks > Webhook Settings.
   - Add a new webhook with the URL provided by Railway, appending your webhook route (e.g., `https://your-railway-app.up.railway.app/chargebee-webhook`).

## Usage

The webhook handler automatically processes the following Chargebee events:

- `subscription_created`: Creates a new user in AnythingLLM and sends a welcome email.
- `subscription_cancelled`: Suspends the user in AnythingLLM.
- `subscription_changed`: Updates the user's role in AnythingLLM based on the new subscription plan.

## Security

- Webhook requests are verified using HMAC SHA256 signature verification.
- All sensitive information is stored in environment variables.
- Passwords are randomly generated and sent securely via email.

## Troubleshooting

- Check Railway.app logs for any error messages.
- Ensure all environment variables are correctly set.
- Verify that your AnythingLLM instance is accessible and the API key is valid.
- Confirm that your SendGrid account is properly set up and the sender email is verified.

