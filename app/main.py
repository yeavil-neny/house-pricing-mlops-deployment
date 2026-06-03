import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import onnxruntime as rt
import numpy as np

app = FastAPI(
    title="House Pricing Inference API",
    description="API para la predicción de precios de vivienda usando ONNX Runtime",
    version="1.0.0"
)

# Definir el nombre del entorno según una variable del sistema (la configuraremos en Cloud Run)
ENV = os.getenv("ENVIRONMENT", "dev")
LOG_FILE = f"predicciones_{ENV}.txt"

# Intentar cargar el modelo ONNX de forma global al arrancar la API
# Nota: En local buscaremos el archivo en la raíz para probar, 
# pero en producción el pipeline lo inyectará automáticamente.
MODEL_PATH = "model_house_pricing.onnx"
session = None

if os.path.exists(MODEL_PATH):
    session = rt.InferenceSession(MODEL_PATH)
    print(f"✅ Modelo ONNX cargado exitosamente desde {MODEL_PATH}")
else:
    print(f"⚠️ Advertencia: No se encontró {MODEL_PATH}. La API iniciará, pero las predicciones fallarán hasta que el archivo esté presente.")

# Esquema de validación de datos de entrada (Pydantic)
class HouseFeatures(BaseModel):
    metros_cuadrados: float
    habitaciones: float
    banos: float
    antiguedad: float

@app.get("/")
def home():
    return {
        "message": f"API de Predicción de Viviendas corriendo en el entorno: [{ENV.upper()}]",
        "model_loaded": session is not None
    }

@app.post("/predict")
def predict(features: HouseFeatures):
    if session is None:
        raise HTTPException(status_code=503, detail="Modelo ONNX no disponible en el servidor.")
    
    try:
        # 1. Preparar los datos en el formato exacto que espera el ONNX ([None, 4])
        input_data = np.array([[
            features.metros_cuadrados,
            features.habitaciones,
            features.banos,
            features.antiguedad
        ]], dtype=np.float32)
        
        # 2. Correr la inferencia en ONNX Runtime
        # 'float_input' fue el nombre que le dimos a la entrada en la fábrica
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name
        
        prediction = session.run([output_name], {input_name: input_data})
        
        # CORRECCIÓN AQUÍ: Accedemos al elemento fila 0, columna 0 de la salida de ONNX
        precio_estimado = float(prediction[0][0][0])
        
        # 3. Formatear y registrar en el log local (Requisito de Observabilidad)
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] Features: {input_data.tolist()} -> Predicción: ${precio_estimado:,.2f}\n"
        
               
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)
            
        # 4. Retornar la respuesta al cliente
        return {
            "status": "success",
            "environment": ENV,
            "prediction": round(precio_estimado, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante la inferencia: {str(e)}")