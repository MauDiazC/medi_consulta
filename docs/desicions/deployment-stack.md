# Estrategia de Despliegue: Dev vs Producción

Para garantizar la paridad entre entornos y la alta disponibilidad en producción, se propone el siguiente stack de despliegue basado en contenedores y servicios gestionados.

## 1. Entorno de Desarrollo (Local/Dev)
El objetivo es la simplicidad y la velocidad de iteración.

- **Orquestación:** `docker-compose`. Permite levantar todo el ecosistema (API, Worker, DB, Redis) con un solo comando.
- **Servidores:** 
  - **API:** Uvicorn con `--reload` para hot-reloading.
  - **Base de Datos:** Imagen oficial de PostgreSQL en Docker.
  - **Cache/Events:** Imagen oficial de Redis en Docker.
- **Gestión de Paquetes:** `uv`. Es significativamente más rápido que pip/poetry y gestiona el entorno virtual de forma eficiente.

## 2. Entorno de Staging / Pruebas (PaaS Cloud)
Para pruebas en la nube con cuentas gratuitas o de bajo costo, se recomiendan plataformas que soporten procesos de larga duración (no Serverless).

- **Railway (Recomendado):** Ideal para este stack. Permite desplegar el API y el Worker como servicios independientes dentro del mismo proyecto, e incluye instancias de PostgreSQL y Redis integradas.
- **Digital Ocean (App Platform):** Excelente para un entorno de staging más cercano a producción. Ofrece una base de datos gestionada muy confiable.
- **⚠️ Nota sobre Vercel:** No se recomienda para este backend. Vercel utiliza Serverless Functions que tienen límites de tiempo (timeouts) y no permiten procesos en segundo plano (Workers) ni conexiones persistentes de larga duración necesarias para SSE/WebSockets.

## 3. Entorno de Producción (Cloud Native)
El objetivo es la escalabilidad, seguridad y alta disponibilidad.

### Infraestructura (AWS/GCP/Azure)
- **Orquestación de Contenedores:** **Kubernetes (EKS/GKE)** o **AWS ECS (Fargate)**.
  - Se deben separar los servicios en pods/tareas independientes: `api-service` y `worker-service`.
  - Escalamiento horizontal automático (HPA) basado en uso de CPU o longitud de cola en Redis.
- **Base de Datos Gestionada:** **AWS RDS (PostgreSQL)**.
  - Configuración **Multi-AZ** para replicación y failover automático.
  - Backups diarios automatizados y cifrado en reposo (AES-256).
- **Cache y Mensajería:** **AWS ElastiCache (Redis)**.
  - Configuración de Cluster/Replication Group para evitar puntos únicos de fallo.
- **Almacenamiento de Archivos:** **AWS S3**.
  - Para documentos clínicos, firmas y snapshots PDF, con políticas de acceso restringido (Presigned URLs).

### Red y Seguridad
- **Balanceador de Carga:** Application Load Balancer (ALB) con terminación SSL (TLS 1.2+).
- **CDN / WAF:** CloudFront y AWS WAF para protección contra ataques DDoS y SQL Injection.
- **Secretos:** **AWS Secrets Manager** o **HashiCorp Vault** para inyectar credenciales en tiempo de ejecución (nunca en archivos `.env`).

## 3. Estrategia de CI/CD
- **GitHub Actions:** Pipeline automatizada que:
  1. Ejecuta tests unitarios e integración.
  2. Realiza el build de la imagen Docker.
  3. Escanea la imagen en busca de vulnerabilidades.
  4. Despliega en el cluster usando **ArgoCD** o **Terraform** (Infrastructure as Code).
