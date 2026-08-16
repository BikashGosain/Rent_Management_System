# RentMS — Complete Azure VM Deployment Guide
**Project:** Rent Management System (RentMS)  
**Stack:** Python + Django + PostgreSQL + Nginx + Gunicorn  
**Azure Free Domain:** rentms.eastasia.cloudapp.azure.com  
**Live Production:** https://bikashgosain.com.np (Render.com)

---

## Azure Resources Created

| Resource | Name | Details |
|---|---|---|
| Resource Group | `rentms-rg` | East Asia — holds all resources |
| PostgreSQL Server | `rentms-db-server` | Standard_B1ms, PostgreSQL 15 |
| Database | `rentms_db` | UTF8 charset |
| Virtual Machine | `rentms-vm` | Ubuntu 22.04, Standard_B2als_v2 |
| Public IP | `20.24.85.96` | Static IP |
| Azure Domain | `rentms.eastasia.cloudapp.azure.com` | Free Azure subdomain |
| VM Admin User | `azureuser` | SSH key authentication |
| DB Admin User | `adminbikash` | Password: ... |

---

## Important: Credit Management

```
VM running 24/7     → ~$30-40/month (compute)
PostgreSQL running  → ~$15-20/month
Public IP           → ~$3/month
Total               → ~$50-65/month

Student credit      → $100 (lasts ~1.5-2 months if always on)
```

**Save credits — deallocate when not using:**
```bash
# Stop VM (no compute charge)
az vm deallocate --resource-group rentms-rg --name rentms-vm

# Stop PostgreSQL
az postgres flexible-server stop --resource-group rentms-rg --name rentms-db-server

# Start VM when needed
az vm start --resource-group rentms-rg --name rentms-vm
```

**Stop vs Deallocate:**
```
stop       → VM off but Azure still reserves hardware → still charges
deallocate → VM fully released → NO compute charge → use this!
```

---

## Deployment Steps

### Step 1 — Login to Azure CLI
```bash
az login
az account show
```
**Note:** Opens browser for login. `account show` confirms correct subscription is selected. You should see `Azure for Students` with your KCT email.

---

### Step 2 — Create Resource Group
```bash
az group create --name rentms-rg --location eastasia
```
**Note:** Resource group is like a folder that holds ALL your Azure resources together (VM, database, IP). East Asia is closest region to Nepal. Delete the whole group to delete everything at once.

---

### Step 3 — Register PostgreSQL Provider
```bash
az provider register --namespace Microsoft.DBforPostgreSQL
az provider show --namespace Microsoft.DBforPostgreSQL --query "registrationState"
```
**Note:** Azure subscriptions need to register services before using them. Only needed once per subscription. Wait until output shows `"Registered"` before creating database.

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
**Note:** Creates the PostgreSQL SERVER (not the database yet). Think of it as the PostgreSQL application running on Azure. Takes 2-3 minutes. `Standard_B1ms` is cheapest tier. `Burstable` means it can handle traffic spikes.

---

### Step 5 — Create Database Inside Server
```bash
az postgres flexible-server db create \
  --resource-group rentms-rg \
  --server-name rentms-db-server \
  --name rentms_db
```
**Note:** Creates actual database `rentms_db` inside the server. Analogy: Server = building, Database = room inside building. Django will connect to this specific database.

---

### Step 6 — Check Available VM Sizes
```bash
az vm list-skus --location eastasia --size Standard_B --output table
```
**Note:** Always check available sizes before creating VM. Some sizes are not available in certain regions for student subscriptions. Look for `Restrictions: None` — those are available. `Standard_B2als_v2` works in East Asia.

---

### Step 7 — Create Virtual Machine
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
**Note:** Creates Ubuntu 22.04 Linux server. `--generate-ssh-keys` auto-creates SSH keys saved to `C:\Users\Hp\.ssh\` — this is how you login securely without password. Returns `publicIpAddress: 20.24.85.96` — this is your server address.

---

### Step 8 — Open Web Ports
```bash
az vm open-port --resource-group rentms-rg --name rentms-vm --port 80 --priority 1001
az vm open-port --resource-group rentms-rg --name rentms-vm --port 443 --priority 1002
```
**Note:** Azure VMs block all traffic by default. Port 22 (SSH) is already open. Port 80 = HTTP (normal web), Port 443 = HTTPS (secure web). Without this nobody can visit your website.

---

### Step 9 — Allow VM to Connect to PostgreSQL
```bash
# Allow VM private IP
az postgres flexible-server firewall-rule create \
  --resource-group rentms-rg \
  --server-name rentms-db-server \
  --name allow-vm \
  --start-ip-address 10.0.0.4 \
  --end-ip-address 10.0.0.4

# Allow all Azure services
az postgres flexible-server firewall-rule create \
  --resource-group rentms-rg \
  --server-name rentms-db-server \
  --name allow-azure-services \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```
**Note:** PostgreSQL blocks all connections by default. First rule allows VM's private IP (10.0.0.4). Second rule (0.0.0.0 to 0.0.0.0) is Azure's special flag to allow all internal Azure services — needed for VM to reach database inside Azure network.

---

### Step 10 — Set Free Azure Domain
```bash
az network public-ip update \
  --resource-group rentms-rg \
  --name rentms-vmPublicIP \
  --dns-name rentms
```
**Note:** Gives your VM a free Azure subdomain `rentms.eastasia.cloudapp.azure.com`. Format is always `<your-label>.eastasia.cloudapp.azure.com`. Completely free — does not consume credits. No need to buy a domain for demo purposes.

---

### Step 11 — SSH into VM
```bash
ssh azureuser@20.24.85.96
```
**Note:** Connects to your Azure VM remotely. Uses SSH key from `C:\Users\Hp\.ssh\` automatically. You are now typing commands on the Linux server in Azure. Type `exit` to disconnect. If connection refused → VM might be stopped, run `az vm start` first.

---

### Step 12 — Update and Install Software on VM
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git nginx
sudo apt install -y libpq-dev postgresql-client
```
**Note:**
- `apt update` → refreshes list of available packages
- `apt upgrade` → upgrades all installed packages to latest
- `nginx` → web server that handles incoming requests
- `libpq-dev` → C library needed to compile psycopg2 (Django's PostgreSQL driver)
- `postgresql-client` → command line tool to connect to PostgreSQL

---

### Step 13 — Clone Project from GitHub
```bash
sudo mkdir -p /var/www/Django_Project/Rent_Management_System
cd /var/www/Django_Project/Rent_Management_System
sudo git clone https://github.com/BikashGosain/Rent_Management_System.git .
```
**Note:** `/var/www/` is standard location for web apps on Linux. `mkdir -p` creates all folders in path. The `.` at end of git clone means "clone into current folder" instead of creating a new subfolder.

---

### Step 14 — Setup Virtual Environment
```bash
sudo python3 -m venv venv
sudo venv/bin/pip install -r requirements.txt
```
**Note:** Creates isolated Python environment — same packages as local machine. `venv/bin/pip` uses the venv's pip not system pip. If Django version error → change `Django==6.0.2` to `Django>=5.2` in requirements.txt and push to GitHub then pull.

---

### Step 15 — Create .env File on VM
```bash
sudo nano /var/www/Django_Project/Rent_Management_System/.env
```
**Note:** `.env` file contains all secrets. NEVER push to GitHub — lives only on VM. Create manually on every server you deploy to. Save with `Ctrl+X → Y → Enter`.

**.env contents for Azure:**
```bash

```

---

### Step 16 — Run Migrations and Setup Django
```bash
sudo venv/bin/python manage.py migrate --settings=config.settings.production
sudo venv/bin/python manage.py collectstatic --settings=config.settings.production --noinput
sudo venv/bin/python manage.py createsuperuser --settings=config.settings.production
```
**Note:**
- `migrate` → creates all Django tables in Azure PostgreSQL database
- `collectstatic` → copies all CSS/JS/images to staticfiles/ folder for nginx to serve
- `createsuperuser` → creates admin account for /admin panel on live site

---

### Step 17 — Create Gunicorn Service
```bash
sudo nano /etc/systemd/system/gunicorn.service
```
**Note:** Gunicorn is a Python WSGI server — it runs your Django app as a background service. `systemd` manages services on Linux. This config makes gunicorn auto-start when VM reboots. It communicates with Nginx via a Unix socket file.

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
sudo systemctl start gunicorn    # start now
sudo systemctl enable gunicorn   # auto-start on reboot
sudo systemctl status gunicorn   # check if running
```

---

### Step 18 — Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/rentms
```
**Note:** Nginx is a web server that receives HTTP requests on port 80 and forwards them to Gunicorn via socket. It also serves static files directly (much faster than Django serving them). Think: Browser → Nginx → Gunicorn → Django.

**Nginx config:**
```nginx
server {
    listen 80;
    server_name 20.24.85.96 rentms.eastasia.cloudapp.azure.com;

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
sudo rm /etc/nginx/sites-enabled/default   # remove default nginx page
sudo nginx -t                               # test config for errors
sudo systemctl restart nginx               # apply changes
```

---

### Step 19 — Fix Permissions
```bash
sudo chown -R azureuser:www-data /var/www/Django_Project/Rent_Management_System
sudo chmod -R 755 /var/www/Django_Project/Rent_Management_System
```
**Note:** `chown` gives ownership to azureuser (your account) and www-data (nginx group). `chmod 755` gives read+execute permission to nginx so it can read static files and access socket. Without this → 403 Forbidden errors.

---

## Architecture

```
User Browser
     ↓ HTTP port 80
   Nginx (web server)
     ↓ unix socket file
   Gunicorn (Python WSGI)
     ↓
   Django App
     ↓
   Azure PostgreSQL
   rentms-db-server.postgres.database.azure.com/rentms_db
```

---

## Update Code After Changes

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

## Useful Maintenance Commands

```bash
# View logs
sudo tail -f /var/log/nginx/error.log
sudo journalctl -u gunicorn -f

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# Check status
sudo systemctl status gunicorn
sudo systemctl status nginx

# Test locally on VM
curl http://localhost
```

---

## Credit Management Commands

```bash
# Save credits — run when done
az vm deallocate --resource-group rentms-rg --name rentms-vm
az postgres flexible-server stop --resource-group rentms-rg --name rentms-db-server

# Start again for demo
az vm start --resource-group rentms-rg --name rentms-vm
az postgres flexible-server start --resource-group rentms-rg --name rentms-db-server

# Check VM status
az vm show --resource-group rentms-rg --name rentms-vm --query "powerState"

# Check remaining credits
az consumption budget list
```

---

## Final Deployment Summary

```
Production (always live, free):
→ https://bikashgosain.com.np
→ Platform: Render.com
→ Database: Render PostgreSQL

Azure (demo/learning, uses credits):
→ http://20.24.85.96
→ http://rentms.eastasia.cloudapp.azure.com
→ Platform: Azure VM (Ubuntu 22.04)
→ Database: Azure PostgreSQL
→ Deallocate VM when not using to save credits
```

---

## CV Description

```
RentMS — Rent Management System
→ Built with Python, Django, PostgreSQL, Bootstrap 5
→ REST APIs with Django REST Framework + JWT Authentication
→ Deployed on Render.com (production) + Microsoft Azure VM
→ Domain: bikashgosain.com.np (SSL via Cloudflare)
→ Azure: VM + PostgreSQL + Nginx + Gunicorn
→ CI/CD: GitHub Actions
→ Features: OTP Email Verification, Google OAuth,
            Property Listing, Booking System,
            Complaint Management, Agreement System
```
