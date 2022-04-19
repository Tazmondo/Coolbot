FROM python:3.9-slim
LABEL application=coolbot
WORKDIR /coolbot
COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD ["python", "setup.py"]
