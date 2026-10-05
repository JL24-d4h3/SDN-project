# Flujos arquitectónicos principales

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** D — Arquitectura de alto nivel (HLD)
**Estado:** Borrador formal para revisión

---

Los flujos de extremo a extremo de la arquitectura, a nivel de componentes y eventos. La exposición detallada paso a paso —con los mensajes OpenFlow exactos— vive en la serie de flujo (`flows/`, partes 0–5); este documento resume cada flujo como cadena de componentes y lo ancla a los requerimientos.

## F1 — Arranque y descubrimiento de la red

**Disparador:** encendido de switches y controlador.

```text
Switch (boot) → canal OpenFlow → FEATURES (capacidades declaradas)
Controlador → FLOW_MOD: table-miss → CONTROLLER
Controlador → FLOW_MOD: eth_type=0x88CC → CONTROLLER   (captura LLDP)
Controlador → PACKET_OUT (LLDP por cada puerto de cada switch)
Switches → PACKET_IN (LLDP del vecino, OFPR_ACTION)
Controlador → deducción de enlaces dirigidos + confirmación bidireccional
           → grafo de topología
Controlador → (+ inventario de servicios) FLOW_MOD por destino:
              caminos hacia los servicios (proactivo; parte 5)
```

**Resultado:** la red conoce su topología y sus caminos hacia los servicios; lista para reaccionar al tráfico. **Detalle:** serie de flujo, partes 2 §2–5 y 5. **Cubre:** RT-05, RP-02.

## F2 — Conexión de un dispositivo y perfil BASE

**Disparador:** primer paquete de un host (DHCPDISCOVER).

```text
Host → frame → Switch → table-miss → PACKET_IN (OFPR_NO_MATCH)
Controlador → aprende host (MAC, IP, switch, puerto) → evento DeviceConnected
Controlador → camino al servidor DHCP por la ruta calculada (sin inundación)
           → FLOW_MOD: identidad en el acceso, destino en el interior
Host ↔ DHCP → diálogo completo (sin pasar por el controlador)
Controlador → entradas del perfil BASE:
              PERMITIR DHCP, DNS y portal   (prioridad 10 / 150)
              DROP hacia red de gestión     (prioridad 100)
```

**Resultado:** el dispositivo opera con privilegios mínimos —DHCP, DNS y una sola puerta, el portal—; el resto llega con el login (P5, P6). **Detalle:** serie de flujo, partes 2 §6–10, 5 §6 y 3 §2. **Cubre:** R1, R2.

## F3 — Login en el portal y sesión privilegiada

**Disparador:** login en el portal cautivo.

```text
Académico → portal → credenciales → IAM/AAA → IdP (identidad válida)
          → perfil ACADÉMICO: servicios académicos e Internet (idle_timeout)
Operador  → portal → paso 1: repositorio propio · paso 2: TOTP
          → identidad + dispositivo (match con registro) + contexto
          → decisión: sesión de rol (p. ej. ADMIN_RED)
IAM → evento SessionOpened
Policy Engine → comando northbound al Controlador
Controlador → FLOW_MOD: acceso de persona y destinos del rol
              (ALLOW hacia red de gestión, prioridad 200,
               idle_timeout = sesión)
Sesión cerrada / inactividad → idle_timeout expira
→ el switch elimina la entrada solo → dispositivo regresa a BASE
→ evento SessionClosed (FLOW_REMOVED lo confirma)
```

**Resultado:** el privilegio dura lo que dura la sesión y es reversible sin intervención (P10). **Detalle:** serie de flujo, parte 3 §5–6. **Cubre:** R1.2, R1.9, RA-09.

## F4 — Solicitud y aprobación de elevación temporal

**Disparador:** solicitud de un usuario académico (P28).

```text
Usuario académico → solicitud (perfil, alcance, duración, justificación)
IAM → evento ElevationRequested → Consola (visible para el Admin. Red)
Administrador de Red → aprueba o rechaza (P29)
Policy Engine → política temporal ABAC-like con TTL
              → evento ElevationGranted → comando al Controlador
Controlador → FLOW_MOD: ALLOW al recurso pedido (prioridad 200, TTL)
TTL vence → Policy Engine emite ElevationExpired
          → Controlador retira la regla (FLOW_MOD DELETE)
```

**Resultado:** un permiso excepcional con fecha de caducidad, aprobado por quien administra la red y registrado en auditoría (P10, P11). **Detalle:** serie de flujo, parte 3 §7. **Cubre:** R1.3, R1.5, P28–P29.

## F5 — Registro de operador y de dispositivo privilegiado

**Disparador:** incorporación de un operador o de un equipo de operación.

```text
Fase A — Solicitud: persona, identificación, rol, área, justificación,
        vigencia, solicitante/aprobador
Fase B — Aprobación: según jerarquía (SA registra admins y TI;
        Admin registra dispositivos, P30)
        → alta en IAM (identidad + rol, con valid_from/valid_until)
        → alta en el Registro de dispositivos (MAC, titular, vigencia)
        → evento DeviceRegistered → Auditoría
Fase C — Autenticación: el alta NO produce reglas; el operador
        obtiene privilegios solo al hacer login (F3)
```

**Resultado:** el registro y la red quedan separados: el catálogo habilita, no concede (P7); la auditoría sabe quién registró qué (P11). **Detalle:** serie de flujo, parte 3 §8. **Cubre:** R1.7, P24, P30.

## F6 — Ciclo completo de R4: detección y mitigación

**Disparador:** tráfico anómalo hacia un servidor protegido.

```text
Monitor (fondo): sondeo de contadores (MULTIPART) → línea base
Monitor → métricas → Detection Engine (cadena Pipe-and-Filter)
Detection → evento AnomalyDetected (tipo, tasas, desviación)
Incident Manager → IncidentOpened (INC-0042, severidad)
Policy Engine → decisión según escalera (RATE_LIMIT → BLOCK → …)
              → evento MitigationRequired + comando northbound
Controlador → FLOW_MOD en el switch de INGRESO de cada origen:
              Meter(m1) o DROP (prioridad 1000, cookie=INC-0042,
              hard_timeout 300 s)
Switch → ejecuta en el plano de datos → MitigationApplied
Monitor → relee contadores: 900 → 35 Mbps → MitigationVerified
Incident Manager → MITIGATED
```

**Resultado:** la cadena completa detección → decisión → aplicación → verificación, con un responsable por eslabón (P8) y mitigación cerca del origen (P9). **Detalle:** serie de flujo, parte 4. **Cubre:** R4, RA-06, RT-08.

## F7 — Recuperación y restauración post-incidente

**Disparador:** verificación de que el ataque terminó (o expiración del timeout).

```text
Monitor: el flujo mitigado ya no supera umbrales → MitigationExpired
  (o hard_timeout expira → FLOW_REMOVED lo informa)
Incident Manager → RECOVERED
Policy Engine → comando de retirada al Controlador
Controlador → FLOW_MOD DELETE (por cookie INC-0042)
Switch → elimina la regla de mitigación → política original activa
Incident Manager → CLOSED
Auditoría → registro completo: quién detectó, quién decidió,
            quién aplicó, cuándo se retiró y por qué
```

**Resultado:** la regla vive exactamente lo que vive el ataque; el usuario legítimo recupera su conectividad sin intervención manual (P10). **Detalle:** serie de flujo, parte 4 §9–10. **Cubre:** R4.9, RT-10.

## Flujo de fondo: monitoreo continuo

Todos los flujos anteriores se apoyan en un flujo permanente: el Monitor sondea contadores, actualiza la línea base y verifica las mitigaciones activas. Sin él, F6 y F7 no existen. Su frecuencia es configurable y depende de los umbrales que se fijen en la Fase F.

## Cuestiones abiertas

- **Intervención humana en F6.** La aprobación del Administrador de Red para aislamientos de alto impacto está definida; queda fijar qué otras acciones la exigen con las mediciones del prototipo.
- **F7 sin F6.** Si la mitigación fue manual (operador), la restauración sigue el mismo camino: la regla se retira igual (cookie + FLOW_MOD DELETE), y la auditoría registra al operador como actor.
