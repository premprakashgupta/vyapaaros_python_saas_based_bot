# 🚀 VyapaarOS AI Bot — Complete Production Setup & Deployment Guide

This guide documents the complete end-to-end deployment process for the **VyapaarOS AI Bot SaaS** platform on an **AWS EC2 Ubuntu Linux VPS** with **PostgreSQL, Gunicorn, Nginx, ChromaDB Vector Store, Groq Cloud LLM, and Free HTTPS SSL**.

---

## 🏗️ Production Architecture Overview

```text
Visitor Browser / Client Website
              │
              ▼ (HTTPS - Port 443 / HTTP - Port 80)
┌──────────────────────────────────────────────────────────┐
│                   Nginx Web Server                       │
│    (Reverse Proxy + Static Files Cache + Let's Encrypt)  │
└─────────────────────────────┬────────────────────────────┘
                              │ (Port 8000 Proxy Pass)
┌─────────────────────────────▼────────────────────────────┐
│              Gunicorn WSGI Application Server            │
│                 (3 Workers, Auto-Restart)                │
└─────────────────────────────┬────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────┐
│                    Django Core Framework                 │
│  ┌───────────────────────┐    ┌──────────────────────┐  │
│  │ PostgreSQL Database   │    │ ChromaDB (Vector DB) │  │
│  │ (Clients, Leads, Keys)│    │ (Product Embeddings) │  │
│  └───────────────────────┘    └──────────────────────┘  │
│                              │                           │
│                              ▼                           │
│                    Groq Cloud LLM API                    │
│                 (Qwen 3.8 / Llama 3.3)                   │
└──────────────────────────────────────────────────────────┘
```

---

## 📑 Table of Contents
1. [AWS EC2 Instance & Elastic IP Setup](#1-aws-ec2-instance--elastic-ip-setup)
2. [Domain DNS Configuration](#2-domain-dns-configuration)
3. [VPS System Package Installation](#3-vps-system-package-installation)
4. [PostgreSQL Database & User Configuration](#4-postgresql-database--user-configuration)
5. [Project Codebase & Python Virtualenv Setup](#5-project-codebase--python-virtualenv-setup)
6. [Environment Variables (`.env`) Configuration](#6-environment-variables-env-configuration)
7. [Database Migrations, Static Assets & Superuser](#7-database-migrations-static-assets--superuser)
8. [Data Seeding (VyapaarOS Services & 300+ Demo Products)](#8-data-seeding-vyapaaros-services--300-demo-products)
9. [Gunicorn Background Systemd Service](#9-gunicorn-background-systemd-service)
10. [Nginx Reverse Proxy & File Permissions](#10-nginx-reverse-proxy--file-permissions)
11. [Free HTTPS SSL Certificate (Certbot Let's Encrypt)](#11-free-https-ssl-certificate-certbot-lets-encrypt)
12. [1-Line Client Website Embed Script](#12-1-line-client-website-embed-script)
13. [Maintenance & Cheat Sheet Commands](#13-maintenance--cheat-sheet-commands)

---

## 1. AWS EC2 Instance & Elastic IP Setup

### A. Launch EC2 Instance
1. Go to **AWS Console** ➔ **EC2** ➔ **Launch Instance**.
2. **Name:** `vyapaaros-production`
3. **AMI (Operating System):** `Ubuntu Server 24.04 LTS (HVM), SSD Volume Type` (64-bit x86).
4. **Instance Type:** 
   - Recommended: `m7i-flex.large` (2 vCPU, 8 GB RAM)
   - Free-Tier: `t2.micro` / `t3.micro` (1 vCPU, 1 GB RAM)
5. **Key Pair:** Create a new key pair (e.g. `vyapaaros-key.pem`) and download it.
6. **Network Settings (Security Group Rules):**
   - ✅ **SSH** (Port `22`) ➔ Source: `Anywhere` (`0.0.0.0/0`)
   - ✅ **HTTP** (Port `80`) ➔ Source: `Anywhere` (`0.0.0.0/0`)
   - ✅ **HTTPS** (Port `443`) ➔ Source: `Anywhere` (`0.0.0.0/0`)
7. **Storage:** Set to `30 GiB` (General Purpose SSD `gp3`).
8. Click **Launch Instance**.

### B. Allocate & Associate Elastic IP (Static Public IPv4)
1. Go to **EC2 Dashboard** ➔ Left Menu ➔ **Elastic IPs** (under Network & Security).
2. Click **Allocate Elastic IP address** ➔ Click **Allocate**.
3. Select the created Elastic IP ➔ Click **Actions** ➔ **Associate Elastic IP address**.
4. Select your running instance `vyapaaros-production` ➔ Click **Associate**.
*(Example Elastic IP: `65.2.232.38`)*

---

## 2. Domain DNS Configuration

In your domain registrar DNS Manager (GoDaddy, Hostinger, Namecheap, Cloudflare, etc.):
Add an **A Record** pointing your subdomain to your Elastic IP:

| Type | Name / Host | Value / Points To | TTL |
|---|---|---|---|
| **A** | `bot` | `65.2.232.38` *(Your Elastic IP)* | `Auto` / `300s` |

---

## 3. VPS System Package Installation

Connect to your VPS via SSH from your local machine:
```bash
ssh -i "path/to/vyapaaros-key.pem" ubuntu@65.2.232.38
```

Run system updates and install essential software:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv nginx git curl build-essential postgresql postgresql-contrib certbot python3-certbot-nginx
```

---

## 4. PostgreSQL Database & User Configuration

Start PostgreSQL service and create dedicated database, user, and permissions:

```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create Database, User, and Grant Full Permissions
sudo -u postgres psql -c "CREATE DATABASE vyapaaros_db;"
sudo -u postgres psql -c "CREATE USER vyapaar_user WITH PASSWORD 'VyapaarSecure2026';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE vyapaaros_db TO vyapaar_user;"
sudo -u postgres psql -c "ALTER DATABASE vyapaaros_db OWNER TO vyapaar_user;"
```

---

## 5. Project Codebase & Python Virtualenv Setup

Clone the repository into the user home directory:
```bash
cd ~
git clone https://github.com/premprakashgupta/vyapaaros_python_saas_based_bot.git
cd vyapaaros_python_saas_based_bot

# Create and activate Python Virtual Environment
python3 -m venv venv
source venv/bin/activate

# Set temporary directory to avoid memory-quota limits during heavy package installation
export TMPDIR=/home/ubuntu/tmp && mkdir -p /home/ubuntu/tmp

# Install lightweight CPU PyTorch wheel first (~150MB instead of 2.5GB GPU CUDA)
pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install all project requirements
pip install --no-cache-dir -r requirements.txt
```

---

## 6. Environment Variables (`.env`) Configuration

Create your production `.env` file:
```bash
cp .env.example .env
nano .env
```

Paste your production secrets and save (`Ctrl + O`, `Enter`, `Ctrl + X`):
```ini
# Django Core Settings
DJANGO_SECRET_KEY=django-insecure-vyapaaros-production-key-2026
DEBUG=False
ALLOWED_HOSTS=*

# PostgreSQL Database Connection
DATABASE_URL=postgresql://vyapaar_user:VyapaarSecure2026@localhost:5432/vyapaaros_db

# Groq Cloud LLM API
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=qwen/qwen3.8-27b
```

---

## 7. Database Migrations, Static Assets & Superuser

```bash
# 1. Apply database schema to PostgreSQL
python manage.py migrate

# 2. Collect static files into staticfiles/ for Nginx
python manage.py collectstatic --no-input

# 3. Create Superadmin User (Enter username: admin, email, password)
python manage.py createsuperuser
```

---

## 8. Data Seeding (VyapaarOS Services & 300+ Demo Products)

Run the seeding scripts to initialize superadmin services and all demo clients:

```bash
# 1. Seed Superadmin VyapaarOS HQ Business Profile
python crawl_vyapaaros.py

# 2. Seed VyapaarOS Services (Web Dev, SEO, AI Bot, App Dev) into ChromaDB
python seed_vyapaaros_services.py

# 3. Seed 3 Complete Demo Businesses + 300+ Clothing/CSC/Furniture Catalogs
python seed_demo_clients.py
```

### 📋 Seeded Accounts & Credentials:
| Business Name | Category | Username | Password | Catalog Size |
|---|---|---|---|---|
| **VyapaarOS HQ** | SaaS Platform | `admin` | *(Your Superuser Password)* | Main Services |
| **Vastra Collection** | Ethnic Clothing | `vastracollection` | `client123` | **300+ Products** |
| **Digital Point Cafe** | Cyber & CSC | `digitalpoint` | `client123` | Full Rate Card |
| **Luxe Interiors** | Home Decor | `luxestore` | `client123` | Furniture Catalog |

---

## 9. Gunicorn Background Systemd Service

Create a persistent background service managed by Linux `systemd`:

```bash
sudo nano /etc/systemd/system/vyapaaros.service
```

Paste the following configuration:
```ini
[Unit]
Description=VyapaarOS Gunicorn Application Server
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/vyapaaros_python_saas_based_bot
ExecStart=/home/ubuntu/vyapaaros_python_saas_based_bot/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 vyapaaros_core.wsgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start Gunicorn:
```bash
sudo systemctl daemon-reload
sudo systemctl start vyapaaros
sudo systemctl enable vyapaaros
sudo systemctl status vyapaaros
```

---

## 10. Nginx Reverse Proxy & File Permissions

### A. Fix Home & Static Permissions
Ensure `www-data` (Nginx) has read access to static assets:
```bash
sudo chmod 755 /home/ubuntu
sudo chmod -R 755 /home/ubuntu/vyapaaros_python_saas_based_bot/staticfiles
```

### B. Configure Nginx Server Block
```bash
sudo nano /etc/nginx/sites-available/vyapaaros
```

Paste the following configuration (Replace `bot.vyapaaros.in` and `65.2.232.38` with your domain and IP):
```nginx
server {
    listen 80;
    server_name bot.vyapaaros.in 65.2.232.38;

    client_max_body_size 50M;

    location /static/ {
        alias /home/ubuntu/vyapaaros_python_saas_based_bot/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/vyapaaros /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

---

## 11. Free HTTPS SSL Certificate (Certbot Let's Encrypt)

Issue and install automated SSL certificate:
```bash
sudo certbot --nginx -d bot.vyapaaros.in
```
Follow prompts to enter your email and agree to terms (`Y`). Certbot will automatically configure Nginx for HTTPS with automatic 90-day renewal.

Verify SSL auto-renewal:
```bash
sudo certbot renew --dry-run
```

---

## 12. 🤖 Complete Bot Integration Guide (Multi-Platform)

The VyapaarOS AI Bot is built with **Shadow DOM Isolation**, meaning its CSS styles and behavior will **never conflict or break** the client website's existing styling or layout.

---

### 🌐 Method A: Standard HTML / PHP / Static Landing Pages

Add the script tag right before the closing `</body>` tag on all pages:

```html
<!-- ======================================================== -->
<!-- 🤖 VyapaarOS AI Sales Executive Widget                   -->
<!-- ======================================================== -->
<script 
  src="https://bot.vyapaaros.in/static/widget.js" 
  data-api-key="vyapaar_live_YOUR_API_KEY_HERE" 
  defer>
</script>
```

---

### ⚛️ Method B: React.js & Next.js

#### 1. Next.js (App Router / Pages Router):
In `app/layout.js` or `pages/_app.js`:
```jsx
import Script from 'next/script';

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        {children}
        <Script
          src="https://bot.vyapaaros.in/static/widget.js"
          data-api-key="vyapaar_live_YOUR_API_KEY_HERE"
          strategy="lazyOnload"
        />
      </body>
    </html>
  );
}
```

#### 2. React.js (Vite / CRA):
In `index.html` (public root) right before `</body>` or dynamically in `App.jsx`:
```jsx
import { useEffect } from 'react';

function App() {
  useEffect(() => {
    const script = document.createElement('script');
    script.src = 'https://bot.vyapaaros.in/static/widget.js';
    script.setAttribute('data-api-key', 'vyapaar_live_YOUR_API_KEY_HERE');
    script.async = true;
    document.body.appendChild(script);

    return () => {
      // Optional cleanup
      const el = document.getElementById('vyapaaros-chat-widget-root');
      if (el) el.remove();
    };
  }, []);

  return <div>{/* Your App */}</div>;
}
```

---

### 🛍️ Method C: Shopify Stores

1. Go to **Shopify Admin** ➔ **Online Store** ➔ **Themes**.
2. Click **`...` (Actions)** next to your active theme ➔ **Edit Code**.
3. In the left sidebar, open **`layout/theme.liquid`**.
4. Scroll down to the bottom and paste right above `</body>`:
```liquid
<!-- VyapaarOS AI Sales Chatbot -->
<script 
  src="https://bot.vyapaaros.in/static/widget.js" 
  data-api-key="vyapaar_live_YOUR_API_KEY_HERE" 
  defer>
</script>
```
5. Click **Save**.

---

### 📝 Method D: WordPress & WooCommerce

#### Option 1: Via Plugin (No Code Required)
1. In WP Admin, install plugin: **"WPCode"** (or *Insert Headers and Footers*).
2. Go to **Code Snippets** ➔ **Header & Footer** ➔ **Footer** section.
3. Paste the script tag and click **Save Changes**.

#### Option 2: Via Theme `functions.php`
```php
function add_vyapaaros_chatbot() {
    ?>
    <script 
      src="https://bot.vyapaaros.in/static/widget.js" 
      data-api-key="vyapaar_live_YOUR_API_KEY_HERE" 
      defer>
    </script>
    <?php
}
add_action('wp_footer', 'add_vyapaaros_chatbot');
```

---

### 🏷️ Method E: Google Tag Manager (GTM — Zero Codebase Touch)

1. Open your **Google Tag Manager** container.
2. Go to **Tags** ➔ **New** ➔ **Tag Configuration** ➔ Choose **Custom HTML**.
3. Paste the `<script>` tag.
4. Set **Triggering** to: **Initialization - All Pages** (or *All Pages*).
5. Name it `VyapaarOS Chat Widget` ➔ Click **Save** ➔ **Submit & Publish**.

---

### 🎨 Layout Adjustment (When Existing Floating WhatsApp Button Exists)

The VyapaarOS Bot launcher is positioned at `bottom: 24px; right: 24px`. If the client already has a floating WhatsApp icon in the same corner, adjust the WhatsApp icon's CSS slightly upwards so both buttons look clean:

```css
/* Shift the existing WhatsApp button slightly above the bot */
.existing-floating-whatsapp-btn {
    position: fixed !important;
    bottom: 96px !important;  /* Elevated above bot launcher */
    right: 24px !important;
    z-index: 9999 !important;
}
```

---

### 🔒 Security & Domain Whitelisting

To prevent third-party websites from stealing or reusing a client's API Key:
1. Open **Django Superadmin** (`https://bot.vyapaaros.in/admin/`) ➔ **Client API Keys**.
2. Set **Allowed Domains** to the client's actual domains:
   ```text
   example.com, www.example.com, *.example.com, localhost
   ```
3. Any unauthorized website trying to load the key will be blocked with `403 Unauthorized Origin`.

---

### ⚡ Direct REST API Integration (Headless / Mobile Apps)

If you are building a custom UI or Mobile App (Flutter / React Native), you can directly interact with the backend chat endpoint:

#### Endpoint:
`POST https://bot.vyapaaros.in/api/v1/widget/chat/`

#### Headers:
```http
Content-Type: application/json
X-Api-Key: vyapaar_live_YOUR_API_KEY_HERE
```

#### Request Body:
```json
{
  "api_key": "vyapaar_live_YOUR_API_KEY_HERE",
  "session_id": "unique_visitor_uuid_123",
  "message": "What is the price of your business portfolio website?",
  "history": [
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello! How can I help you today?"}
  ]
}
```

#### Response:
```json
{
  "success": true,
  "reply": "The Business Portfolio Website starts at ₹4,999 with Free Hosting & SSL.",
  "images": [
    "https://images.unsplash.com/photo-1467232004584-a241de8bcf5d?auto=format&fit=crop&w=600&q=80"
  ],
  "client_name": "VyapaarOS HQ",
  "bot_name": "VyapaarOS Executive",
  "brand_color": "#F2541B",
  "whatsapp_url": "https://wa.me/919955804730?text=Hi%20VyapaarOS%20HQ..."
}
```

---

## 13. Maintenance & Cheat Sheet Commands

### Update Code from GitHub:
```bash
cd ~/vyapaaros_python_saas_based_bot
git pull origin main
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --no-input
sudo systemctl restart vyapaaros
```

### View Live Gunicorn Server Logs:
```bash
sudo journalctl -u vyapaaros -f
```

### View Nginx Access & Error Logs:
```bash
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### Restart All Services:
```bash
sudo systemctl restart vyapaaros
sudo systemctl restart nginx
sudo systemctl restart postgresql
```
