Feature: Estado de servidores
  El skill ServerState debe monitorear servidores y generar
  alertas cuando detecta condiciones anómalas.

  Background:
    Given el skill ServerStateSkill está inicializado

  Scenario: Servidor offline detectado
    Given un servidor con status "offline"
    When el skill procesa los servidores
    Then genera una alerta "server_offline"
    And la severidad es "critical"

  Scenario: CPU alto detectado
    Given un servidor con cpu_usage de 92%
    When el skill procesa los servidores
    Then genera una alerta "high_cpu"
    And la severidad es "high"
    And el valor reportado es 92%

  Scenario: Memoria alta detectada
    Given un servidor con memory_usage de 88%
    When el skill procesa los servidores
    Then genera una alerta "high_memory"
    And la severidad es "high"

  Scenario: Disco lleno detectado
    Given un servidor con disk_usage de 95%
    When el skill procesa los servidores
    Then genera una alerta "disk_full"
    And la severidad es "medium"

  Scenario: Múltiples alertas en distintos servidores
    Given un servidor "web-01" con CPU 45% (normal)
    And un servidor "db-01" con CPU 95% (alerta)
    And un servidor "cache-01" con status "offline" (alerta)
    When el skill procesa los servidores
    Then genera 2 alertas
    And incluye "high_cpu" para "db-01"
    And incluye "server_offline" para "cache-01"

  Scenario: Tracking de estado entre ciclos
    Given el skill ha procesado servidores en un ciclo anterior
    When procesa los mismos servidores en un nuevo ciclo
    Then mantiene el estado interno de todos los servidores
