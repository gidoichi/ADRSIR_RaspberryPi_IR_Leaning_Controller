FROM python:3.14.1-alpine@sha256:b80c82b1a282283bd3e3cd3c6a4c895d56d1385879c8c82fa673e9eb4d6d4aa5
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN ln -sf /usr/local/bin/python3 /usr/bin/python3
RUN mkdir -p /home/pi/I2C0x52-IR/
COPY . .
