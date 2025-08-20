FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# install dependencies
COPY requirements.txt .
RUN apt-get update && apt-get install -y curl && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# copy app
COPY . .

HEALTHCHECK CMD exit 0

# start the app
CMD ["python", "app.py"]
