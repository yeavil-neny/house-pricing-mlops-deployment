# 1. Usar una imagen base de Python oficial y liviana
FROM python:3.11-slim

# 2. Configurar variables de entorno para optimizar Python dentro del contenedor
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=dev

# 3. Establecer el directorio de trabajo dentro del contenedor
WORKDIR /code

# 4. Copiar e instalar las dependencias primero (aprovecha la caché de Docker)
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 5. Copiar el código de la aplicación y el modelo ONNX al contenedor
COPY ./app /code/app
COPY ./model_house_pricing.onnx /code/model_house_pricing.onnx

# 6. Exponer el puerto por defecto que usa Cloud Run (8080)
EXPOSE 8080

# 7. Comando para arrancar la API usando Uvicorn apuntando al puerto correcto
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]