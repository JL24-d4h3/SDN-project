# Policies — imagen del servicio propio, construida sobre el esqueleto común.
FROM python:3.12-slim

WORKDIR /app

COPY contracts/events /app/contracts/events
COPY policy /app/policy
COPY services/common /app/services/common
COPY services/policies /app/services/policies

RUN pip install --no-cache-dir /app/services/common httpx "uvicorn[standard]"

EXPOSE 8006

CMD ["uvicorn", "services.policies.main:app", "--host", "0.0.0.0", "--port", "8006"]
