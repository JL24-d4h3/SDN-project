# Sistemas externos

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** C — Contexto
**Estado:** Borrador formal para revisión

---

Un sistema externo existe con independencia del proyecto y el sistema se integra con él mediante una interfaz. No todos son dependencias: algunos son también origen de amenazas, y otros son aquello que el sistema protege.

---

## 1. Registro

| ID | Elemento externo | Categoría | Criticidad si falla |
|---|---|---|---|
| SE-01 | Internet y redes externas | Sistema externo y fuente de amenaza | Alta: sin él no hay servicio externo ni tráfico que inspeccionar |
| SE-02 | Sistema de identidad institucional | Sistema externo | Alta: sin identidad no hay control de acceso (R1) |
| SE-03 | Fuente de inteligencia de amenazas | Sistema externo | Media: degrada R5.6, no detiene la operación |
| SE-04 | Servicio de nombres (DNS) | Sistema externo | Alta: su manipulación es un vector de ataque (R3.3) |
| SE-05 | Sincronización de tiempo (NTP) | Sistema externo | Media: afecta la correlación de eventos y la auditoría |
| SE-06 | Servidores y servicios institucionales | Activo protegido | Alta: son el objeto de la protección (R2) |
| SE-07 | Dispositivos de usuario final | Activo protegido | Media: su compromiso los convierte en origen de amenaza |

---

## 2. Fichas

### SE-01 — Internet y redes externas

- **Qué se intercambia:** tráfico entrante hacia los servicios publicados y tráfico saliente autorizado.
- **Interfaz esperada:** el borde perimetral de la red (R5.1).
- **Condición de amenaza:** es el origen del atacante externo y de tráfico malicioso dirigido al perímetro.
- **En el prototipo:** se representa mediante un segmento externo controlado; el tráfico ofensivo se genera dentro del entorno (RP-06, RP-08).

### SE-02 — Sistema de identidad institucional

- **Qué se intercambia:** verificación de credenciales y atributos del usuario que solicita acceso.
- **Interfaz esperada:** consulta desde el mecanismo de autenticación de la plataforma.
- **Condición de amenaza:** no ataca, pero es objetivo: si se compromete, se compromete la autorización derivada de él.
- **En el prototipo:** se simula o se integra, según lo que exista en el entorno.
- **Nota:** determina el límite del sistema en todo lo relativo a R1 (ver [`01_limite_del_sistema.md`](01_limite_del_sistema.md)).

### SE-03 — Fuente de inteligencia de amenazas

- **Qué se intercambia:** indicadores (direcciones IP, URLs u otros) considerados maliciosos.
- **Interfaz esperada:** consulta o actualización periódica de listas (R5.6).
- **Condición de amenaza:** no; su corrupción produciría bloqueos erróneos o falsos negativos.
- **En el prototipo:** puede representarse con un conjunto de indicadores propio y controlado.

### SE-04 — Servicio de nombres (DNS)

- **Qué se intercambia:** resolución de nombres para el tráfico legítimo.
- **Interfaz esperada:** servicio de resolución de la red.
- **Condición de amenaza:** sí, indirectamente: la suplantación de respuestas es un caso de origen inconsistente (R3.3).
- **En el prototipo:** servicio de nombres del propio entorno.

### SE-05 — Sincronización de tiempo (NTP)

- **Qué se intercambia:** referencia temporal para los registros.
- **Interfaz esperada:** servicio de tiempo de la red.
- **Condición de amenaza:** no, pero su ausencia o manipulación deteriora la trazabilidad (RNF-09) y la investigación de incidentes (ADM-03).
- **En el prototipo:** servicio de tiempo del entorno virtual.

### SE-06 — Servidores y servicios institucionales

- **Qué se intercambia:** el tráfico autorizado que los alcanza y los registros que generan.
- **Condición de amenaza:** no; son el objeto de protección de R2 y el destino de los ataques de R3 y R4.
- **En el prototipo:** se representan mediante equivalentes controlados, no con los servicios reales de la institución.

### SE-07 — Dispositivos de usuario final

- **Qué se intercambia:** tráfico de los usuarios legítimos.
- **Condición de amenaza:** un dispositivo comprometido se convierte en nodo comprometido, y su tráfico pasa a ser objeto de R3 y R4 aunque el usuario conserve credenciales válidas.
- **En el prototipo:** hosts simulados que representan alumnos y docentes.

---

## 3. Dependencias que el prototipo debe resolver

| Dependencia | Alternativa si no existe en el entorno |
|---|---|
| Identidad institucional | Directorio simulado con usuarios y roles de prueba |
| Inteligencia de amenazas | Conjunto de indicadores propio, definido por el proyecto |
| Internet | Segmento externo controlado dentro del laboratorio |
| Servicios institucionales | Servidores equivalentes desplegados en el prototipo |
| DNS y NTP | Servicios del propio entorno de virtualización |

---

## 4. Cuestiones abiertas

- Si el IDS/IPS y el firewall son sistemas externos institucionales o componentes del propio sistema (ver [`01_limite_del_sistema.md`](01_limite_del_sistema.md)).
- Si la inteligencia de amenazas se alimenta de un servicio real, de listas propias o de ambos.
- Si los dispositivos de usuario final se modelan como activos protegidos o solo como orígenes de tráfico sujetos a observación.
