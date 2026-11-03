# IAM — imagen del servicio propio, construida sobre el esqueleto común.
FROM python:3.12-slim

WORKDIR /app

COPY contracts/events /app/contracts/events
COPY services/common /app/services/common
COPY services/iam /app/services/iam

RUN pip install --no-cache-dir /app/services/common pyotp bcrypt pyrad httpx "uvicorn[standard]"

EXPOSE 8001

CMD ["uvicorn", "services.iam.main:app", "--host", "0.0.0.0", "--port", "8001"]
