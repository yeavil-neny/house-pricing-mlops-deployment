import pytest
import pandas as pd
import numpy as np
import onnxruntime as ort
import os

LOCAL_DATA_PATH = "/tmp/test_data.csv"
LOCAL_MODEL_PATH = "/tmp/model_house_pricing.onnx"

def test_artifacts_exist():
    """Verifica que el pipeline descargó los artefactos correctamente desde GCS"""
    assert os.path.exists(LOCAL_DATA_PATH), "Los datos de prueba no fueron descargados."
    assert os.path.exists(LOCAL_MODEL_PATH), "El modelo ONNX no fue descargado."

def test_model_inference_structure():
    """Punto 1 del profesor: Probar que el modelo responde con datos de entrada definidos"""
    session = ort.InferenceSession(LOCAL_MODEL_PATH)
    input_name = session.get_inputs()[0].name
    
    # Datos de entrada definidos (un registro de prueba)
    input_data = np.array([[100.0, 3.0, 2.0, 10.0]], dtype=np.float32)
    prediction = session.run(None, {input_name: input_data})
    
    assert prediction is not None
    assert isinstance(prediction[0], np.ndarray)
    assert prediction[0].shape == (1, 1)

def test_model_metric_threshold():
    """Punto 2 del profesor: Probar que no existe un cambio significativo en una métrica (Umbral de Calidad)"""
    session = ort.InferenceSession(LOCAL_MODEL_PATH)
    input_name = session.get_inputs()[0].name
    
    # Leer los datos que el pipeline descargó dinámicamente desde el Bucket
    df = pd.read_csv(LOCAL_DATA_PATH)
    
    X_test = df[['metros_cuadrados', 'habitaciones', 'banos', 'antiguedad']].values.astype(np.float32)
    y_true = df['precio_real'].values
    
    predictions = []
    for row in X_test:
        pred = session.run(None, {input_name: np.array([row])})
        predictions.append(pred[0].item())
        
    # Calcular una métrica básica (ejemplo: RMSE o desviación máxima)
    predictions = np.array(predictions)
    mae = np.mean(np.abs(predictions - y_true))
    
    # Definir el umbral límite exigido por la rúbrica (ejemplo: MAE menor a 50 millones)
    UMBRAL_MAXIMO_ERROR = 50000000
    
    assert mae < UBRAL_MAXIMO_ERROR, f"La métrica de calidad falló: MAE actual {mae} supera el límite {UMBRAL_MAXIMO_ERROR}"