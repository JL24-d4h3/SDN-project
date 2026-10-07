# Plano de datos: Pica8/PicOS

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** F — Decisiones tecnológicas
**Estado:** Borrador formal para revisión

---

El plano de datos es donde la política se vuelve realidad: el switch **ejecuta y reporta**, nunca decide (P8). La arquitectura ya fijó el hardware —Pica8 con PicOS (RP-11)— y con qué se le habla —OpenFlow 1.3, out-of-band (I1)—. Lo que esta fase decide es **qué primitivas se usan, cómo se verifican contra el dispositivo y qué regla de decisión se aplica si el dispositivo no las ofrece**, tal como [`C-04`](../C-Contexto/04_alcance_de_la_infraestructura.md) §5 prometió.

## 1. Qué exige la arquitectura del dispositivo

| Exigencia | Primitiva | Origen |
|---|---|---|
| Instalar y retirar reglas por orden del controlador, con vigencia y trazabilidad | `FLOW_MOD` con `cookie`, `idle_timeout`/`hard_timeout`, prioridad | R2.10, P10, RT-05 |
| Limitar tasa por origen sin cortar el servicio (primer peldaño de la escalera) | `METER_MOD` con banda de descarte | R4.6, R4.8, P9 |
| Bloquear origen, aislar dispositivo, contener en el switch de ingreso | `FLOW_MOD` DROP; `GROUP_MOD` para redirección | R3.7, R3.8, R4.7 |
| Reportar contadores al monitor — única fuente de observación del plano de datos | multipart `OFPMP_PORT_STATS`, `OFPMP_FLOW` | R3.1, R4.1, P11 |
| Avisar la llegada de tráfico sin match, el movimiento de una MAC y la expiración de reglas | `PACKET_IN`, `PORT_STATUS`, `FLOW_REMOVED` | R1.1, R3.3, P10 |
| Aceptar control solo por el canal de gestión | interfaz de control dedicada, out-of-band | RP-02, RA-09 |

## 2. Decisión

**PicOS en modo OpenFlow 1.3** como plano de datos del prototipo, con el canal de control out-of-band por la red de gestión (TCP 6653, solo el controlador autorizado) y el conjunto de primitivas de la tabla anterior como superficie contractual con la solución.

```text
Switch Pica8/PicOS — pipeline OpenFlow 1.3, por puerto de acceso
┌─────────────────────────────────────────────────────────────────┐
│  esqueleto BASE      pares 120/110 anti-spoofing · DROP a gestión
│  sesiones            reglas por perfil (cookie = sesión, idle_timeout)
│  mitigaciones        meter (rate limit) · DROP (bloqueo) · cookie = incidente
│  redirección         al portal (grupo o PACKET_OUT — se decide midiendo)
│  observación         contadores por flujo/puerto → multipart al monitor
└─────────────────────────────────────────────────────────────────┘
```

**La decisión no se compromete a ciegas.** Los switches del laboratorio deben soportar las primitivas que el diseño exige, y [`flows/01`](../../../flows/01_primitivas_openflow.md) y [`flows/04`](../../../flows/04_flujo_seguridad_r4.md) dejaron dicho que su disponibilidad se **verifica contra el dispositivo antes de comprometer el diseño**. Esta fase fija el procedimiento y la regla de decisión (§4); la medición ocurre en el prototipo.

## 3. Las primitivas y su uso

| Primitiva | Uso en la solución | Detalle |
|---|---|---|
| `FLOW_MOD` ADD | Esqueleto BASE, reglas de sesión, mitigaciones | match exacto, prioridad por peldaño de la escalera, `cookie` = sesión o incidente |
| `FLOW_MOD` DELETE por cookie | Logout, fin de elevación, cierre de incidente | el retiro es por cookie: nunca se toca una regla ajena (P10) |
| `METER_MOD` | `RATE_LIMIT` de un origen hacia un destino o del tráfico hacia un servicio | banda de descarte; la tasa es el parámetro de la política |
| `GROUP_MOD` | Redirección al portal e inundaciones controladas | tipo `ALL` para replicar hacia varios destinos |
| `PACKET_IN` | Aprendizaje (`OFPR_NO_MATCH`), redirección pre-login | con `in_port` y `buffer_id` |
| `PACKET_OUT` | Respuesta a paquetes buffereados | alternativa de redirección frente a `GROUP_MOD` |
| `FLOW_REMOVED` | Cierre por inactividad (`OFPRR_IDLE_TIMEOUT`) o retiro explícito | el controlador lo sabe antes que nadie y cierra la sesión ([`access/00`](../../../access/00_auth_controller.md) §3.6) |
| `PORT_STATUS` | Caída/recuperación de puerto y enlace | alimenta el aislamiento de fallos (E-04) |
| multipart `OFPMP_PORT_STATS` / `OFPMP_FLOW` | Contadores para el monitor (I8) | única fuente de observación del plano de datos (P11); en ningún caso SNMP o captura |
| `PORT_DESC`, `FEATURES` | Inventario físico del dispositivo | base de la verificación §4 |

**Cookie y timeouts, la convención.** Toda regla instalada lleva cookie y, salvo el esqueleto permanente, timeouts. La cookie identifica el origen de la regla —sesión (`SES-…`) o incidente (`INC-…`)— y es lo que hace posible el retiro quirúrgico y la reconciliación tras una caída ([`04`](04_mensajeria_y_eventos.md) §6). Los valores de vigencia por perfil están en [`03`](03_identidad_sesiones_y_portal.md) §5.

## 4. Verificación contra el dispositivo (regla de decisión)

Procedimiento previo a comprometer la implementación, ejecutado contra el switch del laboratorio:

| # | Prueba | Cómo | Si el resultado es negativo |
|---|---|---|---|
| V1 | Modo OpenFlow 1.3 y capacidades declaradas | `FEATURES_REQUEST/REPLY`: capacidades de tablas, contadores por flujo y por puerto, grupos | Sin contadores por flujo no hay línea base (P11): se reevalúa el modo del pipeline |
| V2 | Meters disponibles | `OFPMP_METER_FEATURES` (máximo de meters, bandas soportadas) y prueba real: instalar un `METER_MOD` de limitación y leerlo con `OFPMP_METER_CONFIG` | Entra la **degradación documentada**: contención por reglas temporales del controlador —se bloquean flujos nuevos del origen mientras persiste la tasa, y se retira al ceder— con su impacto medido (R4.6, R4.8) |
| V3 | Grupos disponibles | `GROUP_MOD` tipo `ALL` + `OFPMP_GROUP_DESC` | La redirección usa `PACKET_OUT`/reglas individuales; se mide la diferencia de latencia y carga de control |
| V4 | Redirección al portal: grupo frente a `PACKET_OUT` | Experimento comparativo con tráfico pre-login: latencia de primera resolución y carga sobre el controlador | P12 decide con los números: quédate con la alternativa medida |
| V5 | Expiración y retiro | Instalar regla con `idle_timeout` corto y observar `FLOW_REMOVED`; retirar por cookie | Sin `FLOW_REMOVED` el cierre por inactividad no se propaga: se compensa con consulta periódica del inventario de reglas |
| V6 | Rol de puerto y control | `PORT_STATUS` al caer un enlace; conexión de control rechazada desde otra interfaz | Se documenta la limitación y se ajusta la observación (I8) |
| V7 | Inundación y table-miss | Verificar que todo paquete sin match llega como `PACKET_IN` y que el `buffer_id` es utilizable | La redirección pasa a responder con `PACKET_OUT` sin buffer |

## 5. Capacidad de reglas

Cuántas reglas simultáneas admite el dispositivo condiciona el dimensionamiento (C-04 §6, B-03 §6). El experimento es directo: **instalar entradas por lotes hasta que el switch rechace (`OFPFMFC_TABLE_FULL`), reportando la cifra por tabla**. La referencia del diseño:

```text
esqueleto BASE por dispositivo conectado   ~6 reglas
reglas de sesión por dispositivo activo    ~4 reglas
caminos por destino                        una entrada por switch del camino
mitigaciones simultáneas (peor caso R4)    decenas
─────────────────────────────────────────────────────────
prototipo completo (ocho switches, ~23 dispositivos)     ≈ 350–450 entradas
```

La cifra medida se reporta como parte del cierre de RNF-05/RA-08 y del análisis de «exceso de reglas SDN» (B-03 §5). Si resultara menor que el escenario, las palancas ya están previstas: timeouts más agresivos, retiro por cookie (nada queda pegado), y agregación de mitigaciones por switch de ingreso —todo ello sin cambiar la arquitectura.

## 6. Límites

- **802.1X queda fuera del prototipo** (D-07 §3): reservado en el diseño para puertos sensibles de un despliegue real. La contención de suplantación en el prototipo es SDN —regla en el puerto nuevo y cuarentena—, no port security nativo.
- El detalle de configuración del pipeline (tablas, orden de instalación) es Fase G.
- Un único modelo de switch en el prototipo; la convivencia con otras plataformas pertenece a un despliegue (Fase H).

## 7. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| V1–V7 (§4) | Disponibilidad real de cada primitiva | C-04 §5, RT-05 |
| Capacidad de reglas (§5) | Entradas simultáneas por tabla | C-04 §6, RNF-05, RA-08 |
| Escenario R4 completo sobre el dispositivo | Meter instalado, tasa efectiva, retiro por timeout | R4.6, R4.7, R4.9 |
| Precisión de contadores frente a tráfico generado conocido | La base de la línea base y de la verificación de mitigaciones | R4.1, P11, RNF-12 |
