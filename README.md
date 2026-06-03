# House Pricing MLOps Deployment (CD Pipeline): house-pricing-mlops-deployment

Sistema de despliegue automatizado (CI/CD) con GitHub Actions y Cloud Run para un modelo de predicción de precios de vivienda en formato ONNX. Este repositorio contiene el sistema de despliegue automático para la aplicación de predicción de precios de vivienda. El proyecto implementa un pipeline de Integración y Despliegue Continuo (CI/CD) que empaqueta la solución en un contenedor Docker y la despliega de forma serverless en la nube, asegurando entornos aislados de desarrollo y producción.

## Arquitectura del Sistema
El sistema está diseñado bajo el principio de desacoplamiento de artefactos:
1. **Modelo & Datos Externos:** El archivo del modelo (`model_house_pricing.onnx`) y los datos de prueba (`test_data.csv`) no residen en este repositorio; se extraen dinámicamente desde un almacenamiento en la nube (Bucket) durante la ejecución del pipeline.
2. **API de Servicio:** Construida sobre **FastAPI**, encargada de exponer el endpoint de predicción y cargar el modelo ONNX en memoria para resolver inferencias en tiempo real.
3. **Observabilidad:** Cada petición procesada por los endpoints escribe de forma persistente los registros de las predicciones en archivos de log (`.txt`) dentro del bucket para su posterior monitoreo.

## Estrategia de Ramas y Endpoints
El repositorio se organiza en dos ramas estables, cada una vinculada a un entorno e infraestructura independientes en la nube:

* **Rama `dev` (Desarrollo):** Dedicada a pruebas e integración de nuevas características de la aplicación o cambios estructurales del modelo.
  * *Endpoint asociado:* `https://<url-gcp-dev>/predict`
  * *Logs de monitoreo:* `predicciones_dev.txt`
* **Rama `prod` (Producción):** Entorno oficial y estable expuesto al usuario final o cliente.
  * *Endpoint asociado:* `https://<url-gcp-prod>/predict`
  * *Logs de monitoreo:* `predicciones_prod.txt`

## Pipeline de CI/CD (GitHub Actions)
Cualquier evento de `push` o `merge` en las ramas `dev` o `prod` activa de forma automática un flujo de trabajo distribuido en las siguientes etapas mínimas:

1. **Etapa de Test (Pruebas Unitarias y de Métricas):**
   * Descarga dinámica del modelo `.onnx` y el archivo `test_data.csv` desde el bucket.
   * Ejecución de pruebas de consistencia (validar que el modelo responda adecuadamente ante estímulos definidos).
   * Validación de degradación de rendimiento (comprobar mediante umbrales límite que el modelo no pierda precisión frente a una métrica establecida).
2. **Etapa de Build / Promote (Empaquetamiento y Despliegue):**
   * Construcción automatizada de la imagen utilizando el `Dockerfile`.
   * Inyección del modelo ONNX descargado dentro del contexto del contenedor.
   * Publicación de la imagen en el registro de contenedores de la nube.
   * Actualización del endpoint correspondiente (promoción del nuevo contenedor en Cloud Run).

## Estructura del Repositorio sugerida
* `.github/workflows/`: Archivos de configuración de GitHub Actions (`ci-cd.yml`).
* `app/`: Código fuente de la API de FastAPI (`main.py`, `schemas.py`, etc.).
* `tests/`: Scripts de pruebas unitarias y validación de umbrales de métricas.
* `Dockerfile`: Instrucciones de construcción del contenedor de la aplicación.
* `requirements.txt`: Dependencias del entorno de producción y ejecución.

## Stack Tecnológico
* **Framework API:** FastAPI / Uvicorn
* **Inferencia de IA:** ONNX Runtime
* **Contenedores:** Docker
* **CI/CD:** GitHub Actions
* **Proveedor Cloud (IaaS/PaaS):** Google Cloud Platform (GCP)
  * *Cloud Storage* (Almacenamiento de artefactos y logs)
  * *Artifact Registry* (Registro de imágenes Docker)
  * *Cloud Run* (Servicio de cómputo serverless para endpoints)
