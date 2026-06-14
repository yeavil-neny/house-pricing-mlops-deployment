## Integrantes del Proyecto

El desarrollo, diseño de arquitectura MLOps e implementación de este ecosistema automatizado fue realizado por:

* **Yenny Alexandra Villarreal Suaza** — *Ingeniera de Sistemas / MLOps & Cloud Infrastructure*
* **Cristian Humberto Yepes Marín** — *Ingeniero de Sistemas / Data & ML Engineer*

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

```text
