# Flujo de tráfico — Usuario genérico (académico)

**Proyecto:** Solución de seguridad para una red de campus académico
**Serie:** Flujos por rol — 4 de 4
**Estado:** Borrador formal para revisión

---

El tráfico del usuario genérico (usuario académico: perfil BASE antes del login, ACADÉMICO después) y, sobre ese mismo tráfico, cómo las reglas de los switches contienen los ataques: DDoS, IP spoofing, port scanning y suplantación de MAC. Todo a nivel de red y de tablas de flujo.

## 1. Conexión: del perfil BASE al perfil ACADÉMICO

```text
 HostA (10.0.1.25, MAC A1:..)                     10.0.2.10 SRV-1 (protegido)
   │  puerto p1                                    10.0.2.1  DHCP/DNS
   ▼
 ┌────────┐          ┌────────┐        ┌────────┐
 │   S1   │──────────│   S2   │────────│   S3   │──► SRV-1
 └────────┘          └────────┘        └────────┘
```

Tras el arranque (DHCP → ARP → aprendizaje por PACKET_IN, serie de flujo parte 2), el switch de ingreso queda con el **perfil BASE** —el mínimo del dispositivo— y con la **validación de origen**:

```text
S1 — reglas del dispositivo académico (p1, MAC A1, IP 10.0.1.25)
┌────────────┬──────────────────────────────────────────────┬───────────────────┐
│ Prioridad  │ Match                                         │ Acción            │
├────────────┼──────────────────────────────────────────────┼───────────────────┤
│ 150        │ in_port=p1, ip_dst=10.0.0.5, tcp=443          │ ALLOW (solo portal)│
│ 120        │ in_port=p1, eth_src=A1, ip_src=10.0.1.25      │ ALLOW             │ ← par aprendido
│ 110        │ in_port=p1, ip_src=10.0.1.25                  │ DROP              │ ← IP con otra MAC
│ 100        │ in_port=p1, ip_dst=10.0.0.0/24                │ DROP              │ ← gestión
│ 10         │ in_port=p1, UDP 67/68, 53                     │ → DHCP/DNS        │
└────────────┴──────────────────────────────────────────────┴───────────────────┘
```

Ese es el BASE: el dispositivo existe en la red (DHCP, DNS) y tiene una sola puerta, el portal. Los servicios académicos e Internet **no** están en el BASE.

**El login y el perfil ACADÉMICO.** Cuando el académico se autentica en el portal (usuario + contraseña contra el IdP institucional vía RADIUS; sin MFA — [doc 04 §4](../../docs/componentes/04_identidades_y_poblaciones.md)), el Policy Engine decide su perfil de sesión y el controlador añade las reglas:

```text
S1 — reglas añadidas por la sesión ACADÉMICO (post-login)
  in_port=p1, eth_src=A1, ip_dst=10.0.2.0/24  → ALLOW    (servicios académicos)
  in_port=p1, eth_src=A1 (resto)              → Internet
  (peldaño por definir al implementar · cookie = sesión · idle_timeout = sesión)
```

El peldaño exacto de la sesión académica en la escalera se fija al implementar (doc 02 §6–7), y sus reglas **no abren la red de gestión**: el DROP 100 y el anti-spoofing 120/110 siguen vigentes por encima. Al cerrar sesión o por inactividad, el switch retira las reglas solas (cookie + idle_timeout) y el dispositivo regresa a BASE.

El tráfico legítimo del académico es la suma de las dos tablas: cada paquete matchea una entrada, los contadores se incrementan y el controlador no interviene.

## 2. IP spoofing: la validación de origen en el puerto

El atacante cambia su IP origen para suplantar a otro host (o evadir su perfil). El controlador **aprendió** la asociación MAC↔IP↔puerto en el DHCP/ARP (parte 2 de la serie), y la materializa como el par de entradas 120/110:

```text
Trama con IP 10.0.1.25 y MAC correcta (A1)
   → matchea prioridad 120 → ALLOW

Trama con IP 10.0.1.25 y MAC falsificada (XX)
   → no matchea la 120 (eth_src distinto)
   → matchea prioridad 110 (la IP desde otra MAC) → DROP
```

- La 120 gana por prioridad solo para el par exacto aprendido; **cualquier otra MAC** que use esa IP muere en la 110.
- El mismo par de entradas se instala **en cada puerto de acceso**, con la IP aprendida de ese puerto: un host no puede usar una IP que el controlador asoció a otro puerto.
- El DROP incrementa contadores: el Monitor ve los descartes y, si el patrón persiste, escala a evento y mitigación (R3.3).

## 3. DDoS: detección y mitigación en el switch de ingreso

```text
HostA (comprometido) ── flood ──► S1 ──► S2 ──► S3 ──► SRV-1 (10.0.2.10)
        contadores suben en S1:p1 y en el flujo A1→SRV-1
```

```text
Monitor:  contadores de A1→SRV-1 = 900 Mbps / 12 000 pkt/s
          (línea base: 80 Mbps / 1 000 pkt/s)
Detection → AnomalyDetected → IncidentOpened (INC-0042, HIGH)
Policy Engine → decisión: RATE_LIMIT (severidad media) o BLOCK (severa)
Controlador → FLOW_MOD en S1 (switch de INGRESO, no junto a la víctima)
```

```text
S1 — regla de mitigación
┌────────────┬──────────────────────────────────────────────┬──────────────────────────┐
│ Prioridad  │ Match                                         │ Acción                   │
├────────────┼──────────────────────────────────────────────┼──────────────────────────┤
│ 1000       │ in_port=p1, eth_src=A1, ip_dst=10.0.2.10      │ Meter(m1)  [o DROP]      │
│            │  (cookie=INC-0042 · hard_timeout=300 s)       │                          │
└────────────┴──────────────────────────────────────────────┴──────────────────────────┘

Meter m1: banda 10 Mbps (tipo drop) — el exceso se descarta en el propio switch
```

- **Prioridad 1000**: por encima de TODO lo demás de la tabla — la mitigación manda sobre el forwarding, el perfil y el anti-spoof.
- **En el switch de ingreso**: el tráfico malicioso muere en S1 y no atraviesa S2/S3 ni llega a SRV-1 (P9). Con múltiples atacantes, la regla se instala en **cada** switch de ingreso de cada origen.
- **El meter limita dentro del plano de datos** a velocidad de línea, sin consultar al controlador.
- **Verificación**: el Monitor relee los contadores del flujo (900 → 35 Mbps) → `MitigationVerified`.
- **Recuperación**: si el ataque continúa al expirar, se renueva; si terminó, FLOW_MOD DELETE (cookie) restaura la política normal (P10).

## 4. Port scanning: limitación por tasa de solicitudes

```text
HostA ── SYN a 10.0.2.10:22, :80, :443, 10.0.2.11:22, ... ──► S1
        cientos de destinos/puertos en segundos
```

El patrón se detecta por **conteo de flujos nuevos desde el mismo origen** (no por volumen de bytes): el Monitor agrega contadores por origen, la Detección clasifica `scanning` (R3.2), y la respuesta es la misma escalera:

```text
S1 — contención del scanner
┌────────────┬──────────────────────────────────────────────┬──────────────────────────┐
│ Prioridad  │ Match                                         │ Acción                   │
├────────────┼──────────────────────────────────────────────┼──────────────────────────┤
│ 1000       │ in_port=p1, eth_src=A1, tcp (SYN)             │ Meter(m2)  [o DROP]      │
│            │  (cookie=INC-0043 · hard_timeout=300 s)       │                          │
└────────────┴──────────────────────────────────────────────┴──────────────────────────┘

Meter m2: banda de pps baja — el scanner sigue "conectado" pero su sondeo
          se degrada hasta ser inútil, sin cortar su tráfico legítimo
```

Igual que en el DDoS: prioridad 1000, cookie, timeout, verificación por contadores y retirada al terminar. La diferencia es la **dimensión limitada**: pps en vez de Mbps.

## 5. Suplantación de MAC: MAC_MOVE y cuarentena

El atacante cambia la MAC de su equipo para heredar un perfil ajeno o evadir el suyo:

```text
MAC A1 apareció en S1:p1 (aprendida) ──► de repente aparece en S2:p3
  → evento MAC_MOVE (incoherencia: misma MAC, otra ubicación)

MAC X cambió su MAC por A1 ──► usa IP 10.0.1.25 con MAC A1 en otro puerto
  → el par 120/110 del paso 2 ya no lo frena (la MAC coincide)
  → la respuesta no es una regla fija: es reacción al evento
```

```text
S2 — respuesta al MAC_MOVE
┌────────────┬──────────────────────────────────────────────┬──────────────────────────┐
│ Prioridad  │ Match                                         │ Acción                   │
├────────────┼──────────────────────────────────────────────┼──────────────────────────┤
│ 1000       │ in_port=p3, eth_src=A1                        │ DROP (bloqueo del puerto)│
│            │  (o mover a VLAN de cuarentena, según severidad)                       │
└────────────┴──────────────────────────────────────────────┴──────────────────────────┘
```

- La MAC original **no se reasocia**: el host legítimo en S1:p1 sigue funcionando; el suplantador en S2:p3 queda bloqueado o en cuarentena (P7).
- En puertos sensibles se añade **port security** (puerto → MACs permitidas) como primera barrera; el MAC_MOVE es la red de detección detrás.

## 6. La escalera completa de prioridades en un switch de acceso

```text
Prioridad   Qué es                                    Quién la instala
─────────────────────────────────────────────────────────────────────
1000        mitigación (meter/drop, cookie, timeout)  Policy → Controlador (R4/R3)
200         sesión privilegiada (gestión)             Policy → Controlador (login)
150         excepción portal (10.0.0.5:443)          Controlador (base)
120         par MAC/IP aprendido → ALLOW              Controlador (aprendizaje)
110         IP aprendida con otra MAC → DROP          Controlador (aprendizaje)
100         DROP hacia red de gestión                 Controlador (base)
10          DHCP y DNS → ALLOW                        Controlador (base)
  --        sesión académica (servicios + Internet)   Policy → Controlador (login)
```

Cada capa puede ser pisada por la de arriba: el DROP de gestión (100) no impide la sesión de un operador (200), y una mitigación (1000) se impone incluso a un operador legítimo si su tráfico coincide con el del ataque. El peldaño de la sesión académica está decidido en su función —servicios e Internet con la sesión atribuida a una identidad—; su **valor exacto se fija al implementar** (doc 02 §6–7).

## 7. Lo que las reglas de los switches NO resuelven

- **La identidad de quién está tras el dispositivo**: las reglas controlan MAC/IP/puerto de una sesión que el Policy Engine atribuyó a una identidad; la persona se autentica en el portal — el académico obtiene ACADÉMICO; el operador, su sesión de rol (P6, P7).
- **Ataques desde el exterior**: son de R5, en el perímetro, no del switch de acceso.
- **El contenido de lo permitido**: si un tráfico está permitido, la red no inspecciona su contenido; eso es asunto de los servicios (fuera del alcance).
