# Quantum CA AI Call Center: Deployment & Management Guide

This guide explains how to deploy the system to a server and how to add new restaurants to the call center.

---

## 1. Deployment Guide

### A. Server Requirements
- **OS**: Ubuntu 20.04 or newer.
- **Python**: 3.9+
- **Security**: Port 80, 443 (for HTTPS/WSS), and 8000 (app internally) must be open.
- **Domain**: A domain pointing to your server (e.g., `quantumca.org`) is REQUIRED for SSL, which Twilio needs for streaming audio.

### B. Step-by-Step Installation

1. **Clone & Setup Environment**:
   ```bash
   cd /var/www/
   git clone <your-repo-url> call_center_ai
   cd call_center_ai
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Credentials**:
   Create a `.env` file and fill in your Twilio and STT provider (Google/Azure) details.
   ```bash
   cp .env.example .env
   nano .env
   ```

3. **Setup Nginx with SSL**:
   Install Certbot and configure your domain.
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d quantumca.org
   ```

4. **Run as a Service**:
   Create a systemd unit file as described in `README.md` to ensure the app restarts on reboot and stays running.

---

## 2. Managing Restaurants

The system is designed to be **multi-tenant**. This means one server can handle calls for hundreds of different restaurants. Each restaurant is identified by the **unique Twilio Phone Number** it uses.

### How to Add a New Restaurant:

#### Step 1: Buy a Twilio Number
1. Login to your [Twilio Console](https://www.twilio.com/console).
2. Go to **Phone Numbers > Manage > Buy a Number**.
3. Choose a local number for the restaurant's location.

#### Step 2: Configure the Twilio Webhook
1. In the Twilio Console, click on your new number.
2. Scroll to the **Voice & Fax** section.
3. Under **"A Call Comes In"**, select **Webhook**.
4. Set the URL to: `https://quantumca.org/voice`
5. Set the Method to: `POST`
6. Save the settings.

#### Step 3: Add Restaurant to Database
Currently, the system uses a mock database in `app/models/database.py`. To add a restaurant:

1. Open `app/models/database.py`.
2. Add a new `Restaurant` entry to the `restaurants_db` list:
   ```python
   Restaurant(
       id="unique_id",
       name="Restaurant Name",
       phone_number="+15551234567", # THE TWILIO NUMBER YOU BOUGHT
       menu=[
           MenuItem(
               id="m1",
               name="Dish Name",
               price=10.99,
               description="Delicious dish description",
               options=[
                   Option(name="Size", choices=["Small", "Large"])
               ]
           ),
           # Add more dishes...
       ]
   )
   ```

#### Step 4: Restart the Server
If you are using the `systemd` service:
```bash
sudo systemctl restart callcenter
```

---

## 3. How the System Routes Calls

When a call comes in, the server receives a `POST` request from Twilio.
1. The server looks at the `To` field in the request (this is the number the customer dialed).
2. It searches the `restaurants_db` for that specific phone number.
3. It loads the correct **Restaurant Name** and **Menu** for that specific caller.
4. The AI then answers: *"Welcome to [Restaurant Name]. What would you like to order?"* and provides the menu context to the AI logic.

---

## 4. Scaling to a Real Database
For a production system with many restaurants, you should replace the list in `database.py` with a real database like **PostgreSQL** or **MongoDB**.
- You would create a simple admin dashboard where you can add restaurants and upload menus without editing code.
- The `get_restaurant_by_phone` function would then perform a SQL query: `SELECT * FROM restaurants WHERE phone_number = ?`.
