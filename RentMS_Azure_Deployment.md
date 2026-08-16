# RentMS — Azure VM Deployment Guide
**Project:** Rent Management System (RentMS)  
**Live URL:** http://20.24.85.96  
**Stack:** Python + Django + PostgreSQL + Nginx + Gunicorn  
**Azure Resources:** Resource Group → PostgreSQL Server → VM  

---

## Azure Resources Summary

| Resource | Name | Details |
|---|---|---|
| Resource Group | `rentms-rg` | East Asia region — holds everything |
| PostgreSQL Server | `rentms-db-server` | Standard_B1ms, Version 15 |
| Database | `rentms_db` | UTF8, inside rentms-db-server |
| Virtual Machine | `rentms-vm` | Ubuntu 22.04, Standard_B2als_v2 |
| Public IP | `20.24.85.96` | Your live server address |
| Admin User (DB) | `adminbikash` | Password: ... |
| Admin User (VM) | `azureuser` | SSH key authentication |

---

## Step-by-Step Commands

### Step 1 — Login to Azure
```bash
az login
az account show
```
**What it does:** Logs into your Azure account via browser. `account show` confirms you are logged in with the correct subscription.

---

### Step 2 — Create Resource Group
```bash
az group create --name rentms-rg --location eastasia
```
**What it does:** Creates a container (folder) called `rentms-rg` in East Asia. All Azure resources (VM, DB) go inside this group. Easy to delete everything at once later.

---

### Step 3 — Register PostgreSQL Provider
```bash
az provider register --namespace Microsoft.DBforPostgreSQL
az provider show --namespace Microsoft.DBforPostgreSQL --query "registrationState"
```
**What it does:** Activates PostgreSQL service on your Azure subscription. Only needed once. Wait until it shows `"Registered"` before proceeding.

---

### Step 4 — Create PostgreSQL Server
```bash
az postgres flexible-server create \
  --resource-group rentms-rg \
  --name rentms-db-server \
  --location eastasia \
  --admin-user adminbikash \
  --admin-password ... \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 15 \
  --yes
```
**What it does:** Creates the PostgreSQL SERVER (the machine that runs database). This is not the database itself — it's the server that will hold databases. Takes 2-3 minutes.

---

### Step 5 — Create Database
```bash
az postgres flexible-server db create \
  --resource-group rentms-rg \
  --server-name rentms-db-server \
  --name rentms_db
```
**What it does:** Creates the actual database `rentms_db` inside the server. Think of it like: server = building, database = room inside building.

---

### Step 6 — Check Available VM Sizes
```bash
az vm list-skus --location eastasia --size Standard_B --output table
```
**What it does:** Lists all VM sizes available in East Asia. Use this before creating VM to avoid "SkuNotAvailable" errors.

---

### Step 7 — Create VM
```bash
az vm create \
  --resource-group rentms-rg \
  --name rentms-vm \
  --image Ubuntu2204 \
  --size Standard_B2als_v2 \
  --admin-username azureuser \
  --generate-ssh-keys \
  --public-ip-sku Standard
```
**What it does:** Creates an Ubuntu 22.04 Linux VM. `--generate-ssh-keys` auto-creates SSH keys saved to `C:\Users\Hp\.ssh\`. Returns your public IP address.

---

### Step 8 — Open Ports
```bash
az vm open-port --resource-group rentms-rg --name rentms-vm --port 80 --priority 1001
az vm open-port --resource-group rentms-rg --name rentms-vm --port 443 --priority 1002
```
**What it does:** Opens port 80 (HTTP) and 443 (HTTPS) so people can visit your website. Port 22 (SSH) is already open by default.

---

### Step 9 — Allow VM to Connect to Database
```bash
az postgres flexible-server firewall-rule create \
  --resource-group rentms-rg \
  --server-name rentms-db-server \
  --name allow-vm \
  --start-ip-address 10.0.0.4 \
  --end-ip-address 10.0.0.4

az postgres flexible-server firewall-rule create \
  --resource-group rentms-rg \
  --server-name rentms-db-server \
  --name allow-azure-services \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```
**What it does:** First rule allows VM's private IP to connect to DB. Second rule (0.0.0.0) allows all Azure services to connect — needed for VM→DB communication inside Azure network.

---

### Step 10 — SSH into VM
```bash
ssh azureuser@20.24.85.96
```
**What it does:** Connects to your Azure VM remotely. You are now typing commands on the Linux server in Azure. Replace IP if it changes.

---

### Step 11 — Install Software on VM
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git nginx
sudo apt install -y libpq-dev postgresql-client
```
**What it does:**
- `apt update` → updates package list
- `apt upgrade` → upgrades installed packages
- Installs Python, pip, venv, git, nginx (web server)
- `libpq-dev` → needed to compile psycopg2 (Django DB driver)
- `postgresql-client` → lets you connect to PostgreSQL from command line

---

### Step 12 — Clone Project
```bash
sudo mkdir -p /var/www/Django_Project/Rent_Management_System
cd /var/www/Django_Project/Rent_Management_System
sudo git clone https://github.com/BikashGosain/Rent_Management_System.git .
```
**What it does:** Creates folder structure and clones your GitHub repo. The `.` at the end means clone into current folder.

---

### Step 13 — Setup Virtual Environment
```bash
sudo python3 -m venv venv
sudo venv/bin/pip install -r requirements.txt
```
**What it does:** Creates isolated Python environment and installs all project dependencies from requirements.txt.

---

### Step 14 — Create .env File on VM
```bash
sudo nano /var/www/Django_Project/Rent_Management_System/.env
```
**What it does:** Creates environment variables file on the VM. This file is NEVER pushed to GitHub — it stays only on the VM. Contains all secrets (DB password, email, secret key).

**.env contents for Azure:**
```bash
SECRET_KEY=your-secret-key
DEBUG=False
DJANGO_SETTINGS_MODULE=config.settings.production
ALLOWED_HOSTS=20.24.85.96

DATABASE_URL=

EMAIL_HOST_USER=youremail@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_SECRET=your-google-secret

TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token
TWILIO_PHONE_NUMBER=+1234567890

CSRF_TRUSTED_ORIGINS=http://20.24.85.96
```

---

### Step 15 — Run Migrations and Collect Static
```bash
sudo venv/bin/python manage.py migrate --settings=config.settings.production
sudo venv/bin/python manage.py collectstatic --settings=config.settings.production --noinput
sudo venv/bin/python manage.py createsuperuser --settings=config.settings.production
```
**What it does:**
- `migrate` → creates all database tables in Azure PostgreSQL
- `collectstatic` → copies all CSS/JS/images into staticfiles/ folder
- `createsuperuser` → creates admin account for /admin panel

---

### Step 16 — Create Gunicorn Service
```bash
sudo nano /etc/systemd/system/gunicorn.service
```
**What it does:** Creates a background service for Gunicorn (Python WSGI server). Gunicorn runs your Django app and communicates with Nginx via a socket file.

**gunicorn.service contents:**
```ini
[Unit]
Description=Gunicorn daemon for RentMS
After=network.target

[Service]
User=azureuser
Group=www-data
WorkingDirectory=/var/www/Django_Project/Rent_Management_System
ExecStart=/var/www/Django_Project/Rent_Management_System/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/var/www/Django_Project/Rent_Management_System/gunicorn.sock \
          config.wsgi:application
EnvironmentFile=/var/www/Django_Project/Rent_Management_System/.env
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn
```
- `start` → starts gunicorn now
- `enable` → auto starts on VM reboot
- `status` → check if running

---

### Step 17 — Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/rentms
```
**What it does:** Creates Nginx configuration. Nginx receives web requests on port 80 and forwards them to Gunicorn via socket.

**Nginx config contents:**
```nginx
server {
    listen 80;
    server_name 20.24.85.96;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        root /var/www/Django_Project/Rent_Management_System;
    }

    location /media/ {
        root /var/www/Django_Project/Rent_Management_System;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/Django_Project/Rent_Management_System/gunicorn.sock;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/rentms /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```
- `ln -s` → enables rentms site
- `rm default` → removes default nginx page
- `nginx -t` → tests config for errors
- `restart` → applies new config

---

### Step 18 — Fix Permissions
```bash
sudo chown -R azureuser:www-data /var/www/Django_Project/Rent_Management_System
sudo chmod -R 755 /var/www/Django_Project/Rent_Management_System
```
**What it does:** Gives nginx permission to read your project files and static/media folders.

---

## How to Update Code (After Changes)

When you make changes on local machine:
```bash
# On local machine
git add .
git commit -m "your changes"
git push origin main

# SSH into VM
ssh azureuser@20.24.85.96

# On VM
cd /var/www/Django_Project/Rent_Management_System
sudo git pull origin main
sudo venv/bin/python manage.py migrate --settings=config.settings.production
sudo venv/bin/python manage.py collectstatic --settings=config.settings.production --noinput
sudo systemctl restart gunicorn
```

---

## Useful Commands for Maintenance

```bash
# Check logs
sudo tail -f /var/log/nginx/error.log
sudo journalctl -u gunicorn -f

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# Check service status
sudo systemctl status gunicorn
sudo systemctl status nginx

# Test connection from VM
curl http://localhost
```

---

## Architecture Overview

```
User Browser
     ↓ port 80
   Nginx (web server)
     ↓ unix socket
   Gunicorn (WSGI server)
     ↓
   Django App
     ↓
   Azure PostgreSQL
   (rentms-db-server.postgres.database.azure.com)
```

---

## Important Notes

- `.env` file lives ONLY on the VM — never push to GitHub
- If VM restarts, gunicorn and nginx auto-start (enabled services)
- Static files served by Nginx directly (faster than Django)
- Media files (uploaded images) stored in `/media/` on VM
- To add domain name later → update `ALLOWED_HOSTS` and `server_name` in nginx config
