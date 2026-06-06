import pytest
import pandas as pd
import numpy as np
import onnxruntime as ort
import os

LOCAL_DATA_PATH = "./test_data.csv"
LOCAL_MODEL_PATH = "./model_house_pricing.onnx"

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
    # 1. Cargar el dataset de prueba descargado por el pipeline
    data = pd.read_csv("./test_data.csv")
    
    # 2. RECONSTRUCCIÓN LÓGICA DEL TARGET (Precio Real)
    # Replicamos la fórmula matemática exacta del script de generación
    # para inyectar la columna 'precio_real' de manera dinámica:
    base_vivienda = 40_000_000
    componente_m2 = data['metros_cuadrados'] * 2_500_000
    componente_hab = data['habitaciones'] * 15_000_000
    componente_banos = data['banos'] * 20_000_000
    componente_antiguedad = data['antiguedad'] * 3_000_000
    
    # Reconstruimos el precio base sin el ruido aleatorio (o el valor esperado teórico)
    # que sirve perfectamente como ground-truth para validar el umbral del modelo.
    data['precio_real'] = base_vivienda + componente_m2 + componente_hab + componente_banos - componente_antiguedad
    
    # 3. Preparar los datos para el modelo ONNX
    # Asegúrate de que las columnas vayan en el orden exacto que requiere tu modelo
    X_test = data[['metros_cuadrados', 'habitaciones', 'banos', 'antiguedad']].values.astype(np.float32)
    
    # 4. Ejecutar la inferencia con el Modelo ONNX descargado
    sess = ort.InferenceSession("./model_house_pricing.onnx")
    input_name = sess.get_inputs()[0].name
    label_name = sess.get_outputs()[0].name
    predicciones = sess.run([label_name], {input_name: X_test})[0]
    
    # Aplanamos las predicciones en caso de que vengan en formato bidimensional
    y_pred = predicciones.flatten()
    y_true = data['precio_real'].values
    
    # 5. Calcular la métrica de calidad (Mean Absolute Error - MAE)
    mae = np.mean(np.abs(y_true - y_pred))
    print(f"\n[CALIDAD MLOPS] El MAE calculado del modelo es: ${mae:,.2f} COP")
    
    # 6. Verificación del Umbral (Ajusta el límite según los requerimientos de tu proyecto)
    # Por ejemplo, garantizar que el error promedio sea menor a 25 millones de pesos
    umbral_maximo = 25_000_000
    assert mae < umbral_maximo, f"El MAE del modelo (${mae:,.2f}) supera el umbral permitido (${umbral_maximo:,.2f})"