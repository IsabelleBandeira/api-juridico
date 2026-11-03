FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONPATH=/app

# Instala o driver ODBC 18 da Microsoft
RUN apt-get update \
    && apt-get install -y curl gnupg2 unixodbc-dev gcc g++ \
    && curl -fsSL https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb \
       -o packages-microsoft-prod.deb \
    && dpkg -i packages-microsoft-prod.deb \
    && rm packages-microsoft-prod.deb \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY tests ./tests