Feature: Correlación de eventos
  El skill EventCorrelation debe identificar patrones de ataque
  agrupando eventos por IP origen y tipo dentro de una ventana de tiempo.

  Background:
    Given el skill EventCorrelationSkill está inicializado
    And la ventana de correlación es de 3600 segundos
    And el umbral de brute-force es 3 intentos

  Scenario: Brute force detectado por múltiples auth_failed
    Given 4 eventos de "auth_failed" desde IP "10.0.0.1"
    When el skill correlaciona los eventos
    Then genera un patrón "brute_force"
    And el patrón tiene source_ip "10.0.0.1"
    And la severidad es "high"

  Scenario: Sin brute force por debajo del umbral
    Given 2 eventos de "auth_failed" desde IP "10.0.0.1"
    When el skill correlaciona los eventos
    Then no genera patrón "brute_force"

  Scenario: Port scan campaign detectado
    Given 3 eventos de "port_scan" desde distintas IPs
    When el skill correlaciona los eventos
    Then genera un patrón "port_scan_campaign"
    And la severidad es "medium"
    And incluye todas las IPs origen

  Scenario: Eventos fuera de la ventana de correlación
    Given eventos creados hace más de 3600 segundos
    When el skill correlaciona los eventos
    Then no se generan patrones

  Scenario: Múltiples IPs con eventos mixtos
    Given eventos de "auth_failed" desde IP "10.0.0.1" (4 eventos)
    And eventos de "auth_failed" desde IP "10.0.0.2" (2 eventos)
    When el skill correlaciona los eventos
    Then solo genera patrón para IP "10.0.0.1"
