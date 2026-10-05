# Método de decisión tecnológica

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** F — Decisiones tecnológicas
**Estado:** Borrador formal para revisión

---

La Fase D fijó **qué componentes existen y qué contrato los une**; esta fase elige **con qué tecnología se materializan**. Ninguna decisión de esta fase cambia la arquitectura: la implementa. Si una tecnología no puede cumplir un contrato ya fijado, se cambia la tecnología, no el contrato.

## 1. De dónde vienen las decisiones

Cada decisión de esta fase tiene origen en un lugar del corpus que la difirió explícitamente:

| Origen | Qué dejó pendiente |
|---|---|
| [B-03](../B-Drivers_de_arquitectura/03_priorizacion_de_drivers.md) §4 | El catálogo de decisiones que activa cada driver: controlador, norte/sur, umbrales, IDS/IPS, almacenamiento, virtualización, visualización |
| [C-04](../C-Contexto/04_alcance_de_la_infraestructura.md) §6 | Capacidad del dispositivo, representación del perímetro, hardware físico o virtual |
| [D-07](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/07_interfaces_principales.md) §4 | Forma concreta de I2 e I7; producto del broker (I5); frecuencia de I8 |
| [D-08](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/08_comunicacion.md) §4, §6 | Mecanismo de entrega ordenada; confirmación de comandos; retención de eventos en el broker |
| [D-04](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/04_descomposición_arquitectonica.md) §7 | Consolidación Monitor/Detección en el prototipo |
| [D-03](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/03_principios_arquitectonicos.md) §7 | Precedencia P9/P12 en caso extremo |
| [E-04](../E-Validacion_del_HLD/04_escenarios_de_fallo.md) §4 | Redundancia del plano de control; reconstrucción del intermediario; retención de registros |
| [E-05](../E-Validacion_del_HLD/05_escenarios_de_ataque.md) §3 | Fuente de tiempo común; cierre del perímetro (R5) |
| [E-02](../E-Validacion_del_HLD/02_requisitos_a_componentes.md) §5 | Elementos cuantitativos: R4.3/R4.4/4.10, RNF-03/04/11/12 |

## 2. Criterios de elección

Toda decisión de producto se justifica con cinco criterios, en este orden:

1. **Cumplimiento** — resuelve el requisito o driver que la origina (R1–R5, RT, RNF, RA).
2. **Verificabilidad** — permite producir las métricas que el curso exige (P12, RNF-12, RP-10); una alternativa sin medición no es una alternativa.
3. **Simplicidad justificada** — dimensionada al prototipo, no a producción (P4, RP-04, RP-07): contra el tamaño real del prototipo, no contra una universidad.
4. **Encaje con las restricciones** — Pica8/PicOS (RP-11), canal de control out-of-band (RP-02), IPv4 (RP-12), entorno del laboratorio.
5. **Separación de responsabilidades** — el producto no absorbe funciones de otro componente (RT-02, P3): elegir un producto no reasigna responsabilidades.

## 3. Formato de cada decisión

Cada documento de la serie sigue la misma estructura:

```text
Contexto      qué exige la arquitectura (con su origen documental)
Decisión      el producto o mecanismo elegido, en una frase
Justificación contra los cinco criterios, punto por punto
Configuración cómo queda en el prototipo (piezas, puertos, parámetros)
Límites       qué no decide esta fase y con qué fase se cierra
Verificación  qué prueba del prototipo cierra la decisión y qué mide
```

Cuando P12 obliga a decidir **con resultados** —meters nativos frente a degradación por controlador, redirección por grupo frente a `PACKET_OUT`— el documento no elige de antemano: fija las alternativas, el experimento y la regla de decisión. La medición decide; el documento registra qué se medirá.

## 4. Mapa de la serie

| Documento | Decide | Cierra |
|---|---|---|
| [`01_controlador_y_api_northbound.md`](01_controlador_y_api_northbound.md) | Producto del controlador; forma de I2; redundancia del plano de control | RA-02, RT-04, E-04 |
| [`02_plano_de_datos_pica8.md`](02_plano_de_datos_pica8.md) | Primitivas del plano de datos; verificación de PicOS; capacidad de reglas | RT-05, R4.6, C-04 §6 |
| [`03_identidad_sesiones_y_portal.md`](03_identidad_sesiones_y_portal.md) | Producto de I4; repositorio de operadores y TOTP; forma de la sesión; distinción de población; valores de vigencia | R1.2, I4, I7, I3 |
| [`04_mensajeria_y_eventos.md`](04_mensajeria_y_eventos.md) | Producto del broker; entrega ordenada; garantías; reconciliación | I5, D-08 §4, E-04 |
| [`05_persistencia_auditoria_y_tiempo.md`](05_persistencia_auditoria_y_tiempo.md) | Persistencia (I6); retención e integridad de registros; tiempo común; visualización | I6, RNF-09, E-04, E-05 |
| [`06_deteccion_y_mitigacion.md`](06_deteccion_y_mitigacion.md) | Algoritmo de detección; umbrales; frecuencia de I8; precedencia P9/P12; presupuesto de latencia | R3.1–R3.10, R4.1–R4.10, D-10 |
| [`07_perimetro_r5.md`](07_perimetro_r5.md) | Evaluación IDS/IPS; perímetro; inteligencia de amenazas | R5.1–R5.8, CU-08 |
| [`08_entorno_del_prototipo.md`](08_entorno_del_prototipo.md) | Virtualización y simulación; segmentos; generación de tráfico; reproducibilidad | RP-05, RNF-11, C-04 |
| [`09_sintesis_y_trazabilidad.md`](09_sintesis_y_trazabilidad.md) | Tabla decisión ↔ requisito ↔ verificación; pendientes que quedan | Todas |

## 5. Fronteras de esta fase

- **Valores finales cuantitativos** (umbrales, capacidades, tiempos): esta fase decide el mecanismo y el experimento; el número final lo produce el prototipo y se reporta como cierre de R4.10, RNF-03/04/11/12.
- **Detalle de implementación** (estructuras internas, librerías): Fase G.
- **Despliegue físico** (nodos, enlaces, redundancia real): Fase H.
- **Cada decisión conserva los contratos** de [`07_interfaces_principales.md`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/07_interfaces_principales.md) y [`08_comunicacion.md`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/08_comunicacion.md): formatos de eventos, separación síncrono/asíncrono y frontera de secretos no se negocian con el producto.

# Controlador SDN y API northbound

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** F — Decisiones tecnológicas
**Estado:** Borrador formal para revisión

---

Dos decisiones en un documento: el **producto del controlador** (RA-02) y la **forma concreta de I2** (RT-04), más la decisión de **redundancia del plano de control** que [`E-04`](../E-Validacion_del_HLD/04_escenarios_de_fallo.md) §4 difirió a esta fase. El papel del controlador no cambia: **aprende, traduce y retira**; nunca autentica, decide ni ve un secreto ([`access/00`](../../../access/00_auth_controller.md) §1).

## 1. Qué exige la arquitectura

| Exigencia | Origen |
|---|---|
| Ser el punto central de decisión de la red: recibir `PACKET_IN`, aprender y mantener las asociaciones `host ↔ MAC ↔ IP ↔ switch ↔ puerto`, traducir cada orden a reglas y retirar lo que expira | D-04 §5, [`access/00`](../../../access/00_auth_controller.md) §2 |
| Hablar OpenFlow 1.3 con los switches, out-of-band, con meters, groups y contadores | I1 (D-07 §2), RP-02, RP-11 |
| Exponer una API northbound por la que los servicios envían **órdenes** («qué») y reciben confirmación | I2 (D-07 §2, §4) |
| Soportar la operación en una única instancia del prototipo y una vía de redundancia documentada | E-04 §4, C-04 §4 |
| Ser protegido como activo de máximo valor: interfaz administrativa restringida, solo desde la red de gestión | RA-09, D-11 §3 |

## 2. Decisión

**ONOS** como controlador SDN del prototipo, desplegado en una instancia única sobre la red de gestión. La lógica propia de la plataforma —la API de órdenes de I2 y su traducción a OpenFlow— vive como una **aplicación del controlador**, no como un servicio aparte: el controlador no es un microservicio de la plataforma (P1, D-04 §6), pero su interior sí tiene una pieza propia que es la única autorizada a tocar el pipeline de los switches.

```text
┌─ Controlador (ONOS, red de gestión) ──────────────────────────────┐
│  aplicación propia:  API de órdenes (I2)  +  traductor a OpenFlow │
│  ONOS base:          topología · asociaciones · state machine OF  │
└───────────────────────────────────────────────────────────────────┘
        ▲ I2 (HTTPS/JSON)                      ▼ I1 (OpenFlow 1.3, TCP 6653)
   servicios de la plataforma              switches Pica8/PicOS
```

## 3. Justificación

**Cumplimiento.** ONOS cubre el papel completo del controlador: descubrimiento de topología (LLDP), seguimiento de hosts, ciclo de vida OpenFlow (handshake, `ECHO`, re-registro), y las primitivas que los requerimientos exigen —`FLOW_MOD`, `METER_MOD`, `GROUP_MOD`, `PACKET_IN`/`PACKET_OUT`, multipart de contadores— sobre OpenFlow 1.3, el protocolo ya fijado para I1 (RT-05).

**Verificabilidad.** Su API REST nativa permite consultar el estado real del plano de control —dispositivos, enlaces, entradas instaladas— que es la fuente para las métricas de RA-07 y R4.10 (tiempo de reinstalación de reglas tras una caída) y para las consultas de asociaciones de la plataforma (§5). ONOS expone además estadísticas internas del propio controlador (carga, memoria, tiempos de respuesta), lo que sirve al análisis de riesgo del controlador que pide D-11.

**Simplicidad justificada (P4).** Una instancia ONOS corre en una VM Linux modesta dentro del laboratorio, sin dependencias externas, y su conjunto de aplicaciones se limita a lo que la solución usa: el controlador no se convierte en una plataforma de aplicaciones. El clúster (§6) es una capacidad nativa que no se despliega en el prototipo.

**Encaje.** OpenFlow 1.3 y out-of-band son configuración directa; la administración (web y CLI) queda restringida a la red de gestión (RA-09); el proyecto es de código abierto con base académica amplia, lo que encaja con el contexto del curso y con la mantenibilidad (RNF-10).

**Separación de responsabilidades.** ONOS no autentica ni decide: recibe órdenes ya decididas por el Policy Engine y las traduce sin alterarlas ([`access/00`](../../../access/00_auth_controller.md) §3.4). La aplicación de traducción es la encargada de mantener esa frontera: su contrato es **traducción fiel**, y toda orden que no pueda traducirse se rechaza con error — nunca se aproxima.

## 4. Forma concreta de I2: la API de órdenes

**Principio.** La orden expresa el **qué** —perfil, dispositivo, ubicación, vigencia, contexto— y el controlador posee el **cómo**: match exacto, prioridad, cookie y timeouts. Los servicios no conocen prioridades ni campos de OpenFlow; el controlador no conoce usuarios ni políticas.

### 4.1 Transporte y seguridad

- HTTPS con JSON sobre la red de gestión (out-of-band); la API no se expone a las redes de usuario.
- Autenticación por servicio: cada servicio de la plataforma tiene su credencial propia ante el controlador (sin credenciales compartidas, mínimo privilegio); el acceso se audita.
- Por I2 no cruza ningún secreto de usuario ([`access/00`](../../../access/00_auth_controller.md) §5): solo MAC, perfil, puerto y vigencia.

### 4.2 Órdenes

| Orden | Cuándo | Efecto |
|---|---|---|
| `APLICAR_PERFIL` | Decisión del Policy Engine tras login o elevación | Instala las reglas de sesión del perfil con cookie de sesión y `idle_timeout` |
| `APLICAR_MITIGACION` | Decisión del Policy Engine ante un incidente | Instala la mitigación de la escalera (meter, drop) con cookie de incidente y timeouts |
| `RETIRAR` | Cierre de sesión, fin de elevación, cierre de incidente | Elimina por cookie (`FLOW_MOD` DELETE); `FLOW_REMOVED` confirma |
| `CONSULTAR` | Servicios y consola (solo lectura) | Topología, asociaciones, reglas instaladas por cookie o por dispositivo |

### 4.3 Esquema de la orden de perfil

```json
POST /api/v1/ordenes            (HTTPS, red de gestión)
{
  "orden": "APLICAR_PERFIL",
  "perfil": "ACADEMICO",
  "dispositivo": { "mac": "00:…:A1", "switch": "S1", "puerto": "p1" },
  "vigencia": { "idle_timeout_s": 1800, "hard_timeout_s": 43200 },
  "contexto":  { "sesion": "SES-000123", "cookie": "0x1001",
                 "solicitante": "policy-engine", "motivo": "login" }
}
→ 201 { "estado": "APLICADA", "reglas": [ … ], "confirmada_en": "2026-10-05T14:03:22Z" }
```

Cada campo existe por una razón: `perfil` es la decisión; `dispositivo` es la ubicación aprendida (el controlador verifica que la asociación siga vigente antes de aplicar); `vigencia` alimenta los timeouts reales; `contexto` da la trazabilidad (qué sesión o incidente originó la regla, P11); `cookie` es la llave de retiro. La orden de mitigación es idéntica en forma, con `incidente` en lugar de `sesion` y la respuesta de la escalera (`RATE_LIMIT`, `BLOCK_SOURCE`, `ISOLATE_DEVICE`) en lugar de `perfil`.

### 4.4 Confirmación

La orden **no se considera ejecutada hasta la confirmación** (D-07, I2). La respuesta 201 se emite solo después de que el switch reconoció la instalación (barrera OpenFlow); cualquier fallo devuelve error con causa, y el servicio decide el reintento. Toda orden y su confirmación —o su fallo— se registran en auditoría: la cadena `evento → detección → decisión → aplicación → resultado` (RA-06) tiene en esta confirmación su eslabón «resultado».

**Los dos niveles de confirmación** (cierre de la cuestión de D-08 §6): la confirmación de OpenFlow basta para **aplicado** —la regla está instalada y el controlador publica `MitigationApplied`—, pero no declara la mitigación **verificada**: eso exige que el Monitor mida el antes/después con contadores y publique `MitigationVerified`. El incidente no avanza a mitigado con la regla instalada, sino con el efecto medido (P12): la instalación es un hecho del plano de control; la mitigación es un resultado del plano de datos.

## 5. Consultas que la plataforma hace al controlador

| Consulta | Quién la usa | Para qué |
|---|---|---|
| Asociación vigente de una IP/MAC | IAM (I3/I7) | Validar el vínculo sesión ↔ dispositivo ([`03`](03_identidad_sesiones_y_portal.md) §4) |
| Reglas instaladas por cookie | Incident Manager | Reconciliación tras una caída ([`04`](04_mensajeria_y_eventos.md) §6) |
| Topología y estado de switches | Consola (I7) | Operación y diagnóstico (RNF-08) |

Las consultas son síncronas y de solo lectura: la frontera de [`D-08`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/08_comunicacion.md) §2 no cambia — por el bus viajan eventos y órdenes; las preguntas van directas al interesado.

## 6. Redundancia del plano de control (decisión de E-04)

**Mecanismo elegido:** clúster nativo de ONOS —varias instancias con consenso sobre el estado— **y** switches configurados con más de un endpoint de controlador, con failover.

```text
Estado normal      ONOS-A ◄──── control ──── switches
                   ONOS-B · ONOS-C  (clúster en espera, estado replicado)
Caída de ONOS-A    los switches re-eligen endpoint → ONOS-B continúa
Reconexión         el switch se re-registra; el estado seguro (P10) ya
                   sostenía la red; las reglas se reinstalan y se reconcilian
```

- **Prototipo:** una sola instancia. El clúster y el multi-controlador son la vía documentada que despliega la Fase H; C-04 §4 ya declara que la alta disponibilidad real se analiza por diseño y no se despliega.
- **Por qué esta forma:** el diseño no exige redundancia para operar —el plano de datos conserva lo instalado y todo expira por timeout (P2, P10)—; la exige para **no degradar durante la caída**. El clúster replica el estado (asociaciones, reglas) sin que los servicios cambien nada: I2 sigue siendo un único extremo lógico.
- **Cuantificación:** el tiempo de re-registro y reinstalación tras una caída se mide en el prototipo (RA-07, R4.10) y alimenta el análisis de riesgo D-09.

## 7. Protección (RA-09)

- Canal de control **out-of-band** (RP-02): los switches solo aceptan conexión de control por su interfaz de gestión; el tráfico de usuario no comparte ese camino — la supervivencia del control ante un flood es estructural, no una priorización.
- La API I2 y la administración de ONOS solo escuchan en la red de gestión; desde BASE existe DROP explícito hacia esa red (escalera, prioridad 100).
- Solo el controlador escribe en el pipeline de los switches (P1); las credenciales de control no son las de administración de la plataforma.

## 8. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Orden de perfil extremo a extremo con confirmación | Latencia orden → regla instalada (presupuesto de [`06`](06_deteccion_y_mitigacion.md) §6) | RT-04, RNF-04 |
| Retiro por cookie con `FLOW_REMOVED` observado | La confirmación de retiro existe y llega | RT-10, P10 |
| Caída y retorno del controlador | Tiempo de re-registro y reinstalación de reglas | RA-07, R4.10, E-04 |
| Consulta de asociaciones durante un `MAC_Moved` | La asociación consultada refleja el movimiento | R3.3 |
| Orden inválida / no autenticada | Rechazo, error con causa y registro | RA-09, RNF-01 |

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
mitigaciones simultáneas (peor caso R4)    decenas
─────────────────────────────────────────────────────────
prototipo completo (≈ 20 dispositivos)     ≈ 200–300 entradas
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

# Identidad, sesiones y portal

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** F — Decisiones tecnológicas
**Estado:** Borrador formal para revisión

---

Cuatro decisiones en un documento: el **producto de I4** (RADIUS + directorio), el **repositorio de operadores con TOTP** (I6), la **forma de la sesión** —cookie o token, y si se liga al dispositivo— y la **distinción de población en el portal** (I3). Las tres últimas estaban declaradas como cuestiones abiertas en [`componentes/01`](../../componentes/01_autenticacion.md) §8 y [`componentes/04`](../../componentes/04_identidades_y_poblaciones.md) §8; la forma de I7 —la API de administración— se decide aquí porque depende de la sesión.

## 1. Qué exige la arquitectura

| Exigencia | Origen |
|---|---|
| Autenticación de la comunidad contra el IdP institucional por I4; los operadores, contra el repositorio propio con segundo factor | R1.2, D-07 I4/I6, [componentes/04](../../componentes/04_identidades_y_poblaciones.md) §4 |
| Un solo portal (I3), tres reinos de identidad; la población se distingue **antes** de validar | [componentes/04](../../componentes/04_identidades_y_poblaciones.md) §3 |
| Sesión con vigencia e `idle_timeout`; toda acción queda en accounting y auditoría | P10, R1.9 |
| La sesión es el SSO del operador: abre la consola y las APIs con su rol (I7) | I7, [componentes/04](../../componentes/04_identidades_y_poblaciones.md) §5 |
| El robo de sesión está en la superficie de ataque: la ligadura al dispositivo quedó **a evaluar** | [componentes/03](../../componentes/03_seguridad.md) §4 |

## 2. I4: FreeRADIUS con directorio LDAP detrás

**Decisión.** El IAM es cliente RADIUS; el IdP simulado del prototipo es **FreeRADIUS** con un directorio **OpenLDAP** detrás. En un despliegue real, I4 apunta al IdP institucional —el mismo protocolo y el mismo rol—; el prototipo **simula al IdP, no al protocolo**.

```text
IAM (cliente RADIUS) ── Access-Request ──► FreeRADIUS ──► OpenLDAP
                       Accounting-Request    (IdP simulado: cuentas y atributos)
                       (Start · Interim · Stop)
```

- **Verificación:** `Access-Request`/`Access-Accept` con las cuentas de prueba del directorio; es lo que corre una universidad real (eduroam), así que el prototipo no inventa un mecanismo.
- **Accounting:** el IAM reporta a RADIUS el ciclo de cada sesión de la comunidad (`Start`, `Interim` periódico, `Stop`) con `Acct-Session-Id`; es el registro AAA que R1.9 exige, y alimenta la correlación de la auditoría.
- **Límite:** la integración con el SSO institucional real (delegación del login) queda para un despliegue posterior al prototipo, ya declarado en [componentes/04](../../componentes/04_identidades_y_poblaciones.md) §5.

## 3. Reino operadores: repositorio propio, credenciales y TOTP

**Decisión.** Las identidades privilegiadas (TI, Admin, SA) viven en el repositorio propio de la plataforma (I6): credenciales **hasheadas** (bcrypt) en el esquema del servicio IAM, nunca en claro ni reversibles; segundo factor **TOTP** (RFC 6238) obligatorio para todos los operadores.

### El aprovisionamiento del TOTP

El secreto nace en el **registro del dispositivo privilegiado**, no en el primer login —el registro es el acto administrativo que habilita (P7)—:

```text
1. TI registra el dispositivo del operador en la consola (rol autorizado)
2. el IAM genera el secreto TOTP del operador y lo muestra UNA vez
   como QR (otpauth://totp/…) en la propia consola
3. el operador lo carga en su app autenticadora y verifica un código
4. recién entonces el par (dispositivo, operador) queda habilitado
5. el alta completa —quién, qué, cuándo— queda en auditoría (R1.9)
```

- **Sin internet ni servicios externos:** TOTP es local por definición; encaja con RP-06 (entorno controlado).
- **Verificación del segundo factor en I6, siempre:** el login de operador no tiene una variante sin TOTP. Código perdido = re-aprovisionamiento por la cadena SA→Admin, auditado.
- **Alcance:** obligatorio para operadores; **no** para académicos ([componentes/04](../../componentes/04_identidades_y_poblaciones.md) §4).

## 4. Forma de la sesión: cookie ligada al dispositivo

**Decisión.** Sesión **con cookie opaca** —un identificador sin datos, `HttpOnly`, `Secure`, `SameSite`— emitida por el portal/IAM y validada **del lado del servidor** contra la tabla de sesiones del IAM; y **ligada al dispositivo**: la sesión nace atada a la asociación MAC ↔ switch:puerto ↔ IP que el controlador aprendió, y solo es válida desde esa ubicación.

```text
login (I3) ──► IAM crea sesión ──► consulta I2: ¿asociación vigente de esta IP?
                                   │
             sesión SES-… = { usuario, rol, MAC, S1:p1, IP,
                              idle_timeout, hard_timeout }
                                   │
cada petición: IP de origen == IP de la sesión        ← verificación barata, siempre
evento MAC_Moved del dispositivo de la sesión         ← la sesión se invalida
   └─► SessionClosed · auditoría · investigación (historial de dispositivo)
```

- **Por qué cookie y no token portador:** la cookie no lleva datos (no hay nada que robar del contenido), la validez vive en el servidor y el retiro es inmediato —coherente con P10. Para llamadas desde herramientas, el IAM emite un **token de vida corta derivado de la misma sesión**, con la misma vigencia y la misma ligadura: una sola fuente de verdad, dos formas de presentarla.
- **La ligadura cierra el robo de sesión por reubicación:** una cookie robada presentada desde otro dispositivo tiene otra MAC, otro puerto y otra IP; el acceso se rechaza, la sesión se cierra y el hecho se audita. Es la respuesta concreta a la fila «robo de sesión» de [componentes/03](../../componentes/03_seguridad.md) §4.
- **El costo no existe:** la asociación ya la mantiene el controlador (P7); ligar la sesión es consultarla (I2, [`01`](01_controlador_y_api_northbound.md) §5).
- **I7 queda definido por esto:** las APIs de administración de cada servicio son **REST/JSON** validadas del lado del servidor contra la sesión y el rol —nunca del lado del cliente—; la consola es un cliente de esas APIs, no un servicio con credenciales propias. La sesión es el SSO ([componentes/04](../../componentes/04_identidades_y_poblaciones.md) §5).

## 5. Vigencias por perfil (valores iniciales)

Dos relojes por sesión, ambos configurables: el **`idle_timeout`** de la regla en el switch (el dispositivo la expira solo, `FLOW_REMOVED` lo informa) y el **tope absoluto** en el IAM (la sesión no se renueva más allá). El valor de la regla y el de la sesión son **el mismo**: una sola cifra por perfil, sin desincronización posible.

| Perfil | `idle_timeout` | Tope absoluto | Nota |
|---|---|---|---|
| BASE | — | — | sin sesión: no hay nada que expirar |
| ACADÉMICO | 30 min | 12 h | la sesión acompaña la jornada académica; el idle devuelve el equipo a BASE |
| Operador (TI/Admin/SA) | 15 min | 8 h | más estricto: la sesión abre la red de gestión, la consola y las APIs (R1.8, RA-09) |
| Elevación temporal | según la elevación | 1 h por defecto | vive en `PermissionRepository`; el tope es parte de la decisión del Policy Engine (P10) |

Los valores son el punto de partida del prototipo; su efecto se mide (expiración observada, regreso a BASE, ausencia de sesiones pegadas) y el resultado se reporta con RNF-12. Un logout explícito no espera a ningún reloj: retiro por cookie y `SessionClosed` inmediatos ([`access/00`](../../../access/00_auth_controller.md) §3.6).

## 6. Distinción de población en el portal: selector explícito

**Decisión.** El portal —un solo servicio— presenta un **selector explícito de población** en su entrada: «Comunidad universitaria» y «Personal de operación». Cada opción determina la **ruta de verificación** (RADIUS/LDAP o repositorio propio + TOTP); el mismo formulario sirve a ambas.

- **Por qué selector y no convención de identificador:** una convención (`usuario@dominio`) entrena al usuario a revelar su reino con cada intento y convierte el formato del identificador en información pública; el selector lo declara sin ambigüedad y sin inferencias.
- **Por qué no URLs separadas:** serían dos vistas del mismo servicio con doble superficie de mantenimiento y de phishing sin ganancia de seguridad —misma razón por la que no hay dos portales ([componentes/01](../../componentes/01_autenticacion.md) §6).
- **El selector no concede nada:** solo elige la ruta de verificación. El rol y los privilegios provienen siempre de la fuente de identidad, jamás de lo que el usuario eligió en pantalla. Un intento de operador con credenciales de comunidad —o al revés— falla en la verificación, y queda auditado.
- La población elegida es un dato de auditoría del intento de login (R1.9), útil en la investigación del historial de dispositivo.

## 7. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Login de comunidad completo (I3 → IAM → RADIUS → LDAP) con accounting | Sesión creada, reglas instaladas, registro AAA | R1.2, R1.9, I4 |
| Login de operador con TOTP; código incorrecto | Rechazo del segundo factor y auditoría | R1.2, MFA |
| Cookie presentada desde otro dispositivo (otra MAC/IP) | Rechazo, invalidación y evento auditado | RNF-01, componentes/03 §4 |
| `MAC_Moved` del dispositivo con sesión viva | `SessionClosed` inmediato y regreso a BASE | R3.3, P10 |
| Inactividad: `idle_timeout` vencido | `FLOW_REMOVED`, cierre y BASE sin intervención | R4.9, P10 |
| Selector de población cruzado (credenciales en la ruta equivocada) | Falla de verificación y registro | RNF-01 |

# Mensajería y eventos

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** F — Decisiones tecnológicas
**Estado:** Borrador formal para revisión

---

El bus de eventos es el canal interno de [`D-08`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/08_comunicacion.md): los componentes de seguridad se comunican por eventos a través de un intermediario (P13) y el catálogo de eventos es su contrato. Esta fase decide **el producto del intermediario (I5), el mecanismo de entrega ordenada, las garantías de entrega y la reconciliación tras un fallo** —los tres últimos diferidos explícitamente por D-08 §4/§6 y E-04 §2.

## 1. Qué exige la arquitectura

| Exigencia | Origen |
|---|---|
| Todo evento del catálogo viaja por el intermediario; publicar no espera al consumidor | P13, D-08 §3 |
| Un consumidor caído **no pierde eventos**: las colas retienen lo no entregado | D-07 I5 |
| Los eventos de un incidente se entregan **en orden**: contrato de identificador de incidente + secuencia monótona | D-08 §4 |
| Las ráfagas de un ataque se absorben en colas; el intermediario caído no detiene a los publicadores | P13, E-04 §2 |
| Tras un fallo, el estado se **reconcilia** contra la realidad del plano de datos | E-04 §2, RA-07 |
| El producto se elige **contra el tamaño real del prototipo**, no contra producción | P4, D-03 §5 |

## 2. Decisión: RabbitMQ

**RabbitMQ** como intermediario de I5, en una instancia única del prototipo. Es un broker de mensajes maduro cuyo modelo —exchange/cola/routing key— calza exactamente con lo que el contrato de D-08 pide sin inventar nada: colas durables (I5: nada se pierde con el consumidor caído), orden FIFO por cola (la entrega ordenada por incidente), confirmaciones de publicación, colas con TTL y auto-borrado (el ciclo de vida de un incidente) y cola de mensajes muertos (lo que no pudo entregarse queda visible, no se pierde).

**Dimensionamiento contra el prototipo (P4).** El bus transporta eventos de **incidente**, no paquetes: un flood sostenido produce decenas de eventos por segundo en el peor caso —muestras de anomalía, transiciones de incidente, aplicaciones y verificaciones—, cada uno del orden de un kilobyte. Es una carga trivial para una instancia única en una VM modesta del laboratorio y, a la vez, suficiente para medir lo que RNF-03/RA-08 piden: la latencia de publicación a consumo y el comportamiento bajo ráfaga. La alta disponibilidad del broker **no se despliega** (C-04 §4); su vía es la misma que la del controlador: por diseño, no en el prototipo.

## 3. Topología de colas

```text
                    exchange  plataforma  (topic, durable)
   publicadores ──────────►  evento.<Tipo>            inc.<INC-id>
                                  │                       │
        colas durables por servicio                    cola por incidente
   ┌──────────┬──────────┬───────────┬──────────┐   ┌──────────────────┐
   │auditoría │ monitor  │ incidentes│ política │   │ inc.INC-0042     │
   │(todo)    │(muestras│(anomalías,│(eleva-   │   │ ciclo de mitiga- │
   │          │ y verif.)│ incidentes)│ ciones) │   │ ción ordenado    │
   └──────────┴──────────┴───────────┴──────────┘   └──────────────────┘
```

- **Exchange único de eventos** (`plataforma`, topic, durable): cada servicio consumidor tiene **su propia cola durable** enlazada a los tipos de evento que le interesan. Añadir un consumidor no toca a ningún publicador (P13); un consumidor caído acumula en su cola y procesa al volver (I5).
- **Cola por incidente** (`inc.<INC-id>`): el ciclo de vida de un incidente —`IncidentOpened`, `MitigationRequired`, `MitigationApplied`, `MitigationVerified`, `MitigationExpired`, las elevaciones asociadas— se publica además en una cola propia del incidente, declarada al abrirse y auto-borrada al cerrarse (con TTL de respaldo). **Es el mecanismo de entrega ordenada que D-08 §4 dejó a esta fase:** orden FIFO de una sola cola, sin reordenamiento en el consumidor.

## 4. Garantías de entrega

| Garantía | Cómo |
|---|---|
| **Nada se pierde con el consumidor caído** | colas durables + mensajes persistentes; el consumidor acumula y procesa al volver |
| **Nada se pierde con el broker caído** | el publicador confirma (`publisher confirms`); si el broker no está, el publicador **bufferiza localmente** (bounded) y reintenta con retroceso progresivo — la ráfaga de un ataque no tumba a nadie (P13, E-04 §2) |
| **Entrega al menos una vez, sin efectos dobles** | ack manual tras procesar; todo evento lleva `evento_id` y los consumidores son **idempotentes** (descartan duplicados por id) |
| **Detección de huecos y desorden** | todo evento de incidente lleva `secuencia` monótona por incidente; el consumidor agrega por incidente y detecta saltos |
| **Lo que no se pudo procesar queda visible** | cola de mensajes muertos (DLQ) por cola: tras N reintentos con retroceso, el mensaje va a la DLQ y su existencia se registra en auditoría — nunca se descarta en silencio |

**Frontera:** el buffer local del publicador es acotado; si se desborda, la pérdida se registra como **hueco declarado** en auditoría — el sistema puede perder un evento bajo una caída doble, pero jamás lo oculta (P11).

## 5. Qué viaja por dónde

- **Eventos** (todos los del catálogo de D-08 §3): por el exchange `plataforma`; los del ciclo de un incidente, además, por su cola `inc.<id>`.
- **Órdenes**: las órdenes de mitigación y de perfil viajan por **I2 hacia el controlador** (síncronas, con confirmación — [`01`](01_controlador_y_api_northbound.md) §4); su eco informativo (`MitigationRequired`, `ElevationGranted`, `ElevationExpired`) viaja como evento —el evento informa, la orden ejecuta (D-08 §3).
- **Preguntas**: no entran al bus (D-08 §2): las consultas administrativas y de reconciliación van directas al interesado.

## 6. Reconciliación tras un fallo (decisión de E-04)

La regla que ordena todo: **el plano de datos es la verdad; los registros se reconcilian contra él.** Los hechos sobreviven en los switches —reglas con cookie y timeout— aunque los servicios pierdan memoria.

| Fallo | Al recuperar |
|---|---|
| **Incident Manager** | relee su cola durable (nada perdido) y **reconcilia contra el controlador**: consulta las mitigaciones vigentes por cookie (I2) y cierra los incidentes cuyas mitigaciones ya expiraron (P10) — una mitigación sin regla viva no puede quedar como activa |
| **Broker** | las colas durables restauran lo pendiente; los publicadores vacían su buffer local; el orden por incidente se restaura por secuencia |
| **Consumidor cualquiera** | procesa el atraso de su cola; la idempotencia absorbe los duplicados del reenvío |
| **Controlador** | los switches conservan reglas y timeouts; al reconectar, re-registro y reinstalación ([`01`](01_controlador_y_api_northbound.md) §6); los servicios confirmados como «aplicado» que ya no existan se reportan como expirados |

## 7. Retención en el broker (decisión de D-08 §6)

El broker es **tránsito, no archivo**: las colas por incidente se autoborran al cerrarse; las colas por servicio tienen TTL de respaldo para lo no entregado; la retención duradera de eventos vive en el `AuditRepository` ([`05`](05_persistencia_auditoria_y_tiempo.md) §4). La capacidad de las colas se acota con límite de longitud y desborde controlado, para que una avalancha no consuma el disco del laboratorio.

## 8. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Publicar con el consumidor detenido; levantarlo | Cero eventos perdidos; todo procesado | I5, D-07 |
| Orden de un ciclo de incidente completo bajo ráfaga | Llegan en orden por la cola del incidente | D-08 §4 |
| Reenvío con duplicados deliberados | Idempotencia: sin efectos dobles | D-08 §4 |
| Detener el broker durante una ráfaga | Buffer local absorbe; reconexión; huecos declarados si los hubo | P13, E-04 |
| Reintento agotado | El mensaje queda en DLQ y en auditoría | P11 |
| Drill de reconciliación: caída del Incident Manager + expiración de una mitigación durante la caída | Al volver, el incidente se cierra por reconciliación con el plano de datos | E-04, P10 |
| Latencia publicación → consumo y caudal sostenido | Los números del prototipo | RNF-03, RA-08 |

# Persistencia, auditoría y tiempo

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** F — Decisiones tecnológicas
**Estado:** Borrador formal para revisión

---

Tres decisiones en un documento: la **persistencia (I6)**, la **retención e integridad de los registros** —lo que E-04 §3 y [componentes/03](../../componentes/03_seguridad.md) §8 dejaron abierto, ahora con motivo forense concreto: el historial de dispositivo— y la **fuente de tiempo común** que E-05 §3 difirió a esta fase. Cierra además la decisión de **visualización** del catálogo de drivers (B-03).

## 1. Qué exige la arquitectura

| Exigencia | Origen |
|---|---|
| Cada servicio persiste sus datos a través de su repositorio: `DeviceRepository`, `IncidentRepository` (`INC-xxxx`), `PolicyRepository`, `PermissionRepository`, `AuditRepository` | D-04 §5 |
| Ningún servicio lee la base de datos de otro: la comunicación es por eventos, no por tablas | D-04, D-07 §3 |
| Los eventos relevantes se almacenan para análisis, asociables a quién, qué, cuándo y por qué | RT-07, RNF-09, P11 |
| Retención y recuperación de registros definidas; aptas para investigación forense | E-04 §3, componentes/05 §6 |
| Fuente de tiempo común: la desincronización deteriora la correlación de eventos | E-05 §3, RNF-09 |
| Información suficiente para supervisar la operación | RT-06, RNF-08 |

## 2. Decisión: PostgreSQL

**PostgreSQL** como almacén de la plataforma, en una instancia única del prototipo con **una base de datos por servicio**. La consolidación de instancia es la permitida por RP-04/RP-07 —el prototipo no opera cinco motores—, pero la frontera no se mueve: **cada servicio accede solo a su base**; ningún servicio consulta la de otro (D-04 §6).

**Por qué relacional:** lo que se persiste es inherentemente relacional y transaccional —dispositivos y sus auditorías, incidentes con su máquina de estados, políticas con vigencia, permisos con TTL, eventos con su cadena de asociación—. La transacción protege la consistencia de la máquina de estados del incidente (nunca dos transiciones a la vez) y las consultas de auditoría que la investigación exige (por dispositivo, por incidente, por operador) son SQL directo. Un solo producto para todo el estado persistente es también la decisión de simplicidad (P4).

```text
PostgreSQL (instancia única del prototipo — red de gestión)
├── bd_registro     dispositivos privilegiados · altas y auditoría del registro
├── bd_iam          operadores (bcrypt) · sesiones · accounting RADIUS
├── bd_incidentes   incidentes INC-xxxx · máquina de estados · acciones
├── bd_politicas    políticas de mitigación · PermissionRepository (elevaciones)
├── bd_auditoria    eventos · acciones · cambios de política · mitigaciones
└── bd_monitor      series de contadores (resúmenes) para línea base y evidencia
```

**Límites:** la persistencia del plano de control (topología y reglas) es del controlador, no de la plataforma; el esquema detallado (columnas, índices) es Fase G; el cifrado en reposo y la gestión de respaldos de un despliegue real pertenecen a la Fase H.

## 3. Qué guarda cada servicio

| Base | Contenido | Clave de la correlación |
|---|---|---|
| `bd_registro` | Dispositivo (MAC, tipo, titular, rol, vigencia, responsable) + historial de altas | `dispositivo_id` |
| `bd_iam` | Cuentas de operador (hash + secreto TOTP), sesiones con su ligadura (MAC/puerto/IP), accounting | `SES-…` |
| `bd_incidentes` | Incidente (`INC-…`), transiciones `DETECTED → … → CLOSED`, acciones ejecutadas, origen | `INC-…` |
| `bd_politicas` | Políticas por severidad, elevaciones con alcance, TTL y responsable | `POL-…` / `PE-…` |
| `bd_auditoria` | Todo evento del catálogo y toda acción, con autor y causa | `evento_id` |
| `bd_monitor` | Resúmenes de contadores (pps, bps, fuentes) por ventana | `(destino, ventana)` |

La correlación entre bases no se hace con JOIN —sería leer la base ajena—: se hace con los identificadores que viajan en los eventos (P11): un incidente tiene su `INC-…`, su sesión, su dispositivo y sus cookies de reglas; con esos cuatro hilos, la auditoría reconstruye la historia completa.

## 4. Auditoría: retención e integridad

**Decisión.** El `AuditRepository` es la fuente autoritativa, con dos formas del mismo registro:

- **Tabla de auditoría** en `bd_auditoria`: consultable por rol (P08, P25), con todos los campos de asociación. Retención en línea: **90 días** (propuesta de despliegue), todo el período de validación en el prototipo.
- **Export JSONL append-only, con cadena de hash:** cada evento se anexa a un archivo diario (`auditoria-AAAA-MM-DD.jsonl`) y cada línea incluye el `sha256` de la línea anterior. Un borrado o una edición intermedia rompe la cadena y es detectable con un verificador de una página. **Es la respuesta a «¿se protegen contra manipulación?»**: la manipulación no se impide —el atacante con acceso total siempre puede borrar— pero **no puede pasar inadvertida**, que es lo que la evidencia forense necesita.

**Recuperación.** Respaldo lógico periódico (`pg_dump`) + el export JSONL, que es a la vez respaldo y evidencia: aunque la base se pierda, la secuencia de eventos sobrevive en texto verificable. En el prototipo se ejecuta un **drill de restauración**: restaurar la auditoría desde el export y verificar la cadena de hash de punta a punta; el tiempo de restauración se reporta (RNF-12).

## 5. Tiempo común

**Decisión.** **chrony** como cliente/servidor NTP en el segmento de gestión: el prototipo tiene **una fuente de tiempo propia** (el servidor de gestión), sincronizada a internet si el laboratorio lo permite y con reloj local disciplinado si no. Todos los nodos —servicios, controlador, hosts simulados— sincronizan contra ella; los switches usan el mismo servidor vía su cliente NTP.

- **Todo sello de tiempo se registra en UTC** (ISO 8601) y la auditoría guarda además el nodo de origen: la correlación (RNF-09) exige que dos eventos de nodos distintos sean comparables, y el orden del historial de dispositivo depende de ello.
- **Verificación:** se mide el desfase de cada nodo contra la fuente; el valor se reporta y se vigila (un desfase creciente es un síntoma temprano, no una sorpresa). Esto cierra el tratamiento de la «desincronización de tiempo» registrado en E-05 §3.

## 6. Visualización

**Decisión.** Dos vistas con audiencias distintas, sin solaparse (P4):

| Vista | Qué es | Para quién |
|---|---|---|
| **Consola** | El componente de administración (I7): consultar y modificar políticas, gestionar el registro de dispositivos, seguir incidentes, consultar auditoría según rol | Los operadores, en la operación diaria |
| **Tableros de observabilidad** | Grafana en modo lectura sobre `bd_monitor` y `bd_auditoria`: línea base, tasas antes/después de una mitigación, tiempos de detección y mitigación, el material de evidencia de R4.10 | La verificación del prototipo y la defensa del proyecto |

La consola no se reconstruye como herramienta de analítica, y los tableros no administran: cada vista hace lo suyo. El conjunto cierra RT-06 y RNF-08.

## 7. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Drill de restauración desde el export JSONL | Auditoría restaurada y cadena de hash verificada | E-04 §3, RT-07 |
| Corrupción deliberada de una línea del export | El verificador la detecta | Integridad, P11 |
| Desfase NTP de cada nodo | Desfase medido y acotado | E-05 §3, RNF-09 |
| Consulta de auditoría por rol | Cada rol ve lo que le corresponde (P08, P25) | R1.9, R2.9 |
| Alimentación de tableros | Línea base y métricas R4.10 visibles como evidencia | RT-06, RNF-08, RNF-12 |
| Aislamiento entre bases | Un servicio no puede leer la base de otro | D-04 §6 |

# Detección y mitigación

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** F — Decisiones tecnológicas
**Estado:** Borrador formal para revisión

---

El corazón de R3 y R4: **qué se observa, con qué frecuencia, con qué umbrales y con qué regla se pasa de la observación a la mitigación**. Esta fase decide el algoritmo de detección, la naturaleza de los umbrales, la frecuencia de I8, la precedencia P9/P12 que [`D-03`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/03_principios_arquitectonicos.md) §7 dejó abierta, y fija el presupuesto de latencia de D-10. Los **valores finales** de umbrales y tiempos no se inventan aquí: se calibran con el prototipo y cierran R4.3/R4.4/R4.10.

## 1. Qué exige la arquitectura

| Exigencia | Origen |
|---|---|
| Obtener del tráfico la información suficiente para detectar scanning, spoofing, anomalías y ataques distribuidos | R3.1–R3.5 |
| Línea base del servicio protegido e indicadores (pps, solicitudes/s, flujos nuevos, fuentes) | R4.1–R4.3 |
| Criterios cuantitativos que distingan tráfico normal de malicioso, con medición de detección, mitigación e impacto | R4.4, R4.10 |
| La cadena nunca salta: detector observa → Policy Engine decide → controlador traduce → switch ejecuta | P8, RA-06 |
| Contadores OpenFlow como única fuente de observación del plano de datos | P11 |
| Mitigar cerca del origen, limitar antes que bloquear, preservar el servicio legítimo | P9, R4.6–R4.8 |

## 2. Observación: qué lee el monitor y con qué frecuencia (I8)

El Monitor nunca habla con los switches: lee a través del controlador (`OFPMP_PORT_STATS`, `OFPMP_FLOW`, I8) y solo contadores (P11). **Decisión de frecuencia:**

| Régimen | Alcance | Frecuencia por defecto |
|---|---|---|
| **Conjunto caliente** | Recursos protegidos y sus puertos/reglas de ingreso | **5 s** |
| **Barrido completo** | Inventario completo de flujos y puertos | **60 s** |

Ambos valores son **configurables**, y esa configurabilidad es en sí la decisión: el presupuesto de carga sobre el plano de control (D-11) y la latencia de detección (D-10) están en tensión, y la resolución se mide — el experimento de sobrecarga de sondeo (RNF-03) prueba 5/30/60 s y reporta carga y latencia resultantes. El barrido completo existe para lo que no está en el conjunto caliente: un destino que despierta interés entra al conjunto caliente a partir del siguiente barrido.

```text
Monitor (observa, no decide)
  cada 5 s   pps · bps · flujos nuevos/s por destino protegido
             y por origen: nº de destinos distintos, flujos nuevos/s
  cada 60 s  inventario completo (flujos y puertos)
        │ métricas y features por el broker (D-04: la materia prima)
        ▼
Detection Engine (clasifica, no ordena)
        │ AnomalyDetected (tipo, objetivo, origen, severidad propuesta)
        ▼
Incidente → Policy Engine → Controlador → Switch   (P8)
```

**Monitor y Detección: dos servicios, también en el prototipo** (cierre de la cuestión de D-04 §7). El Monitor observa y mantiene la línea base; la Detección juzga y clasifica; las métricas viajan del Monitor a la Detección por el broker —el contrato que D-04 ya fija—. Se mantienen separados: la frontera «observar no es juzgar» (P8) es la que la validación comprobó, separarla cuesta dos contenedores, y consolidarlos difuminaría en la demostración el mismo límite que E-01/E-02 trazaron.

## 3. Línea base y umbrales: dinámicos con piso estático

**Decisión.** La línea base por destino protegido es una **media móvil exponencial (EWMA)** del indicador —pps, bps, flujos nuevos— con su varianza también suavizada. El umbral de disparo es **relativo** (la desviación sobre la media, en múltiplos de la desviación típica) y lleva **piso absoluto** (un mínimo por debajo del cual nada dispara) y **histéresis** (cuesta más entrar que salir, para no oscilar). La confirmación exige **N ventanas sostenidas**.

**Por qué así y no un umbral fijo:** el tráfico del campus no es estacionario —varía por hora, por día, por actividad académica—; un umbral fijo calibrado en el peor momento ciega al detector en hora valle y produce falsos positivos en hora punta. La EWMA se adapta sola. El **piso** existe porque la adaptación tiene un punto ciego: un servicio silencioso no debe disparar por pasar de 3 a 6 pps — el piso es estático por diseño. La combinación cierra la pregunta «umbrales estáticos o dinámicos» de B-03 §4: **el mecanismo es dinámico; los pisos y los valores iniciales son estáticos y conservadores; la calibración final sale de las mediciones.**

Valores iniciales del prototipo — punto de partida explícito, ajustado con mediciones (R4.4):

| Parámetro | Valor inicial | Papel |
|---|---|---|
| α (suavizado EWMA) | 0,2 | memoria de la línea base (~5 ventanas) |
| Ventana | 5 s | igual al pulso del conjunto caliente |
| N (ventanas sostenidas) | 3 | confirmación: 15 s antes de proponer acción |
| k de entrada / salida | 4σ / 2σ | histéresis |
| Piso por destino protegido | 200 pps · 2 Mbps | evita disparos triviales |
| Calentamiento | 30 min | antes de él rigen los pisos; el detector observa y alerta, no actúa solo |

## 4. Clasificación por patrón

Cada clase del catálogo ([`D-11.1`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/11.1_catalogo_de_ataques_y_amenazas.md)) tiene su firma de features:

| Clase | Features | Regla de clasificación |
|---|---|---|
| **Flood volumétrico / DDoS** (R4) | pps/bps hacia destino protegido | ≥ k·σ sobre la línea base **y** sobre el piso, sostenido N ventanas |
| **Ataque distribuido** (R3.5) | nº de fuentes distintas contra el mismo destino | ≥ 10 fuentes en 60 s con tasa agregada sobre el umbral: se clasifica distribuido y se mitiga **por switch de ingreso de cada origen** (P9) |
| **Brute-force** (R4) | solicitudes/s por origen hacia puertos de aplicación (portal) | ≥ 20 solicitudes/s por origen sostenidas, con tasa de nuevas conexiones alta |
| **Scanning** (R3.2) | nº de destinos distintos por origen, con volumen por destino muy bajo | > 20 destinos distintos en 60 s: patrón de barrido |
| **Spoofing y `MAC_Moved`** (R3.3) | *no son estadísticos* | El controlador compara contra la asociación aprendida: incoherencia = hecho determinista, no umbral (P7) |

Las detecciones deterministas (última fila) tienen severidad propia y **no esperan confirmación estadística**: una incoherencia sostenida es un hecho, no una tendencia.

## 5. De la severidad a la respuesta: qué se automatiza

La escalera de respuestas ya está fijada: `RATE_LIMIT → BLOCK_SOURCE → ISOLATE_DEVICE → QUARANTINE` ([`D-04`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/04_descomposición_arquitectonica.md)). La decisión de esta fase es **qué peldaños se ejecutan sin humano**:

| Peldaño | Automatización | Fundamento |
|---|---|---|
| `RATE_LIMIT` (meter) | **Automático** ante anomalía confirmada | Mínima intervención; preserva el servicio legítimo (P9); reversible por timeout (P10) |
| `BLOCK_SOURCE` (drop del origen) | **Automático** si la anomalía persiste pese al límite, o si el patrón es inequívoco | El origen ya mostró el comportamiento; el bloqueo es por origen, no por destino (P9); TTL corto |
| `ISOLATE_DEVICE` | **Automático solo ante detección determinista** (spoofing sostenido, `MAC_Moved`) | No depende de umbrales: es un hecho verificado contra la asociación; con TTL y auditoría inmediata |
| `QUARANTINE` (bloqueo total de alto impacto) | **Aprobación humana** | Regla ya fijada en D-03 §5: el bloqueo total de alto impacto exige aprobación del operador |

La frontera automático/humano sigue una regla única: **se automatiza lo reversible y proporcional; lo total y de alto impacto pasa por una persona.**

## 6. Precedencia P9/P12 (cierre de la cuestión abierta)

Si una mitigación que preserva el tráfico legítimo no alcanza las métricas exigidas —el ataque baja, pero no a los valores de la línea base—, **prima P9 en la ejecución automática**: el sistema no sube la fuerza para «mejorar la métrica» a costa del servicio. **P12 gobierna la evaluación**: la brecha entre el resultado y la métrica esperada se mide, se registra y **escala a revisión humana** — el operador decide si el peldaño siguiente corresponde. Así la disponibilidad y la métrica no compiten: la métrica obliga a mirar, la disponibilidad decide sin humano solo hasta donde es reversible.

## 7. Presupuesto de latencia (D-10)

| Etapa | Presupuesto provisional | Cómo se cumple |
|---|---|---|
| Ataque → detección | ≤ 15 s | 3 ventanas de 5 s (N=3); patrones inequívocos pueden confirmar antes |
| Detección → orden confirmada | ≤ 5 s | cadena de eventos + orden sincrónica con confirmación ([`01`](01_controlador_y_api_northbound.md) §4.4) |
| Orden → efecto en el plano de datos | < 1 s | meter nativo; la ejecución no depende del controlador (P2) |
| **Total percibido** | **≤ 20 s en el peor caso de patrón lento** | Los valores finales se miden y reportan (R4.10) |

## 8. Verificación

**Protocolo de escenarios** (tráfico legítimo en paralelo, siempre — sin él no se mide R4.8):

| Escenario | Mide | Cierra |
|---|---|---|
| Flood volumétrico controlado (RP-06/08) | Tiempo de detección, de mitigación y de retiro; tasa efectiva del meter | R4.2, R4.5, R4.6, R4.10 |
| Flood con tráfico legítimo simultáneo | Peticiones legítimas exitosas durante la mitigación (impacto, R4.8) | R4.8, P9 |
| Ataque distribuido desde varios orígenes | Detección por nº de fuentes; mitigación por switch de ingreso | R3.5 |
| Scanning y `brute-force` controlados | Detección por patrón; escalera hasta BLOCK | R3.2, R4 |
| Spoofing e `MAC_Moved` | Detección determinista; aislamiento automático | R3.3, P7 |
| Días de tráfico de fondo sin ataques | **Falsos positivos** por día; ajuste de α, k y pisos | B-03 §5, D-14 |
| Barrido de frecuencias de sondeo (5/30/60 s) | Carga sobre el plano de control y latencia resultante | RNF-03, D-11 |
| Umbral estático calibrado vs. adaptativo | Comparación cuantitativa de detección y falsos positivos | D-14, comparación de alternativas |

El resultado de estos escenarios es el **cierre cuantitativo de R4.3/R4.4/R4.10, RNF-03 y RNF-04**, y la calibración final de los valores iniciales de §3.

# Perímetro (R5)

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** F — Decisiones tecnológicas
**Estado:** Borrador formal para revisión

---

El único hueco material del HLD ([`E-02`](../E-Validacion_del_HLD/02_requisitos_a_componentes.md) §5, CU-08): el perímetro y el bloque R5. Esta fase lo cierra: **evaluación IDS/IPS de R5.2, definición del perímetro (R5.1), determinación de indicadores maliciosos (R5.6) y demostración del bloqueo con la cadena SDN (R5.4, R5.5, R5.7)**. La arquitectura interna ya estaba lista para recibir eventos perimetrales (R5.7 no requiere nada nuevo: es la misma cadena R3/R4).

## 1. Qué exige el requerimiento

| Requisito | Qué pide |
|---|---|
| R5.1 | Definir los mecanismos de control entre redes externas e internas |
| R5.2 | **Evaluar** el uso de IDS, IPS o ambos |
| R5.3 | Analizar el tráfico externo relevante para identificar actividad maliciosa |
| R5.4 | Bloquear tráfico desde IP identificadas como maliciosas |
| R5.5 | Bloquear conexiones hacia destinos maliciosos |
| R5.6 | Definir cómo se determina que una IP, URL u otro indicador es malicioso |
| R5.7 | Que los eventos perimetrales generen políticas o acciones sobre la red SDN |
| R5.8 | Registrar los eventos |

R5 no es un requerimiento asignado: se **diseña por completo y se demuestra con un escenario representativo** (B-03 §3, P1), según lo permita el entorno.

## 2. Evaluación IDS/IPS (R5.2): IDS con enforcement SDN

**Decisión.** Detección perimetral con **IDS** —análisis de tráfico espejado, sin estar en el camino— y **bloqueo ejecutado por la red SDN**: el switch de borde descarta por orden del controlador. La función del IPS existe y se ejerce en cada bloqueo; lo que no existe es un **appliance inline**.

La evaluación que R5.2 pide, en términos de arquitectura:

| Criterio | Appliance inline (IPS) | IDS + enforcement SDN (elegido) |
|---|---|---|
| Separación detectar/decidir/ejecutar (P8) | Fusiona detección y ejecución en un punto | Cada función en su componente: el IDS observa, el Policy Engine decide, el switch ejecuta |
| Disponibilidad (RNF-02) | Es un punto único **en el camino**: su caída o saturación corta el tráfico externo | Fuera del camino: su caída degrada la detección, no el servicio |
| Integración SDN (R5.7) | El bloqueo vive fuera del controlador; la red no aprende | El bloqueo **es** la cadena SDN: evento → política → `FLOW_MOD` en el borde |
| Evidencia para el curso | — | La demostración perimetral ejercita el mismo pipeline que R4, con el borde como punto de aplicación |

Un IDS dedicado más el enforcement SDN **es** «IDS y el efecto de IPS», sin pagar el costo arquitectónico de un inline ni duplicar la función de ejecución que el switch ya cumple.

## 3. La arquitectura perimetral

```text
        RED EXTERNA (simulada en el prototipo)
              │
   ┌──────────▼──────────┐   espejo (SPAN)    ┌────────────────────┐
   │ switch de BORDE     │───────────────────►│ sensor IDS         │
   │ (Pica8/PicOS)       │   tráfico externo  │ (Suricata, IDS)    │
   │ reglas de bloqueo   │                    │ firmas + anomalías │
   └──────────┬──────────┘                    └─────────┬──────────┘
              │ segmento interno                          │ EVE JSON
              │                                           ▼
              │                                 adaptador del sensor
              │                                 (parte del Detection Engine)
              │                                           │ AnomalyDetected
              │                                           │ (origen = perímetro)
              │◄──────── FLOW_MOD DROP ──── Controlador ◄───┴─ Policy Engine
```

- **Punto de control (R5.1):** el switch de borde es el punto de enforcement; entre la red externa y el segmento interno no hay más camino que él. En el prototipo, la «red externa» es un segmento controlado del laboratorio que representa ese papel; los ataques perimetrales se generan dentro del entorno (RP-06/08).
- **Inspección (R5.3):** Suricata en modo IDS sobre el puerto espejo del borde: ve todo el tráfico externo relevante sin participar del reenvío. Sus alertas salen en formato **EVE JSON**.
- **Integración (R5.7):** un adaptador —que pertenece al Detection Engine como su **sensor perimetral**— convierte cada alerta en un `AnomalyDetected` con `origen = perímetro`, el mismo contrato que cualquier otra anomalía. Desde ahí, la cadena es la conocida: Incidente → Policy Engine → controlador → **drop en el switch de borde**.
- **Bloqueo (R5.4):** la mitigación instala un DROP del origen malicioso en el borde —el tráfico externo malicioso se descarta antes de entrar (P9 aplicado al perímetro).
- **Bloqueo hacia destinos (R5.5):** para un destino externo identificado como malicioso, el Policy Engine ordena el DROP de los flujos internos hacia ese destino —la dirección inversa del mismo mecanismo—.

**Qué NO cambia:** el IDS no decide ni ordena (P8); sus alertas son insumo. Y la cadena conserva la trazabilidad completa: una alerta del sensor es tan auditable como una anomalía interna (RA-06).

## 4. Determinación de indicadores (R5.6)

**Decisión.** Dos fuentes, una sola puerta:

1. **Veredicto de las firmas del IDS** sobre el tráfico observado: la actividad maliciosa se identifica en el hecho, con la regla que la detectó como evidencia.
2. **Lista de inteligencia propia de la plataforma**: entradas (**IP o URL maliciosa + origen + vigencia + responsable**) mantenidas desde la consola por los operadores, con TTL como todo estado del sistema (P10).

**La regla de promoción cierra el ciclo:** una alerta perimetral confirmada por un operador puede convertirse en entrada de la lista —con vigencia y responsable— y entonces el bloqueo ya no depende de volver a ver el ataque: el indicador conocido bloquea de entrada. La lista se consulta al decidir; nada se bloquea «para siempre»: cada entrada expira y se revisa.

**Alcance del prototipo:** firmas del IDS + lista propia. La suscripción a feeds externos de inteligencia es una **extensión de despliegue** (Fase H): el mecanismo —ingerir, evaluar, agregar con vigencia— es el mismo; la fuente cambia.

## 5. Registro (R5.8)

Toda alerta perimetral, toda decisión y todo bloqueo entran al `AuditRepository` con `origen = perímetro`, la firma o regla que detectó, el indicador involucrado y la cookie de la regla de bloqueo ([`05`](05_persistencia_auditoria_y_tiempo.md) §4). Los eventos perimetrales aparecen en la consola junto a los internos: una sola historia de la seguridad de la red.

## 6. Cierre del bloque R5

| Requisito | Cómo queda cubierto |
|---|---|
| R5.1 | Switch de borde como único punto de control entre red externa y interna (§3) |
| R5.2 | Evaluación hecha: IDS + enforcement SDN, con la comparación de §2 |
| R5.3 | Suricata en modo IDS sobre el espejo del borde (§3) |
| R5.4 | DROP del origen malicioso en el borde, por la cadena SDN (§3) |
| R5.5 | DROP de flujos internos hacia destinos maliciosos (§3) |
| R5.6 | Firmas + lista propia con vigencia y responsable (§4) |
| R5.7 | La alerta perimetral entra como `AnomalyDetected` y recorre la cadena existente (§3) |
| R5.8 | Registro con origen perimetral en la auditoría (§5) |

Con esto, el hueco CU-08 de [`E-01`](../E-Validacion_del_HLD/01_casos_de_uso_a_componentes.md) y el bloque R5 de E-02 quedan cerrados **por diseño**; la demostración en el prototipo depende de que el entorno la permita (B-03 §3).

## 7. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Ataque desde el segmento externo simulado → alerta del IDS → bloqueo en el borde | Latencia alerta → bloqueo; el ataque cesa en el borde | R5.3, R5.4, R5.7 |
| Bloqueo hacia un destino malicioso de la lista | Flujos internos hacia ese destino descartados | R5.5 |
| Entrada de lista: alta desde la consola, uso inmediato, expiración por vigencia | La lista es operativa y temporal | R5.6, P10 |
| Carga del espejo y descarte del IDS bajo tráfico externo alto | El sensor no degrada el reenvío (no está en el camino) | RNF-02 |
| Días de tráfico externo normal | Falsos positivos del sensor y de la lista | B-03 §5 |

# Entorno del prototipo

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** F — Decisiones tecnológicas
**Estado:** Borrador formal para revisión

---

La decisión de **virtualización o simulación** que activan los drivers D-06 y D-11 (B-03 §4), y con ella el entorno sobre el que todo lo decidido en esta fase se verifica. El marco ya está fijado por [`C-04`](../C-Contexto/04_alcance_de_la_infraestructura.md): la infraestructura del prototipo **representa** a la de referencia en los aspectos que los escenarios y las métricas necesitan, sin reproducir su escala (RP-04, RP-05).

## 1. Decisión: servicios en contenedores, hosts y atacantes en máquinas virtuales, plano de datos en el switch real

| Elemento del prototipo | Forma | Por qué |
|---|---|---|
| Servicios de la plataforma (IAM, registro, Monitor, Detección, Incidentes, Políticas, Auditoría, portal) | **Contenedores**, uno por servicio, en el segmento de gestión | Aislamiento y responsabilidad por servicio (P3); composición declarativa y reproducible (RNF-11); consolidación de despliegue permitida por RP-04/RP-07 |
| Controlador (ONOS) | Contenedor/VM propia en el segmento de gestión | Un plano de control separado del resto (P1); su ciclo de vida es distinto al de los servicios |
| Intermediario (RabbitMQ) y persistencia (PostgreSQL) | Contenedores en el segmento de gestión | Infraestructura de la plataforma; respaldo y operación simples |
| Hosts de usuario y servidores de servicio | **Máquinas virtuales** con su propia MAC e IP | Cada host debe ser un dispositivo real para la red: MAC propia, tráfico propio, conexión por un puerto distinto (R1.1); el contenedor compartiría identidad de red y no serviría |
| Atacante y «red externa» | VM en el segmento externo simulado | El atacante necesita su propia identidad de red y su punto de ingreso; los ataques se generan **solo dentro del entorno del proyecto** (RP-06/08) |
| Switches (plano de datos) | **Pica8/PicOS físicos** del laboratorio (RP-11) | Único lugar donde las primitivas OpenFlow y la capacidad de reglas se verifican de verdad ([`02`](02_plano_de_datos_pica8.md) §4) |
| Sensor perimetral (Suricata) | VM con la interfaz del espejo | Fuera del camino de reenvío ([`07`](07_perimetro_r5.md) §3) |
| Canal de control | Interfaces de gestión del switch, out-of-band (RP-02) | Aislado del tráfico de usuario (RA-09) |

**Conmutador virtual OpenFlow 1.3 como apoyo de desarrollo:** para el trabajo fuera de las ventanas de laboratorio y para la integración continua, la topología puede levantarse íntegramente virtual. Sus límites se declaran: las pruebas de primitivas y capacidad que deciden el diseño (§4 de [`02`](02_plano_de_datos_pica8.md)) se ejecutan **siempre contra el switch físico**; lo virtual sirve para construir y ensayar, no para firmar la verificación.

## 2. Segmentación del prototipo

La segmentación de referencia se representa con lo mínimo que la hace verificable (R2.6, C-04 §4):

```text
┌─────────────┐   ┌──────────────┐   ┌───────────────────────────────┐
│  EXTERNA    │   │  USUARIOS    │   │  GESTIÓN (out-of-band)        │
│  VM atacante│──►│  VMs host    │   │  controlador · servicios ·    │
│  (simulada) │   │  (académicos │   │  broker · BD · consola ·      │
│             │   │   y opera-   │   │  monitor · sensor IDS         │
├─────────────┤   │   dores)     │   ├───────────────────────────────┤
│ switch de   │   │              │   │  SERVIDORES                   │
│ BORDE       │   │  switches de │   │  VMs de servicio académico    │
│ (Pica8)     │   │  acceso      │   │  (representan los activos)    │
└─────────────┘   └──────────────┘   └───────────────────────────────┘
```

- Las poblaciones ocupan sus VMs en el segmento de usuarios; la elevación de un operador se demuestra desde su propia VM, con reglas de sesión hacia la gestión (escalera, prioridad 200).
- El segmento de gestión no es alcanzable desde BASE: el DROP de la escalera usa exactamente esta frontera (R1.6, RA-09).
- Los «servidores de servicio» son las VMs que representan los activos protegidos de R2; su clasificación (general/privilegiado/crítico) es la de [`A-02`](../A-Modelo_de_dominio/02_recursos_y_servicios.md).

## 3. Generación de tráfico

| Tráfico | Desde | Herramientas | Escenario |
|---|---|---|---|
| Legítimo de fondo | VMs de usuarios | Cliente HTTP/DNS/DHCP scriptado; carga sostenida (p. ej. `iperf3`, bucles `curl`) | Línea base y tráfico concurrente durante mitigaciones (R4.8) |
| Flood volumétrico | VM atacante (externa o interna según el caso) | Generador de paquetes a tasa configurable (`hping3`, `Scapy`) | R4 completo |
| Ataque distribuido | Varias VMs origen | El mismo generador, coordinado | R3.5 |
| Brute-force de solicitudes | VM de usuario | Peticiones HTTP concurrentes al portal | R4 |
| Scanning | VM de usuario | Barrido de puertos/destinos (`nmap`-equivalente controlado) | R3.2 |
| Spoofing / `MAC_Moved` | VM de usuario | Tráfico con IP/MAC manipuladas; cambio de puerto | R3.3 |
| Ataque perimetral | VM en el segmento externo | Firmas dirigidas al sensor | R5 ([`07`](07_perimetro_r5.md) §7) |

Todo se ejecuta **dentro del entorno del proyecto** (RP-06, RP-08): sin tráfico malicioso hacia redes del campus ni de terceros. Cada escenario queda definido por parámetros (orígenes, tasa, duración, destino protegido) que se registran junto a la medición — sin ellos la métrica no es reproducible.

## 4. Reproducibilidad (RNF-11)

- **Composición declarativa:** el conjunto de servicios, broker, base de datos y hosts simulados se levanta desde una definición versionada; recrear el entorno no es un procedimiento manual.
- **Configuración del plano de datos scriptada:** la configuración base de los switches (modo OpenFlow, canal de control, espejo del borde) se aplica desde guiones versionados.
- **Escenarios como parámetros:** cada prueba de ataque y de carga se lanza con parámetros explícitos y deja su registro —repetición bajo condiciones controladas— junto a las métricas que produce.
- **Versiones fijadas:** los componentes del entorno se fijan por versión para que una repetición futura no compare contra otro software.

## 5. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Recrear el entorno completo desde la definición versionada | Sin pasos manuales; mismo estado de partida | RNF-11 |
| Repetir un escenario de ataque con los mismos parámetros | Métricas comparables entre corridas | RNF-11, RNF-12 |
| Ejecutar la verificación de primitivas en el switch físico (V1–V7 de [`02`](02_plano_de_datos_pica8.md) §4) | Lo que se firma es del dispositivo real, no del apoyo virtual | C-04 §5 |
| Ataque de carga contra el segmento de gestión durante un escenario | El canal out-of-band sostiene el control | RA-09, P2 |

## 6. Límites

- **Escala (RP-04):** el prototipo no reproduce el campus; representa los escenarios. Las cifras de capacidad y rendimiento valen para el prototipo, y así se reportan.
- **Alta disponibilidad:** la redundancia del plano de datos **se despliega y se mide** — topología de ocho switches dual-homed fijada en la Fase H ([`H-01`](../H-Despliegue/01_infraestructura_fisica.md) §3); la del plano de control (clúster del controlador) se documenta, no se despliega (C-04 §4). Los mecanismos quedaron decididos en [`01`](01_controlador_y_api_northbound.md) §6 y [`04`](04_mensajeria_y_eventos.md) §6.
- **Canal in-band:** el prototipo usa out-of-band (RP-02); la variante in-band queda como objetivo aspiracional del despliegue, ya registrado en C-04 §6.
- **Hardware:** las ventanas de uso del laboratorio condicionan cuándo corre la verificación física; el resto del tiempo rige el apoyo virtual con sus límites declarados (§1).

# Síntesis y trazabilidad

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** F — Decisiones tecnológicas
**Estado:** Borrador formal para revisión

---

La vista completa de la fase: qué se decidió, contra qué requisito responde cada decisión, dónde se verifica y qué queda pendiente. Los documentos de la serie son el detalle; este es el mapa.

## 1. Las decisiones, de un vistazo

| Papel | Decisión | Documento |
|---|---|---|
| Controlador SDN | ONOS, instancia única; API de órdenes sobre su REST | [`01`](01_controlador_y_api_northbound.md) |
| Plano de datos | PicOS OpenFlow 1.3; primitivas verificadas contra el dispositivo | [`02`](02_plano_de_datos_pica8.md) |
| Identidad | FreeRADIUS + OpenLDAP (I4); repositorio propio con TOTP para operadores | [`03`](03_identidad_sesiones_y_portal.md) |
| Sesión | Cookie opaca ligada al dispositivo; I7 = REST por servicio con rol validado en servidor | [`03`](03_identidad_sesiones_y_portal.md) |
| Portal | Un servicio, selector explícito de población | [`03`](03_identidad_sesiones_y_portal.md) |
| Bus de eventos | RabbitMQ; cola por incidente para la entrega ordenada; at-least-once con DLQ | [`04`](04_mensajeria_y_eventos.md) |
| Persistencia | PostgreSQL, una base por servicio; auditoría con export JSONL encadenado | [`05`](05_persistencia_auditoria_y_tiempo.md) |
| Tiempo | chrony, fuente propia del prototipo; UTC en todo registro | [`05`](05_persistencia_auditoria_y_tiempo.md) |
| Visualización | Consola (administración) + tableros de observabilidad en lectura | [`05`](05_persistencia_auditoria_y_tiempo.md) |
| Detección | EWMA con umbral relativo, piso absoluto e histéresis; frecuencias 5 s / 60 s | [`06`](06_deteccion_y_mitigacion.md) |
| Automatización | Escalera automática hasta lo reversible; cuarentena con humano | [`06`](06_deteccion_y_mitigacion.md) |
| Perímetro | Suricata IDS sobre espejo + enforcement SDN en el borde | [`07`](07_perimetro_r5.md) |
| Entorno | Contenedores por servicio; VMs de hosts; Pica8 físico como plano de datos | [`08`](08_entorno_del_prototipo.md) |

## 2. Trazabilidad: decisión → requisito → verificación

| Decisión | Requisitos y drivers | Verificación en el prototipo |
|---|---|---|
| Controlador ONOS | RA-02, RT-03, RT-05, D-06 | Orden de perfil extremo a extremo; caída y reinstalación ([`01`](01_controlador_y_api_northbound.md) §8) |
| API de órdenes (I2) | RT-04, R2.10, RNF-04 | Latencia orden → confirmación; rechazo de órdenes inválidas |
| Redundancia y failover | RA-07, D-09, E-04 | Convergencia ante corte de enlace y caída de switch (desplegado: ocho switches dual-homed); clúster del controlador documentado, no desplegado |
| Primitivas PicOS | RT-05, R4.6, R4.7, C-04 §5 | Checklist V1–V7 ([`02`](02_plano_de_datos_pica8.md) §4) |
| Capacidad de reglas | RNF-05, RA-08, D-11 | Experimento de llenado de tabla ([`02`](02_plano_de_datos_pica8.md) §5) |
| I4 RADIUS + LDAP | R1.2, R1.9 | Login de comunidad con accounting ([`03`](03_identidad_sesiones_y_portal.md) §7) |
| Operadores: repositorio + TOTP | R1.2, R1.8 | Login con segundo factor; alta auditada |
| Sesión ligada al dispositivo | RNF-01, P10, componentes/03 §4 | Cookie desde otro dispositivo → rechazo; `MAC_Moved` → cierre |
| Vigencias por perfil | R1.3, P10 | Expiración por inactividad → BASE ([`03`](03_identidad_sesiones_y_portal.md) §5) |
| Selector de población | I3, RNF-01 | Ruta de verificación por población; cruce falla y se audita |
| Broker RabbitMQ y orden por incidente | I5, P13, D-08 §4 | Consumidor detenido; orden bajo ráfaga; DLQ ([`04`](04_mensajeria_y_eventos.md) §8) |
| Reconciliación tras fallo | RA-07, E-04 | Drill: caída + expiración + retorno ([`04`](04_mensajeria_y_eventos.md) §6) |
| PostgreSQL por servicio | I6, D-04 §6 | Aislamiento entre bases; drill de restauración |
| Auditoría: retención e integridad | RT-07, RNF-09, P11 | Verificador de cadena de hash; consulta por rol |
| Tiempo común | RNF-09, E-05 | Desfase NTP por nodo |
| Visualización | RT-06, RNF-08 | Tableros con línea base y métricas R4.10 |
| Detección EWMA + pisos | R3.1–R3.5, R4.1–R4.4 | Escenarios de ataque + días de fondo (falsos positivos) |
| Frecuencia de I8 | RNF-03, D-11 | Barrido 5/30/60 s: carga y latencia |
| Escalera automático/humano | R3.7, R3.8, RT-08, P8, P9 | Escenarios R4/R3 hasta cada peldaño |
| Precedencia P9/P12 | D-03 §7 | Mitigación que preserva servicio con métrica no alcanzada → escala a humano |
| Presupuesto de latencia | RNF-04, D-10, R4.10 | Tiempos medidos por escenario |
| Perímetro IDS + SDN | R5.1–R5.8 | Ataque desde el segmento externo → bloqueo en el borde ([`07`](07_perimetro_r5.md) §7) |
| Entorno del prototipo | RP-05, RNF-11, C-04 | Repetición de escenarios con parámetros registrados |

## 3. Lo que esta fase cierra

Cada cuestión que el corpus difirió a la Fase F, con su cierre:

| Cuestión diferida | Origen | Cierre |
|---|---|---|
| Producto del controlador | RA-02, B-03 D-06 | [`01`](01_controlador_y_api_northbound.md) §2 |
| Forma de I2 y esquema de la orden de perfil | D-07 §4, access/00 §6 | [`01`](01_controlador_y_api_northbound.md) §4 |
| Forma de I7 | D-07 §4 | [`03`](03_identidad_sesiones_y_portal.md) §4 |
| Redundancia del plano de control | E-04 §4 | [`01`](01_controlador_y_api_northbound.md) §6 |
| Verificación de primitivas y capacidad de reglas | C-04 §6; flows/01 y flows/04 | [`02`](02_plano_de_datos_pica8.md) §4–§5 |
| Producto de I4 | componentes/01 §7 | [`03`](03_identidad_sesiones_y_portal.md) §2 |
| Forma de la sesión; ligadura al dispositivo | componentes/01 §8, componentes/03 §8 | [`03`](03_identidad_sesiones_y_portal.md) §4 |
| Aprovisionamiento del TOTP | componentes/04 §4 | [`03`](03_identidad_sesiones_y_portal.md) §3 |
| Distinción de población en el portal | componentes/01 §8, componentes/04 §8 | [`03`](03_identidad_sesiones_y_portal.md) §6 |
| Vigencias por perfil | componentes/02 §4 | [`03`](03_identidad_sesiones_y_portal.md) §5 |
| Producto del broker; entrega ordenada; retención en el broker | D-08 §4/§6 | [`04`](04_mensajeria_y_eventos.md) §2, §3, §7 |
| Reconciliación tras fallo del intermediario | E-04 §2 | [`04`](04_mensajeria_y_eventos.md) §6 |
| Confirmación de los comandos northbound (aplicado vs verificado) | D-08 §6 | [`01`](01_controlador_y_api_northbound.md) §4.4 |
| Consolidación Monitor/Detección en el prototipo | D-04 §7 | [`06`](06_deteccion_y_mitigacion.md) §2 |
| Persistencia (I6) | C-02 §4, D-07 §4 | [`05`](05_persistencia_auditoria_y_tiempo.md) §2 |
| Retención, integridad y recuperación de registros | E-04 §3, componentes/03 §8, A-02 §4 | [`05`](05_persistencia_auditoria_y_tiempo.md) §4 |
| Fuente de tiempo común (NTP) | E-05 §3 | [`05`](05_persistencia_auditoria_y_tiempo.md) §5 |
| Visualización | B-03 D-08/D-13 | [`05`](05_persistencia_auditoria_y_tiempo.md) §6 |
| Algoritmo de detección; umbrales estáticos o dinámicos | B-03 D-03/D-04 | [`06`](06_deteccion_y_mitigacion.md) §3 |
| Frecuencia de I8 | D-07 §4 | [`06`](06_deteccion_y_mitigacion.md) §2 |
| Precedencia P9/P12 | D-03 §7 | [`06`](06_deteccion_y_mitigacion.md) §6 |
| Presupuesto de latencia | B-03 §6 (D-10) | [`06`](06_deteccion_y_mitigacion.md) §7 |
| IDS, IPS o ambos; inteligencia de amenazas | R5.2, R5.6, E-05 §3 | [`07`](07_perimetro_r5.md) §2, §4 |
| Virtualización o simulación | B-03 D-06/D-11, C-04 §6 | [`08`](08_entorno_del_prototipo.md) §1 |

## 4. Deuda cuantitativa: qué mide el prototipo

Los pendientes que [`E-02`](../E-Validacion_del_HLD/02_requisitos_a_componentes.md) §5 registró no se cierran con documentos sino con mediciones; esta fase deja cada uno con su experimento:

| Pendiente | Experimento | Se reporta como cierre de |
|---|---|---|
| Valores de R4.3/R4.4 (indicadores y umbrales) | Escenarios R4 + días de fondo → calibración de α, k, pisos ([`06`](06_deteccion_y_mitigacion.md) §8) | R4.3, R4.4 |
| R4.10 (tiempos e impacto) | Cronometría por escenario | R4.10, RNF-04 |
| RNF-03 (sobrecarga) | Barrido de frecuencias de sondeo + carga del espejo | RNF-03 |
| RNF-11/12 (reproducibilidad y verificabilidad) | Repetición de escenarios con parámetros registrados ([`08`](08_entorno_del_prototipo.md) §4) | RNF-11, RNF-12 |
| Capacidad y escala (R1.10, RA-08) | Llenado de tablas + carga creciente sobre los ocho switches | RA-08, R1.10 |
| Tiempos de recuperación (RA-07) | Corte de enlace y caída de switch con caminos alternativos; caída del controlador; drill de restauración; reconciliación | RA-07 |

## 5. Fronteras: qué queda para las fases siguientes

- **Fase G (LLD):** esquemas de datos definitivos, estructura interna de cada servicio, contratos de eventos al detalle de campo, configuración del pipeline del switch.
- **Fase H (despliegue):** escrita — la topología física quedó fijada en ocho switches dual-homed ([`H-01`](../H-Despliegue/01_infraestructura_fisica.md) §3); lo que queda como análisis de referencia: clúster del controlador y multi-controlador en operación, feeds externos de inteligencia, cifrado en reposo y política de respaldo de un despliegue real, canal in-band.
- **Prototipo (medición):** todo lo de §4 — la fase F decidió el mecanismo y el experimento; el número final es un resultado, no un supuesto.

--------------------------------------------------------------------

# Método y mapa del LLD

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** G — Diseño de bajo nivel (LLD)
**Estado:** Borrador formal para revisión

---

La Fase D fijó **qué componentes existen y qué contrato los une**; la Fase F eligió **con qué tecnología se materializan**; esta fase escribe **cómo queda cada artefacto**: esquemas de datos definitivos, contratos de eventos al detalle de campo, estructura interna de cada servicio y configuración del pipeline del switch — exactamente lo que [`F-09`](../F-Decisiones_tecnologicas/09_sintesis_y_trazabilidad.md) §5 dejó para esta fase. Nada de lo escrito aquí cambia un contrato de D ni una decisión de F: los implementa.

## 1. La regla de lectura: de lo general a lo particular

Cada documento de esta fase respeta la misma estructura: abre con **el concepto general** —la familia de artefactos, su papel en el sistema, la jerarquía que lo ordena— y recién después baja al **detalle particular** —el endpoint, el campo, el valor—. El detalle no sustituye al concepto: lo aterriza. Primero la sesión como forma del SSO del operador; después, que la sesión es una cookie opaca ligada al dispositivo.

| Documento | Lo general | Lo particular |
|---|---|---|
| [`01`](01_apis.md) | La API como frontera síncrona del sistema: dos familias, I2 e I7 | Endpoints y esquemas JSON campo a campo |
| [`02`](02_eventos.md) | El bus como frontera asíncrona: el evento informa, el comando ejecuta | Catálogo de eventos al detalle de campo, enrutamiento y colas |
| [`03`](03_datos.md) | Un repositorio por servicio; tres clases de dato; correlación por identificadores | Esquema de cada base, tabla a tabla |
| [`04`](04_interfaces.md) | I1–I8 como los contratos entre componentes | La forma operativa de las interfaces que no son HTTP |
| [`05`](05_configuraciones.md) | Configuración como estado declarado y versionado; dos clases | Parámetro por parámetro, producto por producto |
| [`06`](06_reglas.md) | La jerarquía de prioridades como jerarquía de autoridad | El pipeline del switch, entrada a entrada |
| [`07`](07_detalles_de_implementacion.md) | Cada servicio: una responsabilidad, un ciclo de vida, una estructura en capas | Módulos y pseudocódigo de los bucles críticos |

## 2. Invariantes de esta fase

- **Los contratos de D** ([`07_interfaces_principales.md`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/07_interfaces_principales.md) y [`08_comunicacion.md`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/08_comunicacion.md)): separación síncrono/asíncrono, frontera de secretos, catálogo de eventos, reglas de confianza.
- **Las decisiones de F** ([`00`](../F-Decisiones_tecnologicas/00_metodo_de_decision.md)): productos, mecanismos y valores iniciales. El LLD detalla; si un detalle obligara a contradecir una decisión, se reabre la decisión en F — no se ajusta en silencio aquí.
- **La frontera de P12:** los valores numéricos de esta fase son iniciales y configurables; los definitivos los produce la medición del prototipo.

## 3. Qué cierra esta fase

| Cuestión abierta | Origen | Cierre |
|---|---|---|
| Esquemas de datos definitivos | F-09 §5 | [`03`](03_datos.md) |
| Contratos de eventos al detalle de campo | F-09 §5, D-08 §3 | [`02`](02_eventos.md) |
| Estructura interna de cada servicio | F-09 §5 | [`07`](07_detalles_de_implementacion.md) |
| Configuración del pipeline del switch | F-09 §5 | [`06`](06_reglas.md) |
| Métrica del costo por enlace | [`flows/05`](../../../flows/05_enrutamiento.md) §8 | [`06`](06_reglas.md) §4 |
| Prioridad concreta de las reglas de camino | [`flows/05`](../../../flows/05_enrutamiento.md) §8 | [`06`](06_reglas.md) §3 |
| Vía que declara el inventario de servicios | [`flows/05`](../../../flows/05_enrutamiento.md) §8 | [`01`](01_apis.md) §4 |
| Número de tablas del pipeline (plana o multi-tabla) | [`flows/01`](../../../flows/01_primitivas_openflow.md) (cuestiones abiertas) | [`06`](06_reglas.md) §2 |

## 4. Fronteras de esta fase

- **Fase H (despliegue):** qué máquinas, qué red y en qué orden — el LLD define qué corre **dentro** de cada máquina; H define las máquinas y cómo se unen ([`H-00`](../H-Despliegue/00_metodo_y_mapa.md)).
- **Prototipo (medición):** los valores finales cuantitativos (umbrales, tiempos, capacidades) salen de las mediciones ya comprometidas en [`F-09`](../F-Decisiones_tecnologicas/09_sintesis_y_trazabilidad.md) §4; este LLD es su punto de partida.

# APIs

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** G — Diseño de bajo nivel (LLD)
**Estado:** Borrador formal para revisión

---

La **API es la frontera síncrona del sistema**: todo lo que se pide con respuesta inmediata viaja por una API, nunca por el bus ([`D-08`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/08_comunicacion.md) §2). El sistema tiene **dos familias** de API, por su naturaleza:

- **I2 — la API del plano de control.** Órdenes de política al controlador y consultas de topología y estado. La hablan los servicios (Políticas, IAM, Monitor, Incidentes), no las personas.
- **I7 — las API de administración.** Cada servicio expone sus consultas y órdenes administrativas; la Consola es su cliente y **la sesión del operador es el SSO** ([`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §4).

Y una tercera superficie, **I3**: los formularios del portal — la única API que hablan las poblaciones.

**Principios comunes a las tres.** HTTPS sobre la red de gestión (out-of-band), JSON UTF-8, autenticación y autorización validadas **del lado del servidor, siempre** (nunca se confía en el cliente), operaciones idempotentes, errores estructurados y versionado `/v1` en la ruta.

## 2. I2 — órdenes al controlador

Un solo recurso de órdenes y una confirmación en dos niveles ([`F-01`](../F-Decisiones_tecnologicas/01_controlador_y_api_northbound.md) §4.4). Las cuatro órdenes fijadas en F —`APLICAR_PERFIL`, `APLICAR_MITIGACION`, `RETIRAR`, `CONSULTAR`— se materializan así: las tres primeras por `POST /api/v1/ordenes`; `CONSULTAR` se realiza como la familia `GET` de la tabla siguiente (estado de órdenes, asociaciones, reglas, topología, contadores, servicios). Autenticación: clave de servicio por cliente sobre TLS.

| Recurso | Uso |
|---|---|
| `POST /api/v1/ordenes` | Ejecutar una orden (`APLICAR_PERFIL`, `APLICAR_MITIGACION`, `RETIRAR`) |
| `GET /api/v1/ordenes?cookie=…` | Estado de una orden anterior (idempotencia y reconciliación) |
| `GET /api/v1/asociaciones?ip=…` | Asociación vigente MAC ↔ switch:puerto ↔ IP (ligadura de sesión) |
| `GET /api/v1/reglas?cookie=…&switch=…` | Reglas instaladas (reconciliación de incidentes) |
| `GET /api/v1/topologia` · `GET /api/v1/contadores` | Grafo de la red; contadores por puerto y flujo (I8) |
| `POST /api/v1/servicios` · `GET /api/v1/servicios` | Inventario de servicios (anclajes del grafo, §4) |

**Estructura común de la orden** (todas las órdenes la respetan):

```json
POST /api/v1/ordenes            (HTTPS, red de gestión)
{
  "orden": "APLICAR_PERFIL",
  "dispositivo": { "mac": "52:54:00:01:01", "switch": "SA1", "puerto": "p3" },
  "vigencia":    { "idle_timeout_s": 1800, "hard_timeout_s": 43200 },
  "contexto":    { "cookie": "SES-000123", "solicitante": "iam",
                   "motivo": "login-academico" }
}
→ 201  { "estado": "APLICADA", "reglas": ["…"], "confirmada_en": "…" }
```

| Campo | Tipo | Regla |
|---|---|---|
| `orden` | string | Una de las cuatro; las demás claves dependen de ella |
| `dispositivo` | objeto | `mac`, `switch`, `puerto` — la ubicación aprendida del dispositivo |
| `vigencia` | objeto | `idle_timeout_s` y `hard_timeout_s`: **el mismo valor que la sesión** ([`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §5) |
| `contexto.cookie` | string | Clave de idempotencia: reaplicar la misma cookie produce las mismas reglas, sin duplicados |
| `contexto.solicitante` | string | Identidad del servicio que ordena — se registra y se audita |

**`APLICAR_PERFIL`** — instala las reglas de un perfil (sesión o elevación). Además de la anterior: `perfil` (`ACADEMICO`, `OPERADOR`, elevación). El controlador traduce el perfil a sus reglas de alcance ([`06`](06_reglas.md) §3); el solicitante **no** dicta prioridades ni matches: expresa el qué, no el cómo (I2, [`D-07`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/07_interfaces_principales.md)).

**`APLICAR_MITIGACION`** — instala la respuesta de la escalera:

```json
{
  "orden": "APLICAR_MITIGACION",
  "accion": "RATE_LIMIT",
  "objetivo": { "tipo": "servicio", "ip": "10.2.0.10" },
  "origenes": [ { "mac": "52:54:00:03:02", "switch": "SA1", "puerto": "p9" } ],
  "parametros": { "tasa_pps": 1000, "ttl_s": 300 },
  "contexto": { "cookie": "INC-0042", "incidente": "INC-0042",
                "solicitante": "policy-engine", "motivo": "flood",
                "aprobacion": null }
}
→ 201  { "estado": "APLICADA", "verificacion": "PENDIENTE" }
```

| Campo | Tipo | Regla |
|---|---|---|
| `accion` | string | `RATE_LIMIT`, `BLOCK_SOURCE`, `ISOLATE_DEVICE`, `QUARANTINE` |
| `objetivo` / `origenes` | objetos | Dónde y contra quién; `ISOLATE_DEVICE` y `QUARANTINE` apuntan al dispositivo, `BLOCK_SOURCE` al origen |
| `parametros` | objeto | `tasa_pps` (solo `RATE_LIMIT`) y `ttl_s` — toda mitigación expira sola (P10) |
| `contexto.aprobacion` | string o null | Obligatorio para `QUARANTINE`: el identificador de la aprobación humana (D-03 §5). El Policy Engine no emite cuarentena sin él; el controlador la rechaza si falta |

La respuesta `APLICADA` es la **confirmación de aplicación** (OpenFlow barrier). La **verificación** (`verificacion: "PENDIENTE"`) la cierra el Monitor por contadores y llega por el bus como `MitigationVerified` ([`02`](02_eventos.md) §3) — nunca por esta API.

**`RETIRAR`** — `{ "orden": "RETIRAR", "contexto": { "cookie": "SES-000123" } }` → `200 { "estado": "RETIRADA" }`. El retiro es **por cookie, siempre**: nunca se toca una regla ajena (P10, [`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §3).

**Errores** (comunes a las tres órdenes): `400` esquema inválido · `401` sin clave válida · `403` orden fuera de la competencia del solicitante · `404` dispositivo o cookie desconocidos · `409` orden duplicada con cookie distinta · `503` controlador no disponible — el solicitante **reintenta la misma orden** (idempotencia por cookie) hasta confirmación.

## 3. I7 — API de administración por servicio

Cada servicio expone sus propios recursos; la Consola los agrega. La sesión llega como cookie (navegador) o como **token derivado de vida corta** (herramientas) — ambas con la misma vigencia y ligadura ([`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §4). El servicio valida sesión **y** rol en cada petición; la interfaz no concede nada.

| Servicio | Recursos principales | Rol mínimo |
|---|---|---|
| IAM | `GET /sesiones/{id}` · `DELETE /sesiones/{id}` (logout administrativo) · `POST /dispositivos/{mac}/reaprovisionar-totp` | TI |
| Registro | `GET/POST /dispositivos` · `GET /dispositivos/{mac}/historial` | TI / Admin |
| Incidentes | `GET /incidentes` · `GET /incidentes/{id}` · `POST /incidentes/{id}/aprobar` (cuarentena) · `POST /incidentes/{id}/cerrar` | Admin / SA |
| Políticas | `GET/PUT /perfiles` · `GET/PUT /umbrales` · `GET /elevaciones` | TI / Admin |
| Auditoría | `GET /eventos?desde=…&actor=…` (solo lectura) | Auditor |
| Monitor | `GET /metricas` · `GET /lineas-base` (solo lectura) | Admin / SA |

**Convenciones.** Respuesta `{ "datos": …, "error": { "codigo": "SESION_EXPIRADA", "mensaje": "…" } }`; paginación por cursor (`?cursor=…&limite=100`); `401` sin sesión, `403` con sesión sin rol. El `PUT` de umbrales y perfiles escribe en `bd_politicas` y publica el cambio en auditoría — los valores son configurables por diseño (P12), y **quién** los cambió queda registrado.

## 4. El inventario de servicios (cierre de flows/05 §8)

El grafo de la red no ve extremos: LLDP conecta switches, no servicios. Los servicios son infraestructura **declarada** ([`flows/05`](../../../flows/05_enrutamiento.md) §4). La vía que la declara, fijada aquí: **I2, con privilegio administrativo**.

```json
POST /api/v1/servicios
{
  "nombre": "bd-academica", "clase": "critico",
  "ip": "10.2.0.12", "switch": "SA2", "puerto": "p4",
  "declarado_por": "ti-operaciones"
}
```

El controlador ancla cada servicio al grafo y calcula sus caminos; un cambio de anclaje rehace el cálculo igual que un cambio de topología. La administración de la red es la única que declara servicios — ningún servicio se autodeclara.

## 5. I3 — los formularios del portal

La única API que hablan las poblaciones. Un solo servicio, tres pasos:

| Recurso | Qué ocurre |
|---|---|
| `GET /login` | Selector explícito de población: «Comunidad universitaria» / «Personal de operación» ([`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §6) |
| `POST /login` | Credenciales (+ TOTP si operación). El IAM verifica por la ruta elegida; la sesión resultante la decide el Policy Engine — el portal no conecta nada por sí mismo (I3, [`D-07`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/07_interfaces_principales.md)) |
| `POST /logout` | Retiro por cookie y `SessionClosed` inmediatos, sin esperar relojes |
| `GET/POST /elevacion` | Solicitud de elevación del académico → `ElevationRequested` al bus |

El selector no concede nada: solo elige la ruta de verificación. Un intento con credenciales en la ruta equivocada falla y se audita.

## 6. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Orden de perfil completa (I2 → reglas → `APLICADA`) | Latencia orden → confirmación; idempotencia por cookie | RT-04, RNF-04 |
| Rechazo de orden inválida (cuarentena sin aprobación, cookie ajena) | `403`/`400` y registro en auditoría | D-03 §5, P10 |
| Consulta de asociación durante el login | Ligadura de sesión con la ubicación aprendida | RNF-01 |
| Declaración de un servicio en el inventario | El grafo lo ancla y recalcula caminos | flows/05 §4 |
| Petición I7 con sesión vencida y con rol insuficiente | `401` y `403`; la interfaz no concede | R1.8, I7 |

# Eventos

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** G — Diseño de bajo nivel (LLD)
**Estado:** Borrador formal para revisión

---

El **bus es la frontera asíncrona del sistema**: por él viaja todo lo que no espera respuesta ([`D-08`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/08_comunicacion.md) §2). Su regla de fondo es la que fijó D: **el evento informa; el comando ejecuta** — las decisiones que deben aplicarse con confirmación (`MitigationRequired`, `ElevationGranted`, `ElevationExpired`) viajan como comandos por I2 y publican su eco por el bus para que la Auditoría y la Consola los vean. Los eventos cumplen **tres propósitos**: describir estado (sesiones, dispositivos), propagar detección (anomalías, verificaciones) y registrar decisión (incidentes, elevaciones). Las garantías de entrega son las de [`F-04`](../F-Decisiones_tecnologicas/04_mensajeria_y_eventos.md): al menos una vez, idempotencia, orden por incidente.

## 2. La envoltura común

Todo evento viaja con la misma envoltura; el contenido va en `payload`:

```json
{
  "evento_id": "018f2a...",            // UUIDv7: único, clave de idempotencia
  "tipo": "AnomalyDetected",           // nombre del catálogo (D-08 §3)
  "emisor": "deteccion",               // servicio que publica
  "timestamp": "2026-10-05T14:03:22Z", // UTC, reloj común (chrony)
  "secuencia": 7,                      // monótona por incidente; ausente fuera de incidentes
  "correlacion": {                     // claves de correlación entre servicios
    "incidente": "INC-0042",           //   cuando aplica
    "sesion": "SES-000123",            //   cuando aplica
    "dispositivo": "52:54:00:01:01"
  },
  "payload": { … }                     // específico del tipo, §3
}
```

- `evento_id` es lo que hace **idempotente** al consumidor: cada uno registra los ids ya procesados y descarta duplicados ([`F-04`](../F-Decisiones_tecnologicas/04_mensajeria_y_eventos.md) §4).
- `secuencia` es lo que hace **ordenable** al incidente: el consumidor acepta `secuencia == esperada + 1`; un salto se declara como hueco en auditoría, nunca se procesa fuera de sitio (D-08 §4).
- `correlacion` es lo que une los registros entre servicios sin cruzar bases ([`03`](03_datos.md) §1).

## 3. El catálogo, campo a campo

El catálogo es el contrato entre servicios (D-08 §3, P13). Aquí queda su forma definitiva:

| Tipo | Payload (campos) | Productor → consumidores |
|---|---|---|
| `DeviceConnected` | `mac`, `ip`, `switch`, `puerto`, `timestamp` | Controlador → Registro, Monitor, Auditoría |
| `MAC_Moved` | `mac`, `ubicacion_anterior` {switch,puerto}, `ubicacion_nueva` {switch,puerto} | Monitor → Incidentes, Políticas, Auditoría **y IAM** (invalida la sesión ligada, [`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §4) |
| `AnomalyDetected` | `tipo` (clase de ataque), `objetivo` {ip,servicio}, `origenes` [{mac,switch,puerto}], `tasas` {pps,bps}, `linea_base` {media,sigma}, `desviacion`, `severidad_propuesta` | Detección → Incidentes, Consola, Auditoría |
| `IncidentOpened` | `incidente`, `tipo`, `objetivo`, `severidad`, `abierto_en` | Incidentes → Políticas, Consola, Auditoría |
| `MitigationRequired` | `incidente`, `accion`, `objetivo`, `origenes`, `parametros`, `ttl` | Políticas → **comando I2**; eco al bus: Auditoría, Consola |
| `MitigationApplied` | `incidente`, `reglas` [ids], `switches`, `aplicada_en` | Controlador → Monitor (verifica), Incidentes, Auditoría |
| `MitigationVerified` | `incidente`, `tasas_antes`, `tasas_despues`, `cumple_objetivo` | Monitor → Incidentes, Políticas, Auditoría |
| `MitigationExpired` | `incidente`, `regla`, `motivo` (timeout o retirada) | Monitor / Controlador → Incidentes, Políticas, Auditoría |
| `ElevationRequested` | `solicitante`, `perfil_pedido`, `alcance`, `duracion` | IAM → Políticas, Consola, Auditoría |
| `ElevationGranted` / `ElevationExpired` | `solicitante`, `perfil`, `ttl` / `motivo` | Políticas → **comando I2**; eco al bus: Auditoría, Consola |
| `SessionOpened` / `SessionClosed` | `identidad`, `perfil_o_rol`, `dispositivo`, `timestamp` / `motivo` | IAM → Políticas, Auditoría |
| `DeviceRegistered` / `DeviceRevoked` | `mac`, `titular`, `rol`, `responsable`, `vigencia` | Registro → Auditoría, Consola |
| `MetricSample` | `destino`, `ventana`, `pps`, `bps`, `flujos_nuevos`, `fuentes_distintas` | Monitor → **Detección** (la materia prima, [`F-06`](../F-Decisiones_tecnologicas/06_deteccion_y_mitigacion.md) §2) |

`MetricSample` es la única adición de esta fase al catálogo de D: las métricas del Monitor hacia la Detección viajan por el bus por contrato (D-04, F-06 §2), y necesitan su tipo propio. No es un evento de auditoría: es observación en bruto, de alto volumen, consumida por un solo servicio.

**Qué no viaja nunca por el bus:** comandos (I2), preguntas (I7) y **credenciales** — ni en payload ni en correlación. Un evento puede referirse a una sesión por su identificador, jamás por su secreto.

## 4. Enrutamiento y colas

Exchange `plataforma` (topic, durable). Clave de enrutamiento: `evento.<Tipo>`. Cada servicio consumidor tiene **su propia cola durable** con sus enlaces ([`F-04`](../F-Decisiones_tecnologicas/04_mensajeria_y_eventos.md) §3):

| Cola | Enlaces (`evento.*`) | Consumidor |
|---|---|---|
| `auditoria` | `#` (todo el catálogo) | Auditoría |
| `monitor` | `DeviceConnected`, `MitigationApplied` | Monitor |
| `deteccion` | `MetricSample` | Detección |
| `incidentes` | `AnomalyDetected`, `MitigationVerified`, `MitigationExpired`, `MAC_Moved` | Incidentes |
| `politicas` | `IncidentOpened`, `MitigationVerified`, `MitigationExpired`, `ElevationRequested`, `MAC_Moved` | Políticas |
| `iam` | `MAC_Moved` | IAM |
| `registro` | `DeviceConnected` | Registro |
| `consola` | `AnomalyDetected`, `IncidentOpened`, `DeviceRegistered`, `DeviceRevoked` | Consola (alertas en vivo) |

**Cola por incidente** (`inc.INC-0042`): el ciclo completo del incidente —`IncidentOpened`, `MitigationRequired`, `MitigationApplied`, `MitigationVerified`, `MitigationExpired` y sus elevaciones asociadas— se publica **además** en su cola propia, declarada al abrir el incidente y auto-borrada al cerrarlo (TTL de respaldo 24 h). Es el mecanismo de entrega ordenada: orden FIFO de una sola cola, sin reordenamiento en el consumidor (D-08 §4). El Incident Manager consume de ella el ciclo completo; los demás servicios consumen de sus colas por servicio.

## 5. Parámetros de entrega y recuperación

| Parámetro | Valor inicial | Papel |
|---|---|---|
| Confirmación de publicación | Activada (`publisher confirms`) | El publicador sabe que el broker recibió (F-04 §4) |
| Buffer local del publicador | Acotado (10 000 mensajes), retroceso progresivo hasta 60 s | El broker caído no detiene al publicador; el desborde se registra como **hueco declarado** en auditoría — jamás se oculta (P11) |
| Ack de consumo | Manual, tras procesar | Un mensaje solo se descarta cuando se procesó |
| Reintentos | 5, con retroceso 1 s → 60 s | Tras agotarse: a la DLQ |
| DLQ | Una por cola (`dlq.<cola>`), sin consumidor automático | Lo no procesado queda visible; su llegada a DLQ se registra en auditoría |
| Ventana de duplicados | 7 días de `evento_id` procesados por consumidor | Idempotencia |
| Buffer de reorden | 100 mensajes por incidente | Hueco detectado: se espera el faltante; si no llega en 10 s, hueco declarado y se continúa |

## 6. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Consumidor detenido durante un ciclo de incidente; levantarlo | Cero eventos perdidos; orden restaurado por `secuencia` | I5, D-08 §4 |
| Reenvío con duplicados deliberados | Idempotencia por `evento_id`: sin efectos dobles | D-08 §4 |
| Broker detenido durante una ráfaga | Buffer local absorbe; reconexión; huecos declarados si los hubo | P13, E-04 |
| Mensaje que agota reintentos | Queda en DLQ y en auditoría | P11 |
| `MAC_Moved` con sesión viva | El IAM invalida la sesión; `SessionClosed` auditado | RNF-01, R3.3 |
| Validación de esquema | Todo evento emitido valida contra el catálogo de §3 | RNF-12 |

# Datos

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** G — Diseño de bajo nivel (LLD)
**Estado:** Borrador formal para revisión

---

La **persistencia es la memoria de cada servicio, y de nadie más** (I6, [`D-04`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/04_descomposición_arquitectonica.md) §3): un repositorio por servicio, sin accesos cruzados. Los datos del sistema son de **tres clases**, y la clasificación manda sobre todo lo demás:

- **Estado operativo** — lo que describe la realidad del sistema ahora (sesiones, líneas base, mitigaciones vigentes). Se **reconcilia contra el plano de datos** cuando hay duda ([`F-04`](../F-Decisiones_tecnologicas/04_mensajeria_y_eventos.md) §6: el plano de datos es la verdad).
- **Registros de negocio** — lo que las personas y los procesos declaran (dispositivos, políticas, umbrales). Viven hasta que una autoridad los cambia.
- **Auditoría** — lo que prueba quién hizo qué y cuándo. Inmutable y con retención propia ([`F-05`](../F-Decisiones_tecnologicas/05_persistencia_auditoria_y_tiempo.md)).

**La correlación viaja en los eventos, no en las consultas.** Ningún servicio lee la base de otro (D-04). Un incidente y la sesión que lo provocó se relacionan por los identificadores que el evento lleva en su envoltura ([`02`](02_eventos.md) §2: `correlacion`), y cada base guarda su copia del identificador ajeno. Un `JOIN` entre bases no existe: es una decisión de arquitectura, no una limitación del motor.

## 2. El diccionario de entidades

| Entidad | Identificador | Qué es | Vive en |
|---|---|---|---|
| Dispositivo | `mac` | Equipo conocido del campus, con su historial | `bd_registro` |
| Identidad | `usuario` | Persona de la comunidad (IdP) o del reino operadores | IdP / `bd_iam` |
| Sesión | `SES-xxxxxx` | El SSO: identidad + rol + dispositivo ligado + vigencias | `bd_iam` |
| Perfil | `perfil` | ACADÉMICO, operador, elevación: alcance y vigencias | `bd_politicas` |
| Incidente | `INC-xxxx` | La detección y su ciclo de vida completo | `bd_incidentes` |
| Mitigación | (parte del incidente) | La respuesta instalada, de aplicada a expirada | `bd_incidentes` |
| Elevación | `ELE-xxxxxx` | Privilegio temporal, con alcance y tope | `bd_politicas` |
| Línea base | `destino` protegido | La EWMA que el Monitor mantiene por destino | `bd_monitor` |

## 3. Esquemas por servicio

PostgreSQL, **una base por servicio** con su usuario propio y sin permisos cruzados ([`F-05`](../F-Decisiones_tecnologicas/05_persistencia_auditoria_y_tiempo.md) §2). Notación: PK clave primaria, FK clave foránea local (nunca entre bases).

### `bd_registro` — catálogo de dispositivos privilegiados

| Tabla | Columnas principales |
|---|---|
| `dispositivos` | `mac` PK · `tipo` · `titular` · `rol` · `estado` (activo/revocado) · `vigencia_hasta` · `responsable` · `creado_en` |
| `historial_dispositivo` | `id` PK · `mac` FK · `evento` (alta, revocación, movimiento, incidente asociado) · `detalle` · `ts` |

El historial es la fuente del «historial de dispositivo» que la investigación de un `MAC_Moved` consulta ([`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §4). Solo dispositivos privilegiados se registran (los académicos no viven en ningún catálogo, [`C-04`](../C-Contexto/04_alcance_de_la_infraestructura.md) §3).

### `bd_iam` — identidades privilegiadas y sesiones

| Tabla | Columnas principales |
|---|---|
| `operadores` | `usuario` PK · `hash_bcrypt` · `totp_secreto` (cifrado) · `rol` (TI/Admin/SA) · `estado` · `creado_en` |
| `provision_totp` | `usuario` FK · `emitido_en` · `verificado_en` — el alta no se habilita hasta verificar el código ([`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §3) |
| `sesiones` | `sesion_id` PK · `usuario` · `rol` · `mac` · `switch_puerto` · `ip` · `idle_timeout_s` · `hard_timeout_s` · `creada_en` · `ultima_actividad` · `estado` (activa/cerrada/invalidada) · `motivo_cierre` |
| `tokens_derivados` | `token_hash` PK · `sesion_id` FK · `expira_en` — el token corto para herramientas, la misma sesión |

La ligadura de la sesión (MAC, switch:puerto, IP) es la que la petición valida en cada uso y la que `MAC_Moved` invalida. Las credenciales de la comunidad **no** viven aquí: viven en el IdP ([`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §2).

### `bd_incidentes` — ciclo de vida y mitigaciones

| Tabla | Columnas principales |
|---|---|
| `incidentes` | `inc_id` PK · `tipo` · `objetivo` · `severidad` · `estado` (abierto → en_mitigacion → mitigado → escalado → cerrado) · `abierto_en` · `cerrado_en` · `ultima_secuencia` |
| `eventos_incidente` | `inc_id` FK · `secuencia` · `evento_id` · `payload_json` · `procesado_en` — la cola del incidente, persistida |
| `mitigaciones` | `inc_id` FK · `accion` · `alcance` · `tasa_pps` · `ttl_s` · `cookie` · `estado` (aplicada/verificada/expirada) · `aplicada_en` · `verificada_en` · `expirada_en` · `aprobacion` (si cuarentena) |

`eventos_incidente` es el registro local de la cola `inc.<id>`: el Incident Manager persiste cada evento con su secuencia antes de procesarlo — un reinicio retoma exactamente donde quedó (idempotencia durable, [`F-04`](../F-Decisiones_tecnologicas/04_mensajeria_y_eventos.md) §4).

### `bd_politicas` — perfiles, umbrales y elevaciones

| Tabla | Columnas principales |
|---|---|
| `perfiles` | `perfil` PK · `idle_timeout_s` · `hard_timeout_s` · `alcance` — los valores iniciales de [`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §5 |
| `umbrales` | `destino` PK · `alfa` · `k_in` · `k_out` · `piso_pps` · `piso_bps` · `n_ventanas` — la parametrización de [`F-06`](../F-Decisiones_tecnologicas/06_deteccion_y_mitigacion.md) §3 |
| `escalera` | `accion` PK · `automatica` (bool) · `condicion` · `ttl_por_defecto` — la tabla de automatización de F-06 §5 |
| `elevaciones` | `elev_id` PK · `solicitante` · `perfil` · `alcance` · `ttl_s` · `estado` · `otorgante` · `ts` |

Todo cambio en estas tablas es una orden administrativa (I7) y queda en auditoría con su autor: los umbrales son configurables por diseño (P12), y **quién los movió** es parte del registro.

### `bd_monitor` — observación y línea base

| Tabla | Columnas principales |
|---|---|
| `contadores` | `ts` · `switch` · `puerto_o_flujo` · `pps` · `bps` — crudo del sondeo I8 · **retención: 24 h crudo, 7 días agregado** |
| `lineas_base` | `destino` PK · `media` · `varianza` · `ultima_ventana` — la EWMA por destino protegido |
| `features` | `ventana` · `destino` · `fuentes_distintas` · `flujos_nuevos` · `destinos_distintos_por_origen` — la materia prima de la clasificación |

El Monitor es el único que escribe aquí; la Detección recibe los features por el bus (`MetricSample`) y no toca esta base. Grafana lee esta base (y `bd_auditoria`) en **solo lectura** ([`F-05`](../F-Decisiones_tecnologicas/05_persistencia_auditoria_y_tiempo.md) §6).

### `bd_auditoria` — quién, qué, cuándo y por qué

| Tabla | Columnas principales |
|---|---|
| `eventos_auditoria` | `id` PK · `ts` (UTC) · `actor` · `accion` · `objetivo` · `detalle` · `evento_id` (correlación) · `hash_previo` — **retención: 90 días** |
| `exports` | `archivo` · `rango_ts` · `hash_final` · `exportado_por` — el registro de cada export JSONL |

La auditoría llega **por el bus** (la cola `auditoria` consume todo el catálogo) y por registros directos de los servicios para sus actos administrativos (I7). El export de retención larga es **JSONL append-only con cadena de hash**: cada línea lleva el `sha256(línea ‖ hash_anterior)`; el hash final se copia en `exports` y en la primera línea del archivo siguiente. La manipulación no se impide — no puede pasar inadvertida (P11, [`F-05`](../F-Decisiones_tecnologicas/05_persistencia_auditoria_y_tiempo.md) §4).

## 4. El plano de datos manda

Ninguna de estas bases es la verdad del plano de datos: lo son los switches ([`F-04`](../F-Decisiones_tecnologicas/04_mensajeria_y_eventos.md) §6). Tras cualquier caída, los registros se **reconcilian contra I2** —las reglas vivas por cookie— y el estado que no corresponda a una regla viva se cierra (una mitigación sin regla no puede quedar activa). Esta regla vale para todas las tablas de estado operativo de §3.

## 5. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Aislamiento entre bases: intento de acceso cruzado | Rechazo por permisos | I6, D-04 |
| Ciclo de incidente completo persistido | `incidentes` + `eventos_incidente` + `mitigaciones` coherentes al reiniciar el servicio | D-08 §4 |
| Drill de reconciliación (caída + expiración durante la caída) | Al volver, la mitigación expirada se cierra contra I2 | E-04, P10 |
| Verificador de cadena de hash sobre un export | Toda línea valida; una línea alterada rompe la cadena | P11 |
| Retención: borrado automático de `contadores` crudos | 24 h / 7 días según política | F-05 |
| Consulta de auditoría por rol | Solo el Auditor lee; el resto `403` | RT-07 |

# Interfaces

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** G — Diseño de bajo nivel (LLD)
**Estado:** Borrador formal para revisión

---

Las **interfaces son los contratos entre componentes** ([`D-07`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/07_interfaces_principales.md)): I1 a I8 definen qué fluye entre qué partes. Las que hablan HTTP quedaron en [`01`](01_apis.md) (I2, I3, I7), el bus en [`02`](02_eventos.md) (I5) y la persistencia en [`03`](03_datos.md) (I6). Este documento detalla **la forma operativa de las restantes** —las que hablan protocolos de infraestructura—: el southbound (I1), la identidad institucional (I4), la observación (I8), y los dos canales auxiliares del perímetro y del tiempo que el sistema necesita para operar.

## 2. I1 — Southbound: el canal de control

**Lo general:** el controlador habla con los switches por OpenFlow 1.3 sobre TCP 6653, fuera de banda (RP-02). Es un canal de **comandos con confirmación y eventos asíncronos**: el controlador ordena, el switch confirma y reporta (D-07 I1).

**La forma operativa:**

| Aspecto | Valor inicial |
|---|---|
| Transporte | TCP 6653, por las interfaces de gestión (`ma1`) de cada switch — nunca por el plano de datos |
| Autorización | El switch acepta control solo de los endpoints de controlador configurados (whitelist); una conexión desde otra interfaz se rechaza (verificación V6, [`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §4) |
| Latido | `ECHO` cada 5 s; sin respuesta en 3 latidos, el canal se declara caído |
| Confirmación de aplicación | `OFPT_BARRIER_REQUEST/REPLY` tras cada lote de instalación — es lo que sostiene el nivel `APLICADA` de I2 ([`01`](01_apis.md) §2) |
| Cookies | El controlador mantiene el **registro string ↔ 64 bits**: la cookie que los servicios nombran (`SES-…`, `INC-…`) se traduce al valor OpenFlow; el retiro por cookie usa la traducción inversa ([`06`](06_reglas.md) §3) |
| Multipart | `OFPMP_PORT_STATS`, `OFPMP_FLOW`, `OFPMP_METER_CONFIG`, `OFPMP_GROUP_DESC` — la única fuente de observación del plano de datos (P11) |
| Failover (clúster) | Cada switch lleva configurados los tres endpoints del clúster ONOS ([`F-01`](../F-Decisiones_tecnologicas/01_controlador_y_api_northbound.md) §6); en el prototipo uno solo está desplegado — el mecanismo se documenta, no se ejerce |

La negociación inicial (`HELLO`, `FEATURES_REPLY`) fija lo que el switch **declara** soportar; el controlador no puede ordenar más de lo declarado (P1, RP-11). Las verificaciones V1–V7 de [`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §4 son el acta de esa negociación contra el dispositivo real.

## 3. I4 — Identidad institucional: RADIUS y el directorio

**Lo general:** el IAM consume la identidad de la comunidad del IdP institucional; el prototipo **simula al IdP, no al protocolo** — FreeRADIUS con OpenLDAP detrás, lo mismo que una universidad real ejecuta ([`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §2).

**La forma operativa:**

| Aspecto | Valor inicial |
|---|---|
| Puertos | `1812/udp` (autenticación), `1813/udp` (accounting), en el segmento de gestión |
| Cliente RADIUS | Solo el IAM, con secreto compartido propio; otro origen se descarta |
| Autenticación | `Access-Request` (usuario, contraseña) → FreeRADIUS valida contra OpenLDAP → `Access-Accept/Reject` |
| Atributos | `Access-Accept` devuelve el perfil como atributo (`Class` o VSA del prototipo) — el IAM traduce identidad + atributos a la tupla del Policy Engine (D-07 I4) |
| Accounting | `Accounting-Request` `Start` · `Interim` cada 300 s · `Stop`, con `Acct-Session-Id = sesion_id` — el registro AAA que R1.9 exige y que correlaciona la auditoría |
| Directorio | Bind de servicio **de solo lectura**; árbol del prototipo (`ou=comunidad` con las cuentas de prueba); índice sobre `uid` |
| Timeouts | 3 s por intento, 2 reintentos, y el login falla — el IdP es síncrono, la persona espera (D-08 §2) |

Las credenciales de la comunidad nunca atraviesan la plataforma más allá de este intercambio: el IAM no las almacena (D-07 I4). El reino de operadores no usa esta interfaz: vive en el repositorio propio con TOTP ([`03`](03_datos.md) §3).

## 4. I8 — Observación: el sondeo de contadores

**Lo general:** el Monitor observa el plano de datos **solo a través del controlador** — nunca habla con los switches (P1, D-07 I8). Su producto es la materia prima de la Detección.

**La forma operativa:**

| Aspecto | Valor inicial |
|---|---|
| Camino | Monitor → I2 (`GET /api/v1/contadores`) → controlador → `MULTIPART` → switch |
| Conjunto caliente | Cada **5 s**: contadores de los destinos protegidos y de sus puertos de ingreso ([`F-06`](../F-Decisiones_tecnologicas/06_deteccion_y_mitigacion.md) §2) |
| Barrido completo | Cada **60 s**: inventario completo de flujos y puertos |
| Lote | Una consulta por switch, no una por flujo — la carga sobre el plano de control es la que RNF-03 mide |
| Tolerancia | Si el controlador no responde en 2 s, la ventana se registra como **hueco de observación** — la línea base no se inventa (P11) |
| Frecuencias | Configurables por parámetro (I7) — el barrido 5/30/60 s es el experimento de RNF-03 |

Un destino que despierta interés entra al conjunto caliente a partir del siguiente barrido completo.

## 5. Canales auxiliares: el espejo del perímetro y el tiempo

**El espejo** alimenta al sensor perimetral: un puerto del switch de borde replica el tráfico del segmento externo hacia la interfaz dedicada de la VM Suricata ([`F-07`](../F-Decisiones_tecnologicas/07_perimetro_r5.md) §3). El sensor está **fuera del camino de reenvío** (P8): recibe una copia, nunca interpone. Su NIC de espejo es de solo recepción — el sensor no emite por donde observa. La asignación física del puerto está en [`H-05`](../H-Despliegue/05_puertos.md).

**El tiempo** firma todo registro (RNF-09): un servidor chrony del prototipo es la fuente; todos los nodos son clientes; todo timestamp es UTC ([`F-05`](../F-Decisiones_tecnologicas/05_persistencia_auditoria_y_tiempo.md) §5). El tiempo **no** viaja por el plano de datos: la sincronización va por el segmento de gestión. Un servicio que no puede sincronizar no firma tiempo — no firma tiempo falso (P11).

## 6. Qué no son interfaces

Sin cambios respecto de D-07 §3: ningún servicio habla con los switches directamente; la Consola no toca bases; la Detección no ordena al controlador; 802.1X queda reservado para puertos sensibles de un despliegue real ([`H-01`](../H-Despliegue/01_infraestructura_fisica.md) §4). Lo que este documento detalla da forma operativa a los contratos de D — no crea ninguno nuevo.

## 7. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| `FEATURES_REPLY` y negociación contra el switch real | Lo declarado = lo usado (V1) | P1, RP-11 |
| Conexión de control rechazada desde otra interfaz (V6) | El canal es solo de gestión | RA-09 |
| `Access-Request` con accounting completo | Sesión con `Acct-Session-Id` correlacionable | R1.9, I4 |
| Sondeo 5/60 s con hueco simulado (controlador detenido) | Hueco declarado, línea base intacta | P11, RNF-03 |
| Desfase de reloj de todos los nodos | Máximo desfase observado (NTP) | RNF-09, E-05 |
| Espejo activo con tráfico externo generado | El sensor ve una copia fiel y no interpone | R5, P8 |

# Configuraciones

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** G — Diseño de bajo nivel (LLD)
**Estado:** Borrador formal para revisión

---

La **configuración es el estado declarado del sistema**: todo lo que no es código queda en configuración, versionada y reproducible ([`F-08`](../F-Decisiones_tecnologicas/08_entorno_del_prototipo.md) §4, RNF-11). Dos clases, con reglas distintas:

- **Identidad y seguridad** — secretos, credenciales y claves. **Nunca** en el repositorio del código ni en texto claro en disco compartido: variables de entorno o almacén de secretos del entorno, y rotación por procedimiento.
- **Comportamiento** — parámetros que este LLD fija con **valores iniciales** (los definitivos los calibra la medición, P12) y que se ajustan por la vía administrativa (I7), quedando **quién** los cambió en auditoría.

Todo parámetro de este documento lleva su origen: nada se inventa aquí, se aterriza lo que F decidió.

## 2. El controlador (ONOS)

| Parámetro | Valor inicial | Origen |
|---|---|---|
| Modo de operación | OpenFlow 1.3, un pipeline por dispositivo | [`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §2 |
| Endpoints de control (switches) | `tcp:10.0.0.20:6653` + dos endpoints de reserva del clúster (documentados, no desplegados) | [`F-01`](../F-Decisiones_tecnologicas/01_controlador_y_api_northbound.md) §6 |
| Northbound (I2) | REST habilitado solo en la interfaz de gestión; clave de servicio por cliente | [`01`](01_apis.md) §2 |
| Registro de cookies | tabla string ↔ 64 bits, persistida | [`06`](06_reglas.md) §3 |
| Inventario de servicios | anclajes declarados por I2, base del grafo | [`01`](01_apis.md) §4 |
| Registro de asociaciones | MAC ↔ switch:puerto ↔ IP por dispositivo aprendido | P7, [`F-01`](../F-Decisiones_tecnologicas/01_controlador_y_api_northbound.md) §5 |

## 3. El plano de datos (PicOS)

| Parámetro | Valor inicial | Origen |
|---|---|---|
| Modo | OpenFlow 1.3 dedicado (el pipeline SDN no convive con L2 autónomo en los puertos de acceso) | [`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §2 |
| Canal de control | interfaz `ma1`, whitelist del controlador, `ECHO` 5 s | [`04`](04_interfaces.md) §2 |
| Puerto espejo | replicación del segmento externo hacia el puerto del sensor | [`F-07`](../F-Decisiones_tecnologicas/07_perimetro_r5.md) §3 |
| Buffer | `PACKET_IN` con `buffer_id` utilizable (V7); la redirección usa el mecanismo que V3/V4 firme | [`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §4 |
| Tablas | una por etapa del pipeline si V1 confirma multi-tabla; si no, entradas compuestas | [`06`](06_reglas.md) §2 |

## 4. El intermediario (RabbitMQ)

| Parámetro | Valor inicial | Origen |
|---|---|---|
| Vhost / exchange | `plataforma` / exchange `plataforma` (topic, durable) | [`F-04`](../F-Decisiones_tecnologicas/04_mensajeria_y_eventos.md) §3 |
| Usuarios | uno por servicio, permisos solo sobre sus colas | P3 |
| Política de colas por servicio | durable; límite de longitud 100 000; DLX hacia su `dlq.<cola>` | [`02`](02_eventos.md) §5 |
| Política de colas por incidente | `inc.*` durable, TTL de respaldo 24 h, auto-borrado al cierre | [`F-04`](../F-Decisiones_tecnologicas/04_mensajeria_y_eventos.md) §3 |
| Confirmación de publicación | activada; buffer local del cliente 10 000 | [`F-04`](../F-Decisiones_tecnologicas/04_mensajeria_y_eventos.md) §4 |
| Reintentos | 5 con retroceso 1 s → 60 s, luego DLQ | [`02`](02_eventos.md) §5 |

## 5. La persistencia (PostgreSQL)

| Parámetro | Valor inicial | Origen |
|---|---|---|
| Instancias | una única instancia, seis bases, un usuario por base sin grants cruzados | [`F-05`](../F-Decisiones_tecnologicas/05_persistencia_auditoria_y_tiempo.md) §2 |
| Conexiones | pool por servicio, límite por usuario | P3 |
| Respaldo | `pg_dump` diario del volumen; drill de restauración programado | [`F-05`](../F-Decisiones_tecnologicas/05_persistencia_auditoria_y_tiempo.md) §4 |
| Retenciones | auditoría 90 días; contadores 24 h / 7 días agregados | [`03`](03_datos.md) §3 |

## 6. La identidad (FreeRADIUS + OpenLDAP)

| Parámetro | Valor inicial | Origen |
|---|---|---|
| Cliente RADIUS | solo el IAM, con secreto compartido propio | [`04`](04_interfaces.md) §3 |
| Puertos | 1812/1813 UDP, segmento de gestión | [`04`](04_interfaces.md) §3 |
| Accounting | `Interim` cada 300 s; `Acct-Session-Id = sesion_id` | [`04`](04_interfaces.md) §3 |
| Directorio | bind de solo lectura; árbol `ou=comunidad` con cuentas de prueba; índice `uid` | [`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §2 |
| TOTP | RFC 6238, ventana ±1, secreto cifrado en `bd_iam` | [`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §3 |

## 7. El sensor perimetral (Suricata) y su adaptador

| Parámetro | Valor inicial | Origen |
|---|---|---|
| Modo | IDS sobre interfaz de espejo; nunca en el camino (ni IPS inline) | [`F-07`](../F-Decisiones_tecnologicas/07_perimetro_r5.md) §2 |
| Reglas | lista propia con `vigencia` y `responsable` por firma; la regla de promoción de nuevas firmas | [`F-07`](../F-Decisiones_tecnologicas/07_perimetro_r5.md) §4 |
| Salida | `eve.json` → adaptador → evento `AnomalyDetected` con origen `perimetro` | [`F-07`](../F-Decisiones_tecnologicas/07_perimetro_r5.md) §3 |
| Feeds externos | ninguno en el prototipo (RP-06); el punto de integración queda para el despliegue | [`F-07`](../F-Decisiones_tecnologicas/07_perimetro_r5.md) §4 |

## 8. Sesión, portal y consola

| Parámetro | Valor inicial | Origen |
|---|---|---|
| Cookie de sesión | opaca, `HttpOnly` · `Secure` · `SameSite=Lax`; validez en servidor | [`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §4 |
| Token derivado | vida corta, misma vigencia y ligadura que la sesión | [`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §4 |
| Vigencias | ACADÉMICO 30 min idle / 12 h tope · operador 15 min / 8 h · elevación 1 h | [`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §5 |
| TLS | certificados del laboratorio en gestión; el portal es HTTPS siempre | RA-09 |
| Selector | explícito, en la entrada del portal; no concede nada | [`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §6 |

## 9. Observación y visualización

| Parámetro | Valor inicial | Origen |
|---|---|---|
| Frecuencias de I8 | conjunto caliente 5 s · barrido 60 s · configurables | [`F-06`](../F-Decisiones_tecnologicas/06_deteccion_y_mitigacion.md) §2 |
| Detección | α = 0,2 · ventana 5 s · N = 3 · k 4σ/2σ · piso 200 pps / 2 Mbps · calentamiento 30 min | [`F-06`](../F-Decisiones_tecnologicas/06_deteccion_y_mitigacion.md) §3 |
| Clasificación | flood ≥ k·σ + piso · distribuido ≥ 10 fuentes/60 s · brute-force ≥ 20 req/s · scanning > 20 destinos/60 s | [`F-06`](../F-Decisiones_tecnologicas/06_deteccion_y_mitigacion.md) §4 |
| Tiempo | chrony, fuente 10.0.0.25, UTC en todo registro | [`F-05`](../F-Decisiones_tecnologicas/05_persistencia_auditoria_y_tiempo.md) §5 |
| Grafana | datasources `bd_monitor` y `bd_auditoria` con usuario de **solo lectura**; dashboards versionados | [`F-05`](../F-Decisiones_tecnologicas/05_persistencia_auditoria_y_tiempo.md) §6 |

## 10. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Recrear todo el entorno desde la definición versionada | Sin pasos manuales | RNF-11 |
| Ajustar un umbral por I7 | El cambio aplica, se audita con su autor | P12, R1.9 |
| Acceso con credenciales de configuración fuera de gestión | Rechazo | RA-09 |
| Drill de restauración de la persistencia | Recuperación completa en el tiempo medido | F-05, E-04 |
| Desfase de reloj entre nodos | El máximo observado | RNF-09 |

# Reglas

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** G — Diseño de bajo nivel (LLD)
**Estado:** Borrador formal para revisión

---

La **regla es la unidad de política materializada**: cada entrada del pipeline del switch es una decisión de la plataforma convertida en match y acción ([`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §1). El orden de evaluación es una **jerarquía de autoridad**: a mayor prioridad, mayor poder de decidir sobre el paquete. La jerarquía es fija y es la misma en toda la red:

```text
mitigación (1000)   >   sesión y elevación (200)   >   esqueleto BASE (150–100)
>   caminos (20)    >   servicios básicos (10)     >   table-miss (aprendizaje / portal)
```

La mitigación manda sobre todo — es la respuesta al ataque; la sesión manda sobre el esqueleto — es el privilegio otorgado; el esqueleto manda sobre los caminos — es la línea base de cualquier dispositivo. **La política se aplica en el switch de ingreso**; los tramos siguientes solo resuelven caminos (P9: mitigar cerca del origen; [`flows/05`](../../../flows/05_enrutamiento.md) §2).

## 2. El pipeline lógico: dos etapas

**Decisión de esta fase** (cierra la cuestión de [`flows/01`](../../../flows/01_primitivas_openflow.md)): el pipeline lógico es de **dos etapas** — *política* (¿este paquete puede?) y *caminos* (¿por dónde sale?):

```text
paquete ──► ETAPA POLÍTICA (por switch de ingreso)          ──► ETAPA CAMINOS (todos los tramos)
            1000  mitigaciones (meter / drop)    ──►            20  ipv4_dst → puerto de salida
            200   sesión y elevación (allow)     ──►             5  inundación DHCP (broadcast)
            150   portal (pre-login)             ──►             table-miss → PACKET_IN
            120   par MAC/IP aprendido           ──►
            110   anti-spoofing          DROP
            100   destino gestión        DROP
            10    DHCP/DNS               ──►
            table-miss → PACKET_IN (aprendizaje / redirección al portal)
```

- Si la verificación **V1 confirma multi-tabla** ([`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §4), cada etapa es una tabla física (con `GOTO`).
- Si **no**, el controlador compone entradas únicas: match de política + instrucción de salida — la especificación lógica no cambia, cambia la materialización. **El cómo es responsabilidad del controlador** (I2, D-07); este LLD fija el qué.

## 3. Las prioridades, entrada a entrada

| Prioridad | Entrada | Match (etapa política) | Acción | Cookie | Vigencia |
|---|---|---|---|---|---|
| **1000** | Mitigación `RATE_LIMIT` | origen → objetivo | `meter` (banda de descarte a la tasa) → caminos | `INC-…` | `hard_timeout = ttl` (300 s inicial) |
| **1000** | Mitigación `BLOCK_SOURCE` | origen (→ cualquier destino) | DROP | `INC-…` | `hard_timeout = ttl` |
| **1000** | `ISOLATE_DEVICE` / `QUARANTINE` | dispositivo | DROP (todo) | `INC-…` | TTL corto (10 min) / TTL de la aprobación |
| **200** | Sesión de perfil | dispositivo → alcance del perfil | → caminos | `SES-…` | `idle_timeout` y tope de la sesión |
| **200** | Elevación | dispositivo → alcance elevado | → caminos | `SES-…` (sesión temporal) | TTL de la elevación |
| **150** | Portal | dispositivo → portal | → caminos | esqueleto | permanente |
| **120** | Par aprendido | `eth_src = MAC ∧ ip_src = IP` | → caminos | esqueleto | permanente |
| **110** | Anti-spoofing | `ip_src = IP ∧ eth_src ≠ MAC` | DROP | esqueleto | permanente |
| **100** | Denegación a gestión | dispositivo → red de gestión | DROP | esqueleto | permanente |
| **20** | Caminos | `ipv4_dst` | → puerto/vía calculada | camino | mientras valga la topología |
| **10** | DHCP y DNS | UDP 67/68, 53 | → caminos | esqueleto | permanente |
| — | Table-miss | — | `PACKET_IN` → aprendizaje o redirección al portal | — | — |

**El esqueleto BASE** (150–10) es la línea base que todo dispositivo lleva **antes de autenticarse**: portal, par MAC/IP, anti-spoofing, denegación a gestión y DHCP/DNS — la lista cerrada de [`access/00`](../../../access/00_auth_controller.md) §3. La sesión **no reemplaza** al esqueleto: convive y lo vence por prioridad (la escalera); el DROP de un académico hacia la gestión es permanente — su sesión nunca lo abre.

**Las cookies**, la convención ([`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §3): los 64 bits codifican tipo y correlativo — bits altos: `0x01` sesión, `0x02` incidente, `0x03` esqueleto, `0x04` camino —; el controlador mantiene el registro string ↔ valor y el retiro es **siempre por cookie**, en todas las tablas. Nada queda pegado (P10).

**Los meters**: un meter por par (origen, objetivo) limitado, con banda de descarte a la tasa del incidente; el controlador lleva el inventario de meters y los libera al retirar la mitigación. Si V2 no confirmara meters nativos, entra la **degradación documentada** de [`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §4 — el diseño no depende de ella.

**La redirección al portal**: el `PACKET_IN` de un dispositivo sin sesión se responde redirigiendo al portal — por grupo `ALL` o por `PACKET_OUT` según lo que la medición V3/V4 firme (P12 decide con los números; este LLD define ambos tramos del pipeline).

## 4. Los caminos (cierre de flows/05 §8)

- **Prioridad fijada: 20** — por debajo de la escalera (que puede denegar un destino) y por encima de DHCP/DNS (10). El valor era la cuestión abierta de [`flows/05`](../../../flows/05_enrutamiento.md) §8; queda cerrado aquí.
- **Costo por enlace fijado: 1 salto por defecto**, con penalización manual configurable por enlace saturado o de menor capacidad. La métrica era la otra cuestión abierta; el valor fino sale del experimento de rutas.
- **Caminos alternativos — la redundancia del plano de datos.** La topología del prototipo es dual-homed ([`H-01`](../H-Despliegue/01_infraestructura_fisica.md) §3): cada destino tiene dos caminos disjuntos. La conmutación sigue la regla de V3: si el switch confirma grupos *fast-failover*, cada destino lleva su grupo con puerto de vigía — la conmutación es **local, sin controlador** (P2)—; si no, el controlador reinstala el camino alternativo al recibir `PORT_STATUS`. El tiempo de conmutación se mide en ambos casos (RA-07).
- El cálculo se rehace cuando el grafo cambia (caída/alta de enlace por `PORT_STATUS`, alta de servicio en el inventario); un fallo elimina el enlace del grafo y los caminos afectados se reinstalan.
- **Presupuesto de entradas** ([`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §5): esqueleto ~6 por dispositivo + sesión ~4 + una entrada de camino por destino en cada switch del camino (o un grupo fast-failover por destino) + mitigaciones simultáneas — ≈ **350–450 entradas repartidas en los ocho switches**. El llenado real se mide y se reporta (RNF-05, RA-08).

## 5. Determinismo

Las prioridades, la estructura de cookies y la división política/caminos son **constantes del LLD**, no configuración libre: la jerarquía de autoridad no se negocia por parámetro. Lo configurable es lo que las reglas **parametrizan** —tasas, TTL, alcances, umbrales— y eso vive en `bd_politicas` con su auditoría ([`03`](03_datos.md) §3).

## 6. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Instalación del esqueleto en un dispositivo nuevo | Las 6 entradas con sus prioridades | R1.1, P5 |
| Sesión que vence al DROP (académico → servicios) y que nunca abre gestión | La escalera manda | R1.3, R1.6 |
| Mitigación sobre tráfico de sesión en curso | 1000 manda sobre 200 | R4.8, P9 |
| Retiro por cookie de una sesión y de una mitigación | Solo lo propio se retira; nada queda pegado | P10 |
| Caída de un enlace con caminos alternativos | Conmutación (grupo o recálculo) y su tiempo | flows/05 §8, E-04, RA-07 |
| Llenado por lotes hasta `TABLE_FULL` | La capacidad real por tabla | RNF-05, RA-08 |

# Detalles de implementación

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** G — Diseño de bajo nivel (LLD)
**Estado:** Borrador formal para revisión

---

Cada **servicio es una responsabilidad** ([`D-04`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/04_descomposición_arquitectonica.md) §3) **con un ciclo de vida** —arranque, operación, degradación, reconciliación— **y una estructura interna en capas**: API (entrada síncrona), dominio (la lógica), persistencia (su base, solo la suya) y salida de eventos (el bus). Los productos (controlador, broker, bases, RADIUS, directorio, sensor) quedan como están: los servicios propios **no reimplementan lo que los productos ya hacen**.

**Ecosistema único** para los servicios propios: **Python 3.12**, con FastAPI para las APIs, SQLAlchemy para la persistencia, `pika` para el bus, `pyrad` para RADIUS y una implementación directa de RFC 6238 para el TOTP. Un solo lenguaje para ocho servicios es simplicidad justificada (P4): un patrón de despliegue, un patrón de pruebas y una sola forma de operar para todo el equipo. El controlador es Java (ONOS, producto) y el sensor C (Suricata, producto): cada pieza en su ecosistema natural.

**Ciclo de vida común.** Todo servicio expone `/health` en dos niveles: *liveness* (el proceso vive) y *readiness* (su base y sus colas responden). Un servicio no *ready* no recibe tráfico; la red **no** depende de él — lo instalado en los switches sigue operando (P2). La degradación sigue las garantías de [`02`](02_eventos.md) §5 (buffer local, DLQ, huecos declarados) y la reconciliación la regla de [`03`](03_datos.md) §4: **el plano de datos es la verdad**.

## 2. IAM — la identidad y sus sesiones

**Módulos:** `api` (I3 e I7) · `radclient` (I4) · `sesiones` · `totp` · `tokens` · `repositorio` (bd_iam).

```text
login(usuario, secreto, poblacion, ip_origen):
  si poblacion == "operacion":
      op = operadores[usuario]; verificar_bcrypt(secreto, op.hash)
      verificar_totp(op.totp_secreto, codigo, ventana=±1)     # sin variante sin TOTP
  si poblacion == "comunidad":
      r = radius.access_request(usuario, secreto)              # IdP decide (I4)
      perfil = r.atributos["perfil"]; radius.accounting("Start")
  asociacion = i2.asociaciones(ip=ip_origen)                   # ligadura al dispositivo
  sesion = crear_sesion(usuario, perfil, asociacion, ttl[perfil])
  publicar(SessionOpened)                                      # el Policy Engine ordena el perfil
  emitir_cookie_opaca(sesion)                                  # HttpOnly · Secure · SameSite

validar_peticion(cookie, ip_origen):
  s = sesiones[hash(cookie)]            # la validez vive en el servidor
  exigir(s.estado == activa y s.ip == ip_origen y ahora < s.hard_timeout)
  s.ultima_actividad = ahora

al_evento(MAC_Moved) si mac ∈ sesiones activas:
  cerrar_sesion(motivo="mac_moved"); radius.accounting("Stop"); publicar(SessionClosed)
```

El token para herramientas es el mismo hash de sesión con expiración propia (`tokens_derivados`): una sola fuente de verdad, dos formas de presentarla ([`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §4).

## 3. Registro — el catálogo de dispositivos privilegiados

**Módulos:** `api` · `catalogo` · `historial` · `repositorio` (bd_registro).

El alta es el acto administrativo que habilita (P7): TI registra el dispositivo (I7) → el Registro crea la entrada y su historial → el IAM emite el secreto TOTP del operador **una vez** (QR en la consola) → el operador verifica un código → recién entonces el par (dispositivo, operador) queda habilitado y el alta completa se audita ([`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §3). Cada `DeviceConnected` de una MAC registrada se anota en `historial_dispositivo` — es la fuente de la investigación de movimientos.

## 4. Monitor — la observación

**Módulos:** `sondeo` (I8 vía I2) · `ewma` · `publicador` · `repositorio` (bd_monitor).

```text
bucle_sondeo():                                  # régimen dual: 5 s caliente / 60 s completo
  por cada switch del lote:
      c = i2.contadores(switch)                  # multipart vía controlador (P1)
      si timeout(2s): registrar hueco de observacion; continuar   # no se inventa (P11)
      deltas = c - anterior; persistir(contadores)
  por cada destino protegido: actualizar_ewma(destino, deltas)
  publicar(MetricSample, por destino y ventana)  # materia prima de la Detección

actualizar_ewma(destino, x):
  b = lineas_base[destino]
  b.media   += alfa * (x - b.media)              # α = 0,2 (inicial)
  b.varianza += alfa * ((x - b.media)^2 - b.varianza)
```

El Monitor también **verifica** las mitigaciones: ante `MitigationApplied` compara los contadores del objetivo contra la línea base y publica `MitigationVerified` con `tasas_antes/despues` y `cumple_objetivo` — el segundo nivel de confirmación de I2 ([`F-01`](../F-Decisiones_tecnologicas/01_controlador_y_api_northbound.md) §4.4). Y produce `MAC_Moved`: la incoherencia entre la asociación aprendida y la ubicación observada es un **hecho determinista**, no un umbral (P7).

## 5. Detección — el juicio

**Módulos:** `clasificador` · `umbrales` (bd_politicas) · `histeresis`.

```text
al_metric_sample(m):
  b = linea_base(m.destino)
  si calentamiento_activo(m.destino): alertar_sin_actuar; return   # 30 min iniciales
  umbral = max(k_entrada * b.sigma, piso[destino])                  # relativo con piso
  si m.pps > b.media + umbral:
      s = estado[destino]
      si s == normal: s = sospecha(t0)              # 1ª ventana
      si s == sospecha y ventanas(t0) >= N:         # N = 3 sostenidas
          clase = clasificar(m)                     # flood / distribuido / brute / scanning
          publicar(AnomalyDetected, severidad_propuesta)
          s = alarma
  si m.pps < b.media + k_salida * b.sigma: s = normal   # histéresis: cuesta más salir
```

Las reglas de clasificación son las de [`F-06`](../F-Decisiones_tecnologicas/06_deteccion_y_mitigacion.md) §4 (≥ 10 fuentes/60 s → distribuido; ≥ 20 req/s por origen → brute-force; > 20 destinos/60 s → scanning). La Detección **clasifica, no ordena** (P8): su salida es `AnomalyDetected`; la respuesta es del Policy Engine.

## 6. Incidentes — el ciclo de vida

**Módulos:** `ciclo_vida` · `secuencia` · `consumidor_inc` (cola `inc.<id>`) · `reconciliacion` · `repositorio` (bd_incidentes).

```text
estados:  ABIERTO → EN_MITIGACION → MITIGADO → CERRADO
          └─► ESCALADO (brecha P12 o cuarentena pendiente) ─► CERRADO / nuevo peldaño

al_evento(e, secuencia):
  persistir eventos_incidente(e, secuencia)        # antes de procesar: reinicio sin pérdida
  si secuencia != esperada+1: hueco declarado; esperar faltante (buffer 100, 10 s)
  transicionar(incidente, e.tipo)                  # AnomalyDetected → abrir; Verified → mitigar…
  publicar por la cola del incidente y por las colas de servicio

reconciliar():                                     # al volver de una caída
  vivas = i2.reglas(cookie=inc.*)                  # la verdad del plano de datos
  por cada mitigación registrada sin regla viva: marcar expirada y cerrar (P10)
```

## 7. Políticas — la decisión y la orden

**Módulos:** `escalera` · `elevaciones` · `ordenes` (I2) · `repositorio` (bd_politicas).

```text
al_evento(IncidentOpened):
  peldaño = escalera[severidad, patrón]            # RATE_LIMIT → BLOCK → ISOLATE → QUARANTINE
  si peldaño == QUARANTINE: estado = ESPERANDO_APROBACION; publicar a Consola; return
  orden = i2.aplicar_mitigacion(peldaño, objetivo, orígenes, ttl)
  publicar(MitigationRequired)                     # el eco: informa, no ejecuta

al_evento(MitigationVerified) si no cumple_objetivo:
  publicar(IncidentEscalated)                      # P12: la brecha escala a humano (F-06 §6)
  # nunca se sube la fuerza automáticamente: P9 prima en la ejecución

aprobar_cuarentena(aprobacion_id):                 # vía I7, con humano
  i2.aplicar_mitigacion(QUARANTINE, aprobacion=aprobacion_id)
```

## 8. Auditoría — la prueba

**Módulos:** `ingesta` (cola `auditoria`, todo el catálogo) · `registro_directo` (actos I7) · `exportador` · `repositorio` (bd_auditoria).

```text
exportar(rango):                                   # retención larga, append-only
  por cada línea del rango:                        # tabla de 90 días
      hash = sha256(linea ‖ hash_anterior); escribir(linea + hash)
  registrar exports(archivo, rango, hash_final)
```

El export es **append-only con cadena de hash** ([`03`](03_datos.md) §3): cada línea encadena la anterior; el hash final se copia en `exports` y abre el archivo siguiente. La manipulación no puede pasar inadvertida (P11). El drill de restauración y el verificador de cadena son los que E-04 y F-05 exigen.

## 9. El adaptador del perímetro y la Consola

**Adaptador Suricata**: consume `eve.json`, traduce cada alerta de firma a un evento `AnomalyDetected` con `origen = "perimetro"` y lo publica — la cadena de R5 entra por el mismo camino que el resto ([`F-07`](../F-Decisiones_tecnologicas/07_perimetro_r5.md) §3). **Consola**: cliente de I7 (sin credenciales propias: la sesión es el SSO), suscrita a su cola para las alertas en vivo, y la que muestra el QR de aprovisionamiento TOTP en el alta.

## 10. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Login de operador con código TOTP incorrecto | Rechazo del segundo factor, sin variante sin TOTP | R1.2 |
| Cookie presentada desde otra IP | Rechazo e invalidación de sesión | RNF-01 |
| Sondeo con controlador detenido 30 s | Huecos declarados; línea base intacta | P11 |
| Escenario flood completo | Detección N ventanas → orden → `APLICADA` → `Verified` | R4, D-08 §6 |
| Reconciliación tras caída del Incident Manager | Mitigaciones expiradas cerradas contra I2 | E-04, P10 |
| Verificador de cadena de hash sobre un export alterado | La alteración rompe la cadena y se detecta | P11 |

