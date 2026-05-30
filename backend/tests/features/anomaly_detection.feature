Feature: Detección de anomalías
  El skill AnomalyDetection debe identificar ataques conocidos
  mediante firmas en el raw_data de los eventos, y detectar
  problemas de infraestructura en servidores.

  Background:
    Given el skill AnomalyDetectionSkill está inicializado

  Scenario: SQL Injection detectado en raw_data
    Given un evento con payload "' OR 1=1--"
    When el skill procesa el evento
    Then debe clasificarlo como "sql_injection"
    And la severidad debe ser "critical"

  Scenario: XSS detectado en raw_data
    Given un evento con payload "<script>alert('xss')</script>"
    When el skill procesa el evento
    Then debe clasificarlo como "xss"
    And la severidad debe ser "high"

  Scenario: Path traversal detectado en URL
    Given un evento path traversal con ruta "/../../../etc/passwd"
    When el skill procesa el evento
    Then debe clasificarlo como "path_traversal"

  Scenario: Command injection detectado
    Given un evento con comando "id; cat /etc/shadow"
    When el skill procesa el evento
    Then debe clasificarlo como "command_injection"
    And la severidad debe ser "critical"

  Scenario: Resource exhaustion por CPU alto
    Given un servidor "db-01" con cpu_usage 95%
    When el skill procesa los servidores
    Then genera una anomalía "resource_exhaustion" para "db-01"

  Scenario: Sin anomalías con eventos limpios
    Given un evento limpio con ruta "/index.html" y método "GET"
    When el skill procesa el evento
    Then no se generan anomalías

  Scenario: Brute force desde patrón de correlación
    Given un patrón "brute_force" para IP "10.0.0.1" con severidad "high"
    When el skill procesa el patrón
    Then genera una anomalía "brute_force" con IP "10.0.0.1"

  Scenario: raw_data como string en lugar de dict
    Given un evento con raw_data en formato string "GET /?q=' OR 1=1--"
    When el skill procesa el evento
    Then debe detectar "sql_injection"
