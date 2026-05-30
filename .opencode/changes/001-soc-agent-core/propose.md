# Propuesta: Agente Inteligente SOC

**Estado:** Aprobada  
**Autor:** Juan Pablo Castañeda  
**Fecha:** 2026-05-20  

## ¿Qué problema resuelve?

Los equipos SOC (Security Operations Center) reciben cientos de eventos de seguridad por minuto. Clasificarlos manualmente es lento, propenso a errores y deja incidentes críticos sin atender. Se necesita un **agente automatizado** que:

1. Detecte anomalías en tiempo real sobre eventos de red/sistema
2. Correlacione eventos para encontrar patrones de ataque
3. Clasifique incidentes usando un LLM con contexto de incidentes históricos (RAG)
4. Genere recomendaciones accionables basadas en playbooks
5. Notifique al equipo SOC vía Telegram

## Alcance

### Incluye
- Backend FastAPI con PostgreSQL
- Motor de skills: correlación, detección de anomalías, clasificación, recomendación, notificación
- Integración con Ollama (LLM local) para análisis inteligente
- RAG con ChromaDB para recuperar incidentes históricos similares
- Simulador de eventos para prueba y validación
- Frontend React con dashboard en tiempo real
- Autenticación por riddle + verificación Telegram + JWT
- Despliegue con Docker Compose

### No incluye
- Integración con SIEM externo (Splunk, Elastic)
- Machine Learning entrenado específicamente (usa reglas + LLM)
- Despliegue en producción con HTTPS real y dominio
- WebSockets para actualizaciones en tiempo real (usa polling)

## Enfoque

Arquitectura basada en **skills** (Strategy Pattern): cada skill es un módulo independiente que implementa una tarea específica del dominio SOC. El agente orquesta los skills secuencialmente en cada ciclo de análisis. Stack: Python/FastAPI + React + PostgreSQL + Ollama + ChromaDB.
