# StyleHub – Fashion Mini Store Backend

## Project Overview

StyleHub is a fashion mini-store backend built with FastAPI and SQLite. It provides APIs for user authentication, product browsing, shopping cart management, order processing, and Stripe test-mode payments.

## Technology Stack

* Python
* FastAPI
* SQLite
* SQLAlchemy
* JWT authentication
* Password hashing
* Stripe API (Test Mode)
* Stripe webhooks

## Features

* User registration and login
* JWT-based authentication
* Product listing and product details
* Shopping cart management
* Order creation and retrieval
* Stripe payment integration
* Payment status and order status updates
* Checkout page
* Stripe webhook endpoint

## Project Structure

```text
backend/
├── app/
│   ├── routers/
│   │   ├── auth.py
│   │   ├── products.py
│   │   ├── cart.py
│   │   ├── orders.py
│   │   ├── payments.py
│   │   ├── webhook.py
│   │   └── checkout.html
│   ├── auth.py
│   ├── database.py
│   ├── dependencies.py
│   ├── main.py
│   ├── models.py
│   └── schemas.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Setup Instructions

### 1. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a local `.env` file using `.env.example` as a template. Add your own development and Stripe Test Mode credentials. Never commit `.env` to GitHub.

### 4. Start the FastAPI server

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

### 5. Open the API documentation

Visit:
http://127.0.0.1:8001/docs

### 6. Open the checkout page

Visit:
http://127.0.0.1:8001/checkout

## Stripe Testing

Use Stripe Test Mode credentials and test card details from Stripe's official testing documentation. Never use real card details or live-mode credentials for development testing.

For webhook testing, run the Stripe CLI listener in a separate terminal and forward the selected test events to:
http://127.0.0.1:8001/webhook/stripe

## Important Security Notes

* Do not commit `.env` or real credentials.
* Use test-mode Stripe keys for development.
* Keep the application secret key private.
* Verify Stripe webhook signatures before processing payment events.

## Current Verification

The existing test order was verified against Stripe and reconciled successfully.

* Order ID: 1
* Payment status: Paid
* Order status: Confirmed

This reflects the local development database and is not a production order.
