Feature: Notificaciones por Telegram
  El skill Notification debe enviar alertas de incidentes
  al chat de Telegram configurado.

  Background:
    Given el skill NotificationSkill está inicializado

  Scenario: Notificación enviada exitosamente
    Given hay recomendaciones para un incidente crítico
    And el bot de Telegram está configurado con token válido
    When el skill envía la notificación
    Then se realiza una llamada a la API de Telegram
    And se marca como notificado

  Scenario: Sin token de Telegram configurado
    Given hay recomendaciones para un incidente crítico
    And el token del bot de Telegram está vacío
    When el skill intenta notificar
    Then omite el envío sin errores

  Scenario: Múltiples chats configurados
    Given hay 2 chat_ids configurados
    When el skill envía la notificación
    Then se envía el mensaje a ambos chats

  Scenario: Error en la API de Telegram
    Given la API de Telegram responde con error
    When el skill envía la notificación
    Then captura el error y continúa sin interrumpir el ciclo
