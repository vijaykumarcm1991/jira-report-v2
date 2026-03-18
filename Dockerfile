FROM python:3.11-slim

ENV TZ=Asia/Kolkata

RUN apt-get update && apt-get install -y tzdata && \
    ln -fs /usr/share/zoneinfo/Asia/Kolkata /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "python wait_for_db.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]