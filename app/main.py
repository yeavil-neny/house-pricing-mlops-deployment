from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import onnxruntime as ort
import numpy as np
import os
from datetime import datetime
from google.cloud import storage


# Configuración del entorno de manera dinámica (Twelve-Factor App)
# Leer el entorno (por defecto 'dev' si no está definido)
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev").lower()

# Título dinámico para diferenciar los ambientes en /docs
APP_TITLE = f"House Pricing Inference API - MLOps ({ENVIRONMENT.upper()})"
app = FastAPI(title=APP_TITLE)

# Construcción dinámica y agnóstica de infraestructura de almacenamiento (Twelve-Factor App)
# Si ENVIRONMENT='dev' -> gs://house-pricing-mlops-artifacts-dev
# Si ENVIRONMENT='prod' -> gs://house-pricing-mlops-artifacts-prod
BUCKET_NAME = os.getenv("BUCKET_NAME", f"house-pricing-mlops-artifacts-{ENVIRONMENT}")
MODEL_BLOB_PATH = "models/model_house_pricing.onnx"
LOCAL_MODEL_PATH = "/tmp/model_house_pricing.onnx"

# Nombre dinámico del archivo de logs exigido
# Dev: logs/predicciones_dev.txt | Prod: logs/predicciones_prod.txt
LOG_BLOB_PATH = f"logs/predicciones_{ENVIRONMENT}.txt"

session = None
input_name = None

def download_model_from_gcs():
    """Descarga el modelo ONNX real desde el bucket dinámico en tiempo de ejecución"""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(MODEL_BLOB_PATH)
        
        # Asegurar que el directorio temporal /tmp exista (buena práctica en serverless)
        os.makedirs(os.path.dirname(LOCAL_MODEL_PATH), exist_ok=True)
        
        blob.download_to_filename(LOCAL_MODEL_PATH)
        print(f"✅ Modelo ONNX descargado exitosamente de GCS desde el bucket: {BUCKET_NAME}")
    except Exception as e:
        print(f"❌ Error descargando modelo del bucket {BUCKET_NAME}: {e}")
        raise e

def append_log_to_gcs(log_entry: str):
    """Agrega una nueva línea de predicción al archivo TXT correspondiente en el bucket"""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(LOG_BLOB_PATH)
        
        # Descargar contenido existente si ya existe, para no borrar el historial
        existing_content = ""
        if blob.exists():
            existing_content = blob.download_as_text()
        
        # Concatenar la nueva predicción
        new_content = existing_content + log_entry
        blob.upload_from_string(new_content, content_type="text/plain")
    except Exception as e:
        print(f"⚠️ No se pudo guardar el log en GCS (Error de observabilidad): {e}")

@app.on_event("startup")
def startup_event():
    global session, input_name
    
    # En Cloud Run (producción/desarrollo en la nube), forzamos la descarga desde el Bucket
    # En entorno local, si el archivo ya existe en la raíz, lo usa para agilizar pruebas
    if not os.path.exists(LOCAL_MODEL_PATH):
        if os.path.exists("model_house_pricing.onnx") and os.getenv("K_SERVICE") is None:
            # K_SERVICE es una variable automática que Cloud Run inyecta. Si no existe, estamos local.
            blob_target = "model_house_pricing.onnx"
            print("🏠 Usando modelo ONNX local para desarrollo offline.")
        else:
            download_model_from_gcs()
            blob_target = LOCAL_MODEL_PATH
    else:
        blob_target = LOCAL_MODEL_PATH

    try:
        session = ort.InferenceSession(blob_target)
        input_name = session.get_inputs()[0].name
        print(f"🚀 Sesión de inferencia inicializada con éxito para ambiente: {ENVIRONMENT.upper()}.")
    except Exception as e:
        print(f"❌ Error al inicializar ONNX: {e}")

class HouseFeatures(BaseModel):
    metros_cuadrados: float
    habitaciones: float
    banos: float
    antiguedad: float

@app.post("/predict")
def predict(features: HouseFeatures):
    if session is None:
        raise HTTPException(status_code=503, detail="Modelo no disponible.")
    
    try:
        input_data = np.array([[
            features.metros_cuadrados,
            features.habitaciones,
            features.banos,
            features.antiguedad
        ]], dtype=np.float32)
        
        raw_prediction = session.run(None, {input_name: input_data})
        prediction_val = raw_prediction[0].item()
        
        # Estructurar la línea del log exigida para monitoreo
        log_line = f"{datetime.now().isoformat()} | Input: {features.dict()} | Prediction: {prediction_val}\n"
        
        # Guardar de forma persistente en el Bucket correspondiente (dev o prod)
        append_log_to_gcs(log_line)
        
        return {
            "status": "success",
            "environment": ENVIRONMENT,
            "prediction": prediction_val
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))