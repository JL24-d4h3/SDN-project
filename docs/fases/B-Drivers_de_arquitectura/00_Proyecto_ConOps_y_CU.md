# 5. Casos de uso mínimos

## CU-01 — Acceso autorizado
Un dispositivo se conecta y recibe el perfil BASE con privilegios mínimos; un operador con credenciales válidas se autentica y obtiene los permisos correspondientes a su rol, con vigencia acotada.

## CU-02 — Acceso no autorizado
Un dispositivo intenta alcanzar recursos por encima de su perfil y el sistema rechaza la solicitud y registra el evento.

## CU-03 — Acceso autorizado a recurso privilegiado
Un usuario autorizado solicita un recurso privilegiado y el acceso es permitido y registrado.

## CU-04 — Acceso no autorizado a recurso privilegiado
Un usuario sin privilegios suficientes intenta acceder y el sistema bloquea la solicitud.

## CU-05 — Port scanning
Un host genera múltiples intentos de conexión; el sistema detecta el patrón y aplica la respuesta definida.

## CU-06 — IP spoofing
Se detecta tráfico inconsistente con las condiciones de origen esperadas y se aplica la respuesta definida.

## CU-07 — DDoS interno
El tráfico hacia un servidor supera el comportamiento esperado; el sistema detecta, mitiga y posteriormente recupera la política normal.

## CU-08 — Ataque externo
El tráfico externo es inspeccionado; una amenaza identificada genera alerta, bloqueo o mitigación.

## CU-09 — Gestión de política
Un administrador se autentica, modifica una política y la aplica mediante el sistema.

## CU-10 — Recuperación
Después de un incidente, el sistema elimina o modifica las reglas temporales y retorna a la política normal.

---
#
# 6. Flujos operativos

## 11.1 Operación normal

**Dispositivo → perfil BASE (presencia física) → política por defecto → recurso → monitoreo → registro. Con elevación: autenticación → identidad/rol → política contextual → recurso.**

## 11.2 Acceso no autorizado

**Solicitud por encima del perfil → política deniega → rechazo → registro → alerta cuando corresponda.**

## 11.3 Incidente de seguridad

**Tráfico → monitoreo → detección → clasificación → decisión → mitigación → registro → recuperación.**

## 11.4 Administración

**Administrador → autenticación → gestión de política → validación → aplicación → auditoría.**

---
#
# 7. Políticas de seguridad

### PS-01 — Mínimo privilegio
Cada usuario deberá disponer únicamente de los permisos necesarios.

### PS-02 — Denegación por defecto
Una solicitud sin autorización explícita deberá considerarse no autorizada, salvo justificación del diseño final.

### PS-03 — Separación por roles
Los privilegios deberán asociarse principalmente a roles.

### PS-04 — Protección diferenciada
Los recursos críticos deberán recibir controles superiores.

### PS-05 — Respuesta proporcional
La mitigación deberá corresponder al tipo y nivel de amenaza.

### PS-06 — Trazabilidad
Las decisiones relevantes deberán poder auditarse.

### PS-07 — Reversibilidad
Las acciones temporales deberán poder revertirse.

---
#
# 8. Criterios de éxito

La solución deberá evaluarse mediante criterios cualitativos y cuantitativos.

## Seguridad

- tasa de bloqueo de accesos inválidos;
- precisión en la restricción de recursos;
- tasa de detección;
- tasa de falsos positivos.

## Rendimiento

- latencia de autenticación;
- latencia de autorización;
- tiempo de detección;
- tiempo de mitigación;
- throughput;
- solicitudes por segundo.

## Disponibilidad y resiliencia

- disponibilidad durante ataques;
- tiempo de recuperación;
- impacto sobre tráfico legítimo.

## Escalabilidad

- usuarios concurrentes;
- sesiones concurrentes;
- eventos por segundo;
- cantidad de políticas/reglas gestionadas.

## Consumo de recursos

- CPU;
- memoria;
- ancho de banda;
- utilización de recursos de dispositivos SDN;
- TCAM, cuando corresponda.

---
#
# 9. Requisitos de pruebas

### PT-01 — Pruebas funcionales
Cada requerimiento implementado deberá contar con pruebas positivas.

### PT-02 — Pruebas negativas
Deberán probarse condiciones en las que el sistema debe rechazar, bloquear o mitigar.

### PT-03 — Rendimiento
Deberá medirse el comportamiento bajo diferentes cargas.

### PT-04 — Ataques
Los escenarios de seguridad deberán ejecutarse en el entorno controlado.

### PT-05 — Recuperación
Deberá comprobarse el retorno a operación normal.

### PT-06 — Escalabilidad
Cuando resulte viable, deberán incrementarse progresivamente usuarios, flujos, solicitudes o eventos.

### PT-07 — Comparación de alternativas
Cuando existan alternativas de diseño, deberán compararse mediante métricas objetivas.

---
#
# 10. Administración y observabilidad

### ADM-01
El administrador deberá poder consultar las políticas activas.

### ADM-02
El administrador deberá poder identificar eventos de seguridad relevantes.

### ADM-03
La solución deberá proporcionar información suficiente para investigar incidentes.

### ADM-04
Los cambios de política deberán poder registrarse.

### ADM-05
Las acciones automáticas de mitigación deberán poder identificarse posteriormente.
