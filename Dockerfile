FROM python:3.13.4-bookworm
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN ln -sf /usr/local/bin/python3 /usr/bin/python3
RUN mkdir -p /home/pi/I2C0x52-IR/
COPY . .
