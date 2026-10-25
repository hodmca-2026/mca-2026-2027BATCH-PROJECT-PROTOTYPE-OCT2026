FROM python:3.11-slim

WORKDIR /app

# System deps: libgl1/libglib for opencv, unixodbc for pyodbc (SQL Server)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    unixodbc \
    unixodbc-dev \
    curl gnupg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ml/ (training scripts + trained model) is mounted/copied in via docker-compose
# so the backend can import train.py/gradcam.py and load best_model.pth
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["sh", "-c", "python seed_db.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
