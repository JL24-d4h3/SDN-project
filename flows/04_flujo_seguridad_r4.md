# Flujo de seguridad: el ciclo completo de R4

**Proyecto:** Solución de seguridad para una red de campus académico
**Serie:** Descripción del flujo — parte 4 de 6
**Estado:** Borrador formal para revisión

---

R4: **detectar y mitigar ataques DDoS/brute-force en la intranet cuando el tráfico hacia un servidor o nodo se dispara.** Esta parte muestra la cadena completa detección → decisión → enforcement → verificación → recuperación, con los operadores privilegiados de la parte 3 participando donde corresponde.

```text
H1 ──── S1 ──── S2 ──── S3 ──── SERVIDOR (activo protegido)
H2 ──────┘
H3 ──────────┘
```

## 1. Paso 1 — Tráfico normal

La red opera en estado estable. Las entradas instaladas reenvían el tráfico legítimo (perspectiva del paquete):

```text
S1: match H1→SERVER  →  output p2
S2: match H1→SERVER  →  output p4
S3: match H1→SERVER  →  output p7
```

El controlador no ve paquetes; solo recibe estadísticas (paso 2).

## 2. Paso 2 — Monitoreo: lectura de counters

El monitor consulta periódicamente los **contadores** OpenFlow: por puerto (`OFPMP_PORT_STATS`) y por flujo (`OFPMP_FLOW`), mediante mensajes MULTIPART (parte 1 §5). Con ellos construye la línea base del servidor:

```text
Destino 10.0.0.50 (SERVER):
  normal:     100 Mbps · 1 000 pkt/s · 40 fuentes
  observado:  900 Mbps · 12 000 pkt/s · 143 fuentes
```

Un aumento no significa ataque: puede ser una clase virtual, una transferencia grande o un laboratorio. Por eso la condición de detección nunca es un único umbral aislado.

## 3. Paso 3 — Detección

El Detection Engine analiza: tasa de paquetes y bytes, número de fuentes, conexiones nuevas, duración, distribución de orígenes y puerto destino. Distingue dos fenómenos:

- **Flood/DDoS volumétrico:** busca saturar ancho de banda, pps o capacidad del servidor.
- **Brute-force de solicitudes:** cantidad excesiva de intentos/conexiones por segundo desde un origen.

Al superar los umbrales produce el evento:

```text
DDoSDetected
  destination = SERVER
  traffic_rate = 950 Mbps · 18 000 pkt/s
  sources = 143 (línea base: 40)
  deviation = anomalía sostenida
```

## 4. Paso 4 — Incidente

El detector **no bloquea**: genera un incidente en el Incident Manager. La separación es deliberada — el detector observa, no decide:

```text
Incidente INC-0042
  type:     TRAFFIC_FLOOD
  target:   SERVER
  sources:  H1, H2, H3, …
  severity: HIGH
  status:   DETECTED
```

El incidente es además el objeto que la auditoría seguirá de principio a fin.

## 5. Paso 5 — El Policy Engine decide

El Policy Engine recibe: incidente + estado de red + política de seguridad + contexto. Decide **qué hacer**, con una escalera de respuestas según severidad:

```text
NORMAL ──► RATE_LIMIT ──► BLOCK_SOURCE ──► ISOLATE_DEVICE ──► QUARANTINE
```

Ejemplo: 5 000 pkt/s sostenidos de H1 → `RATE_LIMIT`. 50 000 pkt/s multi-puerto persistente → `BLOCK_SOURCE`. La decisión sale como `MitigationRequested`, no como un bloqueo directo.

## 6. Paso 6 — El controlador decide dónde intervenir

El controlador conoce: topología + ubicación de los hosts + flujos existentes + política. El punto clave de la exposición: **mitiga cerca del origen, no cerca de la víctima.**

```text
H1 ── S1:p5 ── X ── S2 ── S3 ── SERVER
              ↑
   la regla se instala en el switch de ingreso de H1
```

Así, el tráfico malicioso se descarta antes de atravesar la red. Si el ataque entra por varios switches (H1 por S1, H2 por S2, H3 por S4), el controlador instala la regla **en cada switch de ingreso correspondiente** — control centralizado sobre una red distribuida, imposible con configuración manual por dispositivo.

Las reglas de camino por destino no se tocan: la mitigación se superpone en el ingreso (parte 5 §1).

## 7. Paso 7 — FLOW_MOD: la regla y el meter

El controlador construye la entrada de mitigación según la decisión (perspectiva del pipeline):

```text
Decisión RATE_LIMIT:
  Meter m1: bandas → hasta 10 Mbps permitido, el exceso se descarta
  S1: match ip_src=H1, ip_dst=SERVER
      → Meter(m1)            (prioridad 1000, hard_timeout 300 s)

Decisión BLOCK:
  S1: match in_port=p5, eth_src=MAC_H1, ip_dst=SERVER
      → DROP                 (prioridad 1000, hard_timeout 300 s)
```

Tres detalles importantes:

- **Prioridad 1000:** por encima del forwarding normal (prioridad ~10) y del perfil base (prioridad ~100). La mitigación manda sobre todo lo demás.
- **Meter vs controlador:** con el medidor, la limitación de tasa se ejecuta **dentro del switch**, a velocidad de línea, sin que el controlador procese paquetes. Si PicOS no soportara meters, el rate limiting tendría que degradarse a muestreo + reglas periódicas desde el controlador — una alternativa peor que conviene evitar (RP-11).
- **cookie:** la entrada se marca con un cookie que identifica al incidente INC-0042, para retirarla junto con sus hermanas en un solo FLOW_MOD DELETE (parte 1 §2).

## 8. Paso 8 — Verificación: releer los counters

La mitigación no se da por buena sin evidencia. El monitor vuelve a leer los contadores del flujo y del puerto:

```text
Antes:  900 Mbps hacia SERVER
Después: 35 Mbps hacia SERVER (tráfico legítimo residual)
```

`MitigationVerified` → el incidente cambia de estado: `DETECTED → MITIGATING → MITIGATED`.

## 9. Paso 9 — Recuperación: reglas que no se quedan para siempre

Una regla de DROP permanente bloquearía al usuario legítimo cuando el ataque termine. Dos mecanismos, combinados:

1. **Temporizadores nativos:** la entrada se instala con `hard_timeout`/`idle_timeout` (p. ej. 300 s). El switch la elimina solo al expirar, y con `OFPFF_SEND_FLOW_REM` avisa al controlador con un FLOW_REMOVED.
2. **Verificación periódica del controlador:** antes de dejar expirar, el controlador relee los contadores del flujo. Si el ataque continúa, renueva; si terminó, retira.

El segundo es mejor que depender solo del timeout: la regla vive exactamente lo que vive el ataque.

## 10. Paso 10 — Restauración

El controlador envía `FLOW_MOD DELETE` para la regla de mitigación (por cookie del incidente). Vuelve a quedar la política normal:

```text
FLOW_MOD DELETE (S1, cookie=INC-0042)
  → H1 ── S1 ── S2 ── S3 ── SERVER  (por los flujos originales)

Incidente: MITIGATED → RECOVERED → CLOSED
```

## 11. Paso 11 — Los operadores en R4

El sistema no depende de una persona para cada ataque: sería demasiado lento. La intervención humana escala con la severidad y el impacto:

| Situación | Respuesta | Interviene |
|---|---|---|
| Anomalía leve | `RATE_LIMIT` automático | Sistema (sin intervención) |
| DDoS severo | `BLOCK` automático + notificación | Sistema + Especialista de TI supervisa |
| Aislar un segmento completo | Propuesta de aislamiento | **Requiere aprobación** del Administrador de Red |
| Operaciones excepcionales (política global) | — | Superadministrador |

## 12. Paso 12 — Accounting: quién hizo qué

Cada acción queda registrada, conectando R4 con el registro de la parte 3:

```text
2026-09-24 10:32  INC-0042  detección automática  RATE_LIMIT  actor: SYSTEM
2026-09-24 10:35  INC-0042  jperez (ADMIN_RED)    BLOCK_SOURCE  target: H1  motivo: continued_attack
2026-09-24 10:48  INC-0042  jperez (ADMIN_RED)    REMOVE_MITIGATION  motivo: incident_recovered
```

Esto responde las preguntas de auditoría: ¿quién modificó qué regla, en qué switch, cuándo, por qué, y qué incidente lo originó? La cadena de responsabilidades queda explícita:

| Componente | Responsabilidad |
|---|---|
| Monitor | Obtener métricas (counters) |
| Detection Engine | Determinar si hay anomalía |
| Incident Manager | Registrar y gestionar el incidente |
| Policy Engine | Decidir la respuesta |
| SDN Controller | Traducir la decisión a FLOW_MOD/meters |
| Switch | Ejecutar la política en el plano de datos |
| Operador (TI/Admin/SA) | Supervisar y autorizar acciones de alto impacto |
| AAA/Identidad | Determinar quién puede actuar |
| Auditoría | Registrar acciones y resultados |

R4 es el caso de uso donde se ve toda la cadena de extremo a extremo: detección, política, SDN, OpenFlow, enforcement, privilegios y recuperación.

## 13. Cuestiones abiertas

- **Umbrales y línea base.** Los valores concretos (pps, Mbps, nº de fuentes, ventana temporal) dependen de mediciones en el entorno del prototipo, que aún no existe.
- **Soporte de meters en PicOS.** Determina si el rate limiting usa medidores nativos o degrada a controlador; se fija en la Fase F.
- **Renovación vs timeout.** Si la verificación periódica del paso 9 basta o se combina con temporizadores más cortos.
