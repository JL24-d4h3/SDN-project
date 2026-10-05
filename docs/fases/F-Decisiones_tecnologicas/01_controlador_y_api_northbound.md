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
