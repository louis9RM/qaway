FROM python:3.11-slim
WORKDIR /app/backend
# libs de sistema para rasterio/GDAL (COG remotos) y procesamiento
RUN apt-get update && apt-get install -y --no-install-recommends \
    libexpat1 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# El código (backend + módulo de datos) se monta en /app/sarvigia y /app/backend
EXPOSE 8100
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8100"]
