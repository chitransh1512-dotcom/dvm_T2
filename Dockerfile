FROM python:3.13-slim

# Prevent Python from writing pyc files & buffer logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Start Gunicorn
CMD ["gunicorn", "metro_project.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60"]

