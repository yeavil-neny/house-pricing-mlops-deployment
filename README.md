## Integrantes del Proyecto

El desarrollo, diseño de arquitectura MLOps e implementación de este ecosistema automatizado fue realizado por:

* **Yenny Alexandra Villarreal Suaza** — *cod. A00417016*
* **Cristian Humberto Yepes Marín** — *cod. A00417015*

---


# Proyecto Final MLOps - House Pricing MLOps Deployment (CD Pipeline)

Sistema de despliegue automatizado corporativo (CI/CD) basado en GitOps utilizando **GitHub Actions** y **Google Cloud Run** para un modelo de predicción de precios de vivienda optimizado en formato **ONNX**. 

Este repositorio contiene el sistema de despliegue automático para la aplicación de predicción de precios de vivienda. El proyecto implementa un pipeline de Integración y Despliegue Continuo (CI/CD) que empaqueta la solución de forma agnóstica en un contenedor Docker y la despliega de forma serverless en la nube, asegurando entornos aislados de desarrollo y producción.

---


## Arquitectura del Sistema y Desacoplamiento

El sistema está diseñado bajo el principio de desacoplamiento de artefactos: **separación estricta de código y artefactos de datos**

* **Desacoplamiento de Artefactos:** Ni el archivo binario del modelo (`model_house_pricing.onnx`) ni los datos de prueba (`test_data.csv`) residen en este repositorio de código. Se extraen en tiempo de ejecución de manera segura desde un almacenamiento en la nube (Bucket) de Google Cloud Storage.
* **API de Servicio:** Desarrollado con **FastAPI** y **Uvicorn**, exponiendo endpoints REST autodeclarativos y cargando la sesión de predicción optimizada con `onnxruntime` a través del modelo ONNX en memoria para resolver inferencias en tiempo real.
* **Observabilidad (Auditoría):** Cada petición procesada por los endpoints escribe de forma persistente los registros de las predicciones en archivos de log (`.txt`) dentro del bucket para su posterior monitoreo, auditoría y evaluación de data drift.

  > 📌 **Nota de Arquitectura del Ecosistema MLOps:** El diseño del sistema se fundamenta en el **desacoplamiento total entre el ciclo de vida del modelo y el ciclo de vida de la aplicación de inferencia**, distribuyéndose en dos repositorios independientes:
  > 1. **`house-pricing-ml-pipeline`**: Repositorio de Ingeniería de Datos y Modelamiento. Contiene el código de generación de datos sintéticos (`generate_data.py`), entrenamiento (`train.py`) y la exportación del artefacto final en formato abierto ONNX (`model_house_pricing.onnx`) con un rendimiento validado de $R^2 = 0.97$.
  > 2. **`house-pricing-mlops-deployment`** *(Este repositorio)*: Repositorio de despliegue y servicio enfocado en la infraestructura y la API de inferencia en tiempo real.

  <img width="1024" height="559" alt="image" src="https://github.com/user-attachments/assets/6b53007b-9c30-4127-a7b5-5375d9bb8088" />


## Estrategia de Ramas y Endpoints
El repositorio se organiza en dos ramas estables, cada una vinculada a un entorno e infraestructura independientes en la nube:

* **Rama `dev` (Desarrollo):** Dedicada a pruebas e integración de nuevas características de la aplicación o cambios estructurales del modelo.
  * *Endpoint asociado:* `https://<url-gcp-dev>/predict`
  * *Logs de monitoreo:* `predicciones_dev.txt`
* **Rama `prod` (Producción):** Entorno oficial y estable expuesto al usuario final o cliente.
  * *Endpoint asociado:* `https://<url-gcp-prod>/predict`
  * *Logs de monitoreo:* `predicciones_prod.txt`


## Pipeline de CI/CD (GitHub Actions)

Tanto el archivo `.github/workflows/ci-cd.yml` (para desarrollo) como `.github/workflows/production.yml` (para producción) estructuran un flujo automatizado compuesto por dos etapas críticas:

### 1. Etapa de Test (Pruebas Unitarias y Validación de Umbrales)
* **Descarga Dinámica:** El pipeline se conecta mediante políticas IAM seguras a Cloud Storage y descarga en caliente el modelo de producción (`model_house_pricing.onnx`) y el set de datos de validación cruzada (`test_data.csv`).
* **Validación de Consistencia (`pytest`):** Se ejecutan las pruebas unitarias contenidas en `tests/test_main.py` para asegurar que el contrato de entrada y salida de la API de FastAPI se mantenga intacto.
* **Control de Degradación (Performance Gating):** Se evalúan las métricas del modelo frente al conjunto de prueba dinámico para confirmar que el artefacto no experimente degradación de rendimiento por debajo de los umbrales corporativos establecidos antes de autorizar el empaquetado.

### 2. Etapa de Build & Promote (Empaquetamiento y Despliegue)
* **Construcción Agnóstica:** El `Dockerfile` compila el entorno de Python 3.11 de forma optimizada y limpia. El modelo ONNX se integra en el contexto local.
* **Versionamiento Inmutable:** La imagen resultante es etiquetada con el código único del commit (`$COMMIT_SHA`) y la etiqueta del entorno, garantizando la trazabilidad absoluta del software.
* **Despliegue Serverless:** Se realiza la promoción automática hacia Google Cloud Run de manera transparente y sin tiempo de inactividad (*Zero-Downtime Deployment*).


## Stack Tecnológico
* **Framework API:** FastAPI / Uvicorn
* **Inferencia de IA:** ONNX Runtime
* **Contenedores:** Docker
* **CI/CD:** GitHub Actions
* **Proveedor Cloud (IaaS/PaaS):** Google Cloud Platform (GCP)
  * *Cloud Storage* (Almacenamiento de artefactos y logs)
  * *Artifact Registry* (Registro de imágenes Docker)
  * *Cloud Run* (Servicio de cómputo serverless para endpoints)
 

## Alineación con Estándares de la Industria (Twelve-Factor App)

Para asegurar un diseño robusto y escalable, la solución implementa los siguientes factores de diseño:

* **I. Código Base (Codebase):** Un único repositorio rastreado en control de versiones para el despliegue, mapeado hacia múltiples entornos mediante estrategias de ramificación eficientes (`dev` y `main`).
* **II. Configuraciones (Config):** La aplicación no almacena credenciales ni rutas estáticas en código duro. El entorno (`ENVIRONMENT`) se inyecta dinámicamente en tiempo de ejecución en Cloud Run, y la autenticación perimetral se resuelve de forma segura mediante claves efímeras con *Workload Identity Federation* en GitHub Actions, eliminando el uso de archivos JSON de claves de GCP.
* **III. Construcción, Distribución, Ejecución (Build, Release, Run):** Separación estricta del flujo. El pipeline de GitHub genera una fase de construcción (*Build*) inmutable mediante Docker, la empaqueta de forma versionada usando el `COMMIT_SHA` en Artifact Registry (*Release*) y la ejecuta de forma serverless en Cloud Run (*Run*).
* **IV. Procesos (Process):** La API de inferencia se comporta como un proceso sin estado (*stateless*). No retiene datos locales en el contenedor, permitiendo el auto-escalado horizontal inmediato de Google Cloud Run desde 0 hasta N instancias según la demanda de peticiones.
* **V. Historiales de ejecución (Logs):** Los logs de la aplicación son tratados como flujos de eventos continuos. Cada inferencia se procesa y se escribe de forma desacoplada y persistente en archivos de auditoría (`predicciones_dev.txt` y `predicciones_prod.txt`) directamente sobre Google Cloud Storage para habilitar la trazabilidad y detectar posibles derivas de datos (*Data Drift*).


---
## Estructura del Repositorio Real

```text
house-pricing-mlops-deployment/
├── .github/
│   └── workflows/
│       ├── ci-cd.yml          # Pipeline de Integración/Despliegue para entorno DEV
│       └── production.yml      # Pipeline de Integración/Despliegue para entorno PROD
├── app/
│   ├── __init__.py            # Inicializador del módulo de la API
│   └── main.py                # Núcleo de la API (FastAPI, ONNX Runtime y exportación de Logs)
├── tests/
│   └── test_main.py           # Suite de pruebas automatizadas y chequeo de regresión
├── .gitignore                 # Archivos y directorios excluidos del control de versiones
├── Dockerfile                 # Receta de empaquetamiento del contenedor de producción
├── LICENSE                    # Licencia del proyecto
├── README.md                  # Documentación técnica del sistema
└── requirements.txt           # Dependencias estrictas del entorno de ejecución
```


## Guía de Onboarding (Ejecución del Proyecto)

Esta sección describe los pasos necesarios para clonar, configurar y ejecutar la API de inferencia tanto en un entorno local de desarrollo como en la infraestructura serverless de la nube.

### Prerrequisitos Mínimos
* **Python 3.11** instalado localmente.
* **Docker Desktop** activo (para pruebas de contenedores).
* **Google Cloud SDK (gcloud CLI)** instalado e inicializado.
* Cuenta de servicio con permisos sobre los buckets de GCP (`Storage Object Viewer` y `Storage Object Creator`).

---

### 1. Ejecución en Entorno Local (Desarrollo)

Para realizar pruebas ágiles, depuración de código o flujos offline, sigue estos pasos:

#### Paso 1.1: Clonar el repositorio y preparar el entorno
```bash
# Clonar el proyecto de despliegue
git clone [https://github.com/tu-usuario/house-pricing-mlops-deployment.git](https://github.com/tu-usuario/house-pricing-mlops-deployment.git)
cd house-pricing-mlops-deployment

# Crear y activar un entorno virtual de Python
python -m venv venv
source venv/bin/activate  # En Windows usa: venv\Scripts\activate

# Instalar las dependencias del proyecto
pip install -r requirements.txt
```

#### Paso 1.2: Ubicar el artefacto del modelo
Para desarrollo offline local, el script app/main.py cuenta con un mecanismo de fallback inteligente. Coloca una copia del archivo del modelo en la raíz del repositorio:
```bash
Ruta: ./model_house_pricing.onnx
```

#### Paso 1.3: Lanzar el servidor de FastAPI
Ejecuta el servidor web asíncronamente a través de Uvicorn inyectando la variable de entorno de desarrollo:
```bash
export ENVIRONMENT=dev
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Paso 1.4: Probar la suite de pruebas unitarias localmente
```bash
export PYTHONPATH="."
pytest tests/test_main.py
```
---

### 2. Ejecución Local empaquetada con Docker
Si deseas certificar el comportamiento exacto del contenedor antes de subirlo al registro de la nube:
```bash
# 1. Construir la imagen Docker local
docker build -t house-pricing-api:local .

# 2. Correr el contenedor mapeando los puertos y pasando las credenciales de GCP
docker run -p 8080:8080 \
  -e ENVIRONMENT=dev \
  -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/gcp-key.json \
  -v ~/.config/gcloud:/tmp/keys \
  house-pricing-api:local
```
  - Acceso local por contenedor: `http://localhost:8080/docs`

### 3. Ejecución y Despliegue en la Nube (Google Cloud Platform)
El despliegue en la nube está completamente automatizado a través de GitOps con GitHub Actions, por lo que no requiere comandos manuales repetitivos en producción. El flujo operativo se gestiona de la siguiente manera:

#### Flujo de Promoción a Desarrollo (Ambiente DEV)
  1. Realiza tus modificaciones de código en tu máquina local.
  2. Envía los cambios a la rama de desarrollo:
      ```bash
      git add .
      git commit -m "feat: optimización de lógica de logs"
      git push origin dev
      ```
  3. El pipeline: `.github/workflows/ci-cd.yml` se activará automáticamente:
     - Descargará el modelo desde `gs://house-pricing-mlops-artifacts-dev/.`
     - Ejecutará `pytest`.
     - Compilará la imagen y la enviará a **Artifact Registry**.
     - Actualizará de forma serverless el servicio **Cloud Run** (`house-pricing-api-dev`).


#### Flujo de Promoción a Producción (Ambiente PROD)
  - Una vez que el entorno de desarrollo se encuentre estable y verificado, se realiza la promoción a producción mediante la fusión hacia la rama principal:
  
      ```bash      
      # Cambiar a la rama principal y sincronizar
      git checkout main
      git pull origin main
      ```
      ```bash 
      # Fusionar los cambios aprobados desde desarrollo
      git merge dev
      ```
      ```bash 
      # Disparar el pipeline de producción en la nube
      git push origin main
      ```
    
  4. El pipeline: `.github/workflows/production.yml` tomará el control de forma aislada:
     - Descargará los artefactos oficiales desde el bucket de producción `gs://house-pricing-mlops-artifacts-prod/.`
     - Correrá los umbrales de validación sobre el conjunto de pruebas dinámico `test_data.csv`.
     - Empaquetará la imagen inmutable inyectando el código del ```COMMIT_SHA```.
     - Actualizará el endpoint productivo en **Cloud Run** (`house-pricing-api-prod`) inyectando de forma inmutable la variable de entorno `ENVIRONMENT=prod`.
     - A partir de ese momento, cada inferencia del usuario final quedará registrada de forma persistente en `gs://house-pricing-mlops-artifacts-prod/logs/predicciones_prod.txt`.
