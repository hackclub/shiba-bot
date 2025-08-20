FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

HEALTHCHECK CMD pgrep -f app.py || exit 1

CMD ["python", "app.py"]
