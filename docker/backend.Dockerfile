FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y \
        build-essential \
        default-libmysqlclient-dev \
        default-mysql-client \
        pkg-config \
        curl \
        cron \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY city_care/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY city_care /app

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

CMD ["/entrypoint.sh"]
