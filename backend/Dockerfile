# Imagen para correr Trackion en local (servidor HTTP que envuelve los handlers Lambda).
# NO es la imagen de despliegue en AWS (allá se usa Serverless Framework).
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY handler.py local_server.py ./
COPY app ./app

ENV PORT=8080
EXPOSE 8080

CMD ["python", "local_server.py"]
