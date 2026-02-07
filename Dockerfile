FROM python:3.14.3-alpine@sha256:faee120f7885a06fcc9677922331391fa690d911c020abb9e8025ff3d908e510
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN ln -sf /usr/local/bin/python3 /usr/bin/python3
RUN mkdir -p /home/pi/I2C0x52-IR/
COPY . .
