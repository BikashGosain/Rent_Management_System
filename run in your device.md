1. Install Docker Desktop

Download and install Docker Desktop for Windows from the official Docker website: Choose this

Windows – AMD64 → ✅

Docker Desktop for Windows

During installation, keep the recommended WSL 2 option if offered.

2. Start Docker Desktop

After installation:

Open Docker Desktop from the Start menu.
Wait until Docker says it is running/ready.
Close your current CMD window.
Open a new CMD or PowerShell window.

This last step is important because the installer adds Docker to your PATH.

3. Check Docker

Run:

docker --version

Then:

docker compose version

You should get something similar to:

Docker version ...
Docker Compose version ...
4. Go back to your project
cd ""

Then:

docker compose up --build


# 1. Clone the repo
git clone https://github.com/BikashGosain/Rent_Management_System.git
cd Rent_Management_System

Check:

ls

You should see something like:

apps
config
csv_data
Dockerfile
docker-compose.yml
entrypoint.sh
manage.py
requirements.txt
...

4. Check Docker
docker --version

Then:

docker compose version

You should get versions similar to:

Docker version ...
Docker Compose version ...

# 2. Copy .env
cp .env.example .env
# Edit .env — only needs to change SECRET_KEY
# DB settings already match docker-compose.yml

# 3. Build and run
docker compose up --build

You should see:

==> Running migrations...

then:

==> Collecting static files...

then:

==> Starting server...

and finally:

Starting development server at http://0.0.0.0:8000/
Don't close this terminal.

<!-- Open another terminal -->

Keep the first terminal running.

Open another SSH/terminal session and go to:

cd Rent_Management_System

Check:

docker compose ps

You should see:

rent_management_system-web-1    Up

and:

0.0.0.0:8000->8000/tcp

<!-- Find your VM IP -->
hostname -I
or
ipconfig

For example:

192.168.203.132

Then from your Windows browser:

http://192.168.203.132:8000

# 4. Open browser
# http://localhost:8000

# 5. (First time only) Create superuser
docker compose exec web python manage.py createsuperuser

# 6. (Optional) Load sample data
docker compose exec web python manage.py load_sample_data

<!-- Check logs -->

If the website doesn't open:

docker compose logs -f web

You want to see:

Starting development server at http://0.0.0.0:8000/

And when you open the website:

"GET / HTTP/1.1" 200

That 200 means the request succeeded.

<!-- To stop application: -->
If docker compose up is running:

CTRL + C

Or from another terminal:
docker-compose down

<!-- To stop and delete all data: -->

docker-compose down -v

<!-- Start again -->
docker compose up -d

<!-- Check status -->
docker compose ps
<!-- See logs -->
docker compose logs -f web



Docker provides the isolated Python environment inside the web container.

Without Docker

They would need:

Python
   ↓
create venv
   ↓
activate venv
   ↓
pip install -r requirements.txt
   ↓
install/configure PostgreSQL
   ↓
configure .env
   ↓
python manage.py runserver
With your Docker setup

They need roughly:

Docker Desktop
      ↓
git clone
      ↓
create .env
      ↓
docker compose up --build
      ↓
Django + Python + dependencies + PostgreSQL
      ↓
localhost:8000

Your Dockerfile should install the Python dependencies, for example:

FROM python:3.14

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

So the Python environment is inside Docker, not on their Windows machine.

What about your existing venv?

You can keep your local:

venv/

for development if you want to run:

python manage.py runserver

directly on Windows.

But do not commit it to GitHub:

venv/

And when someone downloads your project, they don't need your venv/.

One important distinction

If they want to run:

python manage.py runserver

directly on their computer, then yes, they need Python + a virtual environment + dependencies.

If they run:

docker compose up --build

then no local venv is required.

For your Dockerized project, I'd recommend documenting Docker as the primary setup method in your README.



<!-- ⭐ Fresh setup — shortest version -->

Once you've done the configuration correctly, the normal fresh-server procedure is:

cd ~/Djangp_Project
git clone https://github.com/BikashGosain/rent_management.git
cd rent_management
cp .env.example .env
nano .env
chmod +x entrypoint.sh
docker compose down -v
docker compose build --no-cache
docker compose up -d
docker compose ps
docker compose logs -f web

Then create the admin:

docker compose exec web python manage.py createsuperuser

Then load sample data:

docker compose exec web python manage.py load_sample_data

Finally:

hostname -I

and open:

http://YOUR_VM_IP:8000