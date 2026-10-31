# Plan de trabajo de la etapa 2 — Despliegue e implementación

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** Implementación — Etapa 2
**Estado:** Borrador formal para revisión

---

## 1. Propósito

Convertir el diseño de [`05_plan_de_implementacion.md`](05_plan_de_implementacion.md) en una secuencia ejecutable: paquetes de trabajo, dependencias, entregables y criterios de aceptación. La etapa 2 termina con un entorno **reproducible** que ejecuta los flujos F1–F3 y deja preparados F4–F7; la campaña completa de prueba y medición pertenece a la etapa 3.

## 2. Condiciones de entrada

- Etapa 0 cerrada: matriz, YAML y generador en verde ([`00_cierre_etapa_0_permisos.md`](00_cierre_etapa_0_permisos.md)).
- Etapa 1 documentada: checklist de capacidades y presupuesto en [`04_capacidades_del_switch.md`](04_capacidades_del_switch.md).
- Slice asignado por la nube privada, o un sustituto local declarado mientras se recibe.
- Acceso VPN, credenciales SSH, imágenes de contenedores y ventana de trabajo.
- Decisión de perfil: cinco switches (recomendado) o tres (mínimo), según [`05`](05_plan_de_implementacion.md) §2–§3.

## 3. Resultado esperado

La etapa se considera terminada cuando se cumplen estos criterios:

| # | Criterio | Evidencia |
|---|---|---|
| 1 | Inventario real del slice completo: switches, puertos, NICs, VLANs, RAM, CPU, disco, salida y persistencia | Tabla de mapeo de §4 de [`05`](05_plan_de_implementacion.md) llena; acta de capacidades |
| 2 | Clúster ONOS de tres nodos con quórum, un maestro por switch y API I2 disponible en cualquier nodo | Estado del clúster y prueba de humo de I2 |
| 3 | Switches con VLANs, puertos, OpenFlow, espejo, modo seguro y respaldo de configuración | Configuraciones versionadas y respaldo restaurable |
| 4 | Cuatro servidores de servicios con Compose, PostgreSQL, RabbitMQ, Prometheus/Grafana y FreeRADIUS/OpenLDAP | Archivos Compose y salud de los servicios |
| 5 | Los diez servicios responden `/health` y los contratos de eventos y API validan | Informe de humo y validación de contratos |
| 6 | F1 (descubrimiento), F2 (BASE) y F3 (login) funcionan; F4 (elevación) tiene su esqueleto | Tablas de flujo y trazas de sesión |
| 7 | Reconstrucción desde cero con Ansible, sin secretos en el repositorio | Ejecución limpia de playbooks y análisis de secretos |
| 8 | Desviaciones y límites del slice documentados | Registro de desviaciones en el anexo del slice |

## 4. Paquetes de trabajo

### WP2.0 — Inventario y go/no-go del slice

**Objetivo:** confirmar que el slice puede sostener el diseño antes de instalar nada.

Tareas:

1. Llenar la tabla de mapeo de direcciones, interfaces y VLAN de [`05`](05_plan_de_implementacion.md) §4.
2. Ejecutar el script de verificación de [`04`](04_capacidades_del_switch.md) en cada switch y registrar las banderas de capacidad.
3. Confirmar RAM, vCPU, disco, persistencia, salida a Internet y acceso externo.
4. Elegir el perfil de cinco o tres switches y registrar toda desviación.

**Entregable:** anexo de inventario del slice y acta de capacidades.
**Aceptación:** todos los campos llenos; decisión go/no-go firmada; respaldo definido para cada capacidad ausente.

### WP2.1 — Base de hosts y acceso

**Objetivo:** dejar los hosts administrables y repetibles.

Tareas:

1. VPN, claves SSH, usuarios, `sudo` y firewall.
2. chrony y DNS; verificar desfase de reloj.
3. Docker y acceso al registro de imágenes.
4. Inventario de Ansible, grupos y Vault.
5. Playbook `00_bootstrap.yml` y prueba de humo.

**Entregable:** inventario, playbook 00 y salida de la prueba.
**Aceptación:** todos los hosts responden a `ansible -m ping`; Docker ejecuta una imagen de prueba; desfase de reloj menor a 1 s; ningún secreto en texto plano.

### WP2.2 — Red y switches

**Objetivo:** materializar la topología del slice y el canal de control.

Tareas:

1. VLAN 10 (usuarios), 100 (gestión), 20 (servidores) y 30 (frontera).
2. Mapa de puertos y enlaces L01–L12 del perfil elegido.
3. Troncales, puertos de acceso y VLAN de gestión.
4. Endpoints OpenFlow de los tres nodos ONOS.
5. Espejo hacia el sensor; si no existe, activar el respaldo de [`04`](04_capacidades_del_switch.md).
6. Modo seguro: SSH con claves, sin telnet/HTTP, ACL de gestión, puertos no usados deshabilitados, respaldo de configuración.
7. Playbook `01_switches.yml`.

**Entregable:** configuraciones de switch, mapa de puertos y playbook 01.
**Aceptación:** matriz de alcanzabilidad de VLAN correcta; OpenFlow conecta con ONOS; el espejo captura tráfico; puertos no usados apagados; respaldo restaurable.

### WP2.3 — Clúster ONOS

**Objetivo:** dejar el plano de control redundante y observable.

Tareas:

1. Tres nodos ONOS-1/2/3 en `.20`, `.30` y `.40`, cada uno en su propio servidor.
2. Java, ONOS, Atomix/Raft y aplicaciones.
3. NIC de datos en VLAN 100 y NIC de gestión OOB.
4. API I2 en TCP 8181, claves y clientes.
5. Playbook `02_onos.yml`.
6. Prueba preliminar de caída de un nodo.

**Entregable:** clúster en verde, API de humo y playbook 02.
**Aceptación:** tres nodos con quórum; un maestro por switch; I2 responde en cualquier nodo; al caer un nodo hay re-maestría y reconciliación sin borrar reglas vigentes.

### WP2.4 — Servicios base

**Objetivo:** desplegar la plataforma mínima que sostiene identidad, eventos y observación.

Tareas:

1. Cuatro servidores S1–S4 según [`05`](05_plan_de_implementacion.md) §5.
2. Compose por servidor, redes, volúmenes y dependencias.
3. PostgreSQL por servicio o esquema propio; RabbitMQ con colas y DLQ.
4. Prometheus, Grafana, FreeRADIUS y OpenLDAP.
5. Esqueletos de los diez servicios con `/health` y contratos.
6. Playbook `03_services.yml` y CI de contratos.

**Entregable:** Compose, contratos, CI y playbook 03.
**Aceptación:** los diez servicios responden; base y broker alcanzables; contratos validan; reinicio automático; sin secretos en el repositorio.

### WP2.5 — Identidad y portal mínimo

**Objetivo:** cerrar el camino de identidad que alimenta los perfiles.

Tareas:

1. Portal con login académico y login de operador.
2. IAM: RADIUS contra FreeRADIUS/OpenLDAP y TOTP para operadores.
3. Sesión, cierre e inactividad.
4. Decisión de perfil y orden a I2.
5. Evento de sesión y registro de auditoría.

**Entregable:** F3 funcionando y evidencia de sesión.
**Aceptación:** antes del login el dispositivo es BASE; académico obtiene ACADÉMICO; operador con MFA obtiene OPERADOR_*; logout e inactividad devuelven a BASE; la auditoría registra la sesión.

### WP2.6 — Flujos base y perfiles

**Objetivo:** materializar F1–F4 en el pipeline.

Tareas:

1. Descubrimiento de topología y caminos por destino.
2. Esqueleto BASE con prioridades 150/120/110/100/10.
3. Reglas de sesión con cookie, prioridad 200 e idle_timeout.
4. Elevación temporal con TTL y hard_timeout.
5. Subconjunto de pruebas L4 de [`03`](03_plan_de_pruebas_permisos.md).
6. Verificación de retiro por cookie y `FLOW_REMOVED`.

**Entregable:** tablas de flujo e informe de pruebas L4.
**Aceptación:** prioridades y cookies coinciden con [`G-06`](../docs/fases/G-Diseno_de_bajo_nivel-LLD/06_reglas.md); no quedan reglas residuales; la elevación expira; el perfil BASE se restaura.

### WP2.7 — Reproducibilidad y cierre

**Objetivo:** demostrar que el entorno no depende de pasos manuales.

Tareas:

1. Reconstrucción limpia con los playbooks 00–04.
2. Respaldo y restauración de PostgreSQL, ONOS y switches.
3. Runbook de operación y solución de problemas.
4. Etiqueta de liberación de la etapa 2.
5. Registro de desviaciones y límites.

**Entregable:** etiqueta `etapa-2`, runbook e informe de reconstrucción.
**Aceptación:** reconstrucción dentro de la ventana acordada; todas las pruebas de humo pasan; el respaldo restaura; las desviaciones están documentadas.

## 5. Dependencias y secuencia

```text
WP2.0 ──► WP2.1 ──► WP2.2 ──► WP2.3 ──► WP2.6 ──► WP2.7
              │
              └────► WP2.4 ──► WP2.5 ──► WP2.6
```

- **Camino crítico:** WP2.0 → WP2.1 → WP2.2 → WP2.3 → WP2.6 → WP2.7.
- WP2.2 y WP2.4 pueden avanzar en paralelo después de WP2.1.
- WP2.5 no puede cerrarse sin WP2.4; WP2.6 no puede cerrarse sin WP2.3 y WP2.5.
- WP2.7 exige todos los paquetes anteriores.

## 6. Calendario

| Semana | Hito | Paquetes |
|---|---|---|
| 1 | H0 — slice verificado | WP2.0, WP2.1 |
| 1–2 | H1 — etapa 0 cerrada (ya cumplido) | — |
| 2 | Base y red | WP2.2 |
| 2–3 | H2 — esqueleto de servicios | WP2.3, WP2.4 |
| 3 | Identidad y sesión | WP2.5 |
| 3–4 | H3 — clúster, switches y flujos base | WP2.6 |
| 4 | Cierre de etapa | WP2.7 |

Los identificadores `Hn` son los hitos de [`05`](05_plan_de_implementacion.md) §12. El calendario es una guía; la fecha real la fija la asignación del slice. Si el slice se retrasa, WP2.1 y WP2.4 se ejecutan contra el sustituto local y se repiten al recibirlo.

## 7. Entregables

| Entregable | Paquete | Ubicación |
|---|---|---|
| Inventario y acta de capacidades | WP2.0 | Anexo del slice |
| Playbooks 00–05 e inventario | WP2.1–WP2.7 | `deploy/ansible/` |
| Compose por servidor | WP2.4 | `deploy/compose/` |
| Contratos de eventos y API | WP2.4 | `contracts/` |
| Configuraciones de switch | WP2.2 | `deploy/switches/` |
| Informe de pruebas L4 | WP2.6 | `tests/evidence/etapa_2/` |
| Runbook y etiqueta | WP2.7 | Raíz del repositorio |

## 8. Riesgos y contingencias

| Riesgo | Señal | Mitigación | Respaldo |
|---|---|---|---|
| El slice cambia de dispositivos o puertos | Inventario no coincide | Congelar el mapa en WP2.0 y versionarlo | Rehacer WP2.2 con el mapa nuevo |
| No hay espejo al sensor | `/capabilities` con `mirror=false` | Activar sFlow/NetFlow o tap en el host | Degradar R5 y declararlo |
| Los tres ONOS comparten host | Caída del host apaga el clúster | Distribuir nodos si el slice lo permite | Documentar el límite; no reduce el quórum lógico |
| Registro de imágenes inaccesible | `docker pull` falla | `docker save/load` y registro local | Construir imágenes en el host |
| Conflicto de VLAN o dirección | Tráfico no alcanza | Mapa de direcciones y VLAN antes de configurar | Renumerar el segmento afectado |
| Tiempo insuficiente | WP2.6 no cierra | Priorizar F1–F3 y dejar F4 en esqueleto | Posponer F4 y la consola a la etapa 3 |
| Credenciales o secretos expuestos | Análisis de secretos falla | Vault, variables de entorno y `.gitignore` | Rotar credenciales y rehacer el despliegue |

## 9. Fuera de alcance

- La campaña completa de R4, la suite L0–L6 y las mediciones de la etapa 3.
- La topología de referencia de diez switches.
- Kubernetes, 802.1X en puertos sensibles y P35/P36 a nivel funcional.
- La integración con el IdP institucional de producción.

## 10. Trazabilidad

| Documento | Relación |
|---|---|
| [`00_cierre_etapa_0_permisos.md`](00_cierre_etapa_0_permisos.md) | Decisiones de permisos que los servicios aplican |
| [`04_capacidades_del_switch.md`](04_capacidades_del_switch.md) | Verificación y respaldos de capacidad |
| [`05_plan_de_implementacion.md`](05_plan_de_implementacion.md) | Diseño de topología, servidores, orquestación y Ansible |
| [`07_plan_de_trabajo_etapa_3.md`](07_plan_de_trabajo_etapa_3.md) | Campaña de ejecución y medición |
| [`../docs/fases/H-Despliegue/`](../docs/fases/H-Despliegue/) | Infraestructura, VMs, red y puertos de referencia |
| [`../docs/fases/G-Diseno_de_bajo_nivel-LLD/`](../docs/fases/G-Diseno_de_bajo_nivel-LLD/) | Contratos, reglas y configuraciones |
