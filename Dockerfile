FROM python:3.14.4-alpine@sha256:dd4d2bd5b53d9b25a51da13addf2be586beebd5387e289e798e4083d94ca837a
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN ln -sf /usr/local/bin/python3 /usr/bin/python3
RUN mkdir -p /home/pi/I2C0x52-IR/
COPY . .
