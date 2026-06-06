from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import onnxruntime as ort
import numpy as np
import os
from datetime import datetime
from google.cloud import storage

app = FastAPI(title="House Pricing Inference API - GCP Cloud Native")

# Configuración del entorno y almacenamiento centralizado
BUCKET_NAME = "house-pricing-mlops-artifacts-dev"
MODEL_BLOB_PATH = "models/model_house_pricing.onnx"
LOCAL_MODEL_PATH = "/tmp/model_house_pricing.onnx"

# Variables globales para el modelo
session = None
input_name = None

def download_model_from_gcs():
    """Descarga dinámicamente el modelo desde el Bucket de Google Cloud"""
    try:
        print(f"🔄 Conectando a GCP para descargar el modelo desde el bucket: {BUCKET_NAME}...")
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(MODEL_BLOB_PATH)
        
        # Guardar en la carpeta /tmp (estándar seguro para entornos serverless)
        blob.download_to_filename(LOCAL_MODEL_PATH)
        print("✅ Modelo ONNX descargado exitosamente en el entorno temporal.")
    except Exception as e:
        print(f"❌ Error crítico al descargar el modelo desde GCS: {e}")
        raise e

@app.on_event("startup")
def startup_event():
    """Este bloque se ejecuta automáticamente al encender el contenedor en la nube"""
    global session, input_name
    
    # Si estamos en local y el archivo ya existe, lo usa. Si no, lo descarga de GCP.
    if not os.path.exists(LOCAL_MODEL_PATH):
        if os.path.exists("model_house_pricing.onnx"):
            # Bypass para desarrollo local rápido
            blob_target = "model_house_pricing.onnx"
        else:
            download_model_from_gcs()
            blob_target = LOCAL_MODEL_PATH
    else:
        blob_target = LOCAL_MODEL_PATH

    try:
        session = ort.InferenceSession(blob_target)
        input_name = session.get_inputs()[0].name
        print("🚀 Sesión de inferencia ONNX inicializada correctamente.")
    except Exception as e:
        print(f"❌ No se pudo inicializar el modelo ONNX: {e}")

class HouseFeatures(BaseModel):
    metros_cuadrados: float
    habitaciones: float
    banos: float
    antiguedad: float

@app.get("/")
def read_root():
    return {
        "message": "API de Predicción de Viviendas - MLOps Universidad Icesi",
        "status": "online"
    }

@app.post("/predict")
def predict(features: HouseFeatures):
    if session is None:
        raise HTTPException(status_code=503, detail="Modelo no cargado en el servidor.")
    
    try:
        # 1. Preparar la matriz de entrada para el modelo ONNX
        input_data = np.array([[
            features.metros_cuadrados,
            features.habitaciones,
            features.banos,
            features.antiguedad
        ]], dtype=np.float32)
        
        # 2. Ejecutar la inferencia en tiempo real
        raw_prediction = session.run(None, {input_name: input_data})
        
        # CORRECCIÓN AQUÍ: Usamos .item() para extraer el valor numérico puro de forma segura
        prediction_val = raw_prediction[0].item()
        
        # 3. Observabilidad: Estructurar la traza del log
        log_line = (
            f"Timestamp: {datetime.now().isoformat()} | "
            f"Input: {features.dict()} | "
            f"Prediction: {prediction_val}\n"
        )
        
        # En entornos serverless guardamos el log local de manera temporal 
        # (Posteriormente se puede extender para subir paquetes de logs a la carpeta logs/)
        print(f"📊 [LOG TRACE]: {log_line.strip()}")
        
        return {
            "status": "success",
            "environment": os.getenv("ENVIRONMENT", "local"),
            "prediction": prediction_val
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante la inferencia: {str(e)}")