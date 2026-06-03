from fastapi.testclient import TestClient
from app.main import app
import os

client = TestClient(app)

def test_read_home():
    """Valida que el endpoint raíz responda correctamente"""
    response = client.get("/")
    assert response.status_code == 200
    assert "API de Predicción de Viviendas" in response.json()["message"]

def test_predict_successful():
    """Prueba de consistencia: Valida que el modelo infiera un precio coherente"""
    # Solo corremos la prueba si el modelo local está presente para el test
    if os.path.exists("model_house_pricing.onnx"):
        payload = {
            "metros_cuadrados": 120.0,
            "habitaciones": 3.0,
            "banos": 2.0,
            "antiguedad": 5.0
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        # Umbral límite/Validación: El precio debe ser un número positivo mayor a 10 millones
        assert data["prediction"] > 10000000