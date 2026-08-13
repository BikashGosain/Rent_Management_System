# 1. Clone the repo
git clone https://github.com/BikashGosain/rent_management.git
cd rent_management

# 2. Copy .env
cp .env.example .env
# Edit .env — only needs to change SECRET_KEY
# DB settings already match docker-compose.yml

# 3. Build and run
docker-compose up --build

# 4. Open browser
# http://localhost:8000

# 5. (First time only) Create superuser
docker-compose exec web python manage.py createsuperuser

# 6. (Optional) Load sample data
docker-compose exec web python manage.py load_sample_data

<!-- To stop: -->

docker-compose down

<!-- To stop and delete all data: -->

docker-compose down -v

<!-- Start again -->
docker compose up -d




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