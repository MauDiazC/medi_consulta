# Estrategia de Crecimiento y Escalabilidad

El stack actual soporta miles de usuarios concurrentes en un modelo modular (Monolito Modular). Sin embargo, existen puntos de inflexión donde se debe evaluar un cambio.

## 1. ¿Cuándo Evaluar Cambios?
- **Carga de Escritura Masiva:** Si PostgreSQL llega al límite de IOPS a pesar del escalado vertical.
- **Orquestación Compleja:** Si la lógica de eventos entre módulos se vuelve inmanejable y genera cuellos de botella en Redis.
- **Microservicios Reales:** Cuando los equipos de desarrollo crecen y necesitan desplegar módulos de forma independiente (ej: el motor de Dictado o IA).

## 2. Transición de Tecnologías (Roadmap)
- **Bases de Datos Especializadas:** 
  - Pasar de PostgreSQL a bases vectoriales dedicadas (Qdrant, Pinecone) para el RAG.
  - Implementar TimescaleDB para análisis históricos de la Timeline.
- **Lenguajes de Bajo Nivel:**
  - Migrar servicios críticos (como el pipeline de criptografía o streaming de audio) a **Go** o **Rust** si el uso de CPU en Python se vuelve ineficiente.
- **Broker de Mensajería:**
  - Si el volumen de eventos es masivo, reemplazar Redis por **Kafka** o **RabbitMQ** para asegurar la persistencia y ordenamiento estricto de eventos clínicos.

## 3. Estrategia de Despliegue
- El primer paso hacia la escalabilidad masiva es separar el `app/worker` y el `app/api` en pods de Kubernetes independientes con auto-escalado (HPA).
