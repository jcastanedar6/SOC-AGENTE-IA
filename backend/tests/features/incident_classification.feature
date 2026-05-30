Feature: Clasificación de incidentes
  El skill IncidentClassification debe clasificar anomalías
  usando el LLM (con contexto RAG) o un fallback rule-based.

  Background:
    Given el skill IncidentClassificationSkill está inicializado con un LLM

  Scenario: Clasificación exitosa con LLM batch
    Given hay 3 anomalías detectadas (sql_injection, xss, brute_force)
    When el skill clasifica las anomalías con el LLM
    Then el LLM recibe todas las anomalías en un solo prompt
    And se retorna una clasificación por cada anomalía

  Scenario: Fallback rule-based cuando el LLM falla
    Given hay 1 anomalías detectadas (sql_injection)
    And el LLM no está disponible (lanza excepción)
    When el skill clasifica las anomalías
    Then usa clasificación rule-based
    And cada anomalía tiene severidad según su tipo

  Scenario: Sin anomalías retorna lista vacía
    Given no hay anomalías
    When el skill ejecuta la clasificación
    Then retorna una lista vacía

  Scenario: RAG context incluido en el prompt del LLM
    Given hay incidentes históricos en ChromaDB
    And se detectan anomalías de sql_injection
    When el skill construye el prompt para el LLM
    Then el prompt incluye el contexto de incidentes similares

  Scenario: LLM responde con JSON mal formado
    Given hay 1 anomalías detectadas (sql_injection)
    And el LLM responde con texto que no es JSON válido
    When el skill intenta parsear la respuesta
    Then usa fallback rule-based
