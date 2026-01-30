# Quantum CA AI Call Center

## Overview
This system enables automated food ordering via phone calls using AI-driven Speech-to-Text (STT). It is a **multi-tenant** platform, meaning one server can host many different restaurants simultaneously.

**[Read the Restaurant Management & Deployment Guide](RESTAURANT_GUIDE.md)** for detailed instructions on how to add restaurants and deploy to production.

## Prerequisites
- **Server**: Ubuntu 20.04+ (DigitalOcean recommended)
- **Domain**: A public domain name pointing to your server IP (Required for SSL/WebSockets).
- **Twilio Account**: With a purchased phone number.
- **Python**: 3.9 or higher.

---

## Deployment Guide (Step-by-Step)

### 1. Server Setup
SSH into your DigitalOcean Ubuntu server.

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv nginx -y
```

### 2. Application Installation
Clone or upload this code to `/var/www/call_center_ai`.

```bash
cd /var/www/call_center_ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file from the example.

```bash
cp .env.example .env
nano .env
```

Fill in your details:
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`
- `SERVER_HOST`: Your domain name (e.g., `https://quantumca.org`)
- `STT_PROVIDER`: "twilio", "google", or "azure"

**For Google Cloud:**
- Put your JSON service account key in the folder.
- Set `GOOGLE_APPLICATION_CREDENTIALS` path in env.

**For Azure:**
- Set `AZURE_SPEECH_KEY` and `AZURE_SPEECH_REGION` in env.

### 4. Running the Application (Systemd)
Create a systemd service to keep the app running.

`sudo nano /etc/systemd/system/callcenter.service`

```ini
[Unit]
Description=Call Center AI API
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/call_center_ai
Environment="PATH=/var/www/call_center_ai/venv/bin"
ExecStart=/var/www/call_center_ai/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable callcenter
sudo systemctl start callcenter
```

### 5. Nginx & SSL Configuration
Twilio Media Streams (for Google/Azure STT) **require** encryption (HTTPS/WSS).

Create Nginx block: `sudo nano /etc/nginx/sites-available/callcenter`

```nginx
server {
    server_name quantumca.org;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket Support for Audio Streaming
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/callcenter /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Get SSL Cert (Certbot):**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d quantumca.org
```

### 6. Twilio Configuration
1. Go to Twilio Console > Phone Numbers > Manage.
2. Select your number.
3. Under **Voice & Fax** > **A Call Comes In**:
   - Webhook
   - URL: `https://quantumca.org/voice`
   - HTTP Method: `POST`
4. Save.

## Multi-purpose Hosting
In addition to the AI Call Center, this server can host general web content (HTML, CSS, JS).

### How to add web content:
1. Place your files in the `static/` directory.
2. The `index.html` in `static/` will be served at the root `/`.
3. You can create subdirectories for different projects, e.g., `static/portfolio/index.html` will be available at `https://quantumca.org/portfolio/`.



### 7. Demo Flow: Lanzhou Hand Pulled Noodles (Guided)
The system is pre-configured with a demo for "Lanzhou Hand Pulled Noodles". 
**New!** The logic is now "Guided," helping customers who don't know how to order from a robot.

1. Call your Twilio number.
2. **Greeting**: Clearly states it is an automated assistant.
3. **Ordering**:
   - Speak naturally: *"I'd like the General Tso Chicken"*
   - Or browse categories: *"What poultry dishes do you have?"*
   - Or specifically ask for combos: *"Chicken Chow Mein Combo"*
4. **Guiding**: If you stay silent or say "I don't know", the system offers categories and examples.
5. **Confirmation & Summary**: Ensures accuracy before placing the order.

## Testing
- **API Status**: Visit `https://quantumca.org/api/status`
- **Web Content**: Visit `https://quantumca.org/` to see the landing page.
- **Voice Call**: Make a call to your Twilio number.
- **Logs**: Check logs: `journalctl -u callcenter -f`

