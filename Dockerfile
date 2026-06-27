FROM python:3.14.6-alpine@sha256:26730869004e2b9c4b9ad09cab8625e81d256d1ce97e72df5520e806b1709f92
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN ln -sf /usr/local/bin/python3 /usr/bin/python3
RUN mkdir -p /home/pi/I2C0x52-IR/
COPY . .
