FROM python:3.12-slim
LABEL authors="m t"

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY /requirements.txt /app/requirements.txt
RUN pip install --no-caсhe-dir -r requirements.txt

copy . /app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
