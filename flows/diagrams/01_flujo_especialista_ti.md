# Flujo de tráfico — Especialista de TI

**Proyecto:** Solución de seguridad para una red de campus académico
**Serie:** Flujos por rol — 1 de 4
**Estado:** Borrador formal para revisión

---

El tráfico asociado a la autenticación del Especialista de TI, a nivel de red y de reglas en los switches: qué entra antes del login, cómo llega al portal, qué reglas se instalan después y cómo se retiran al cerrar la sesión.

## 1. Escenario y topología

```text
 PC-TI (10.0.1.30, MAC B1:..)                     red de gestión 10.0.0.0/24
   │  puerto p3                                      ┌──────────────────┐
   ▼                                                 │ portal   10.0.0.5 │
 ┌────────┐          ┌────────┐        ┌────────┐    │ consola  10.0.0.6 │
 │   S1   │──────────│   S2   │────────│   S3   │    │ APIs     10.0.0.7 │
 └───┬────┘          └────────┘        └───┬────┘    │ control. 10.0.0.2 │
     │                                     │         │ sw mgmt .11-.13   │
   HostA (10.0.1.25)                    SRV-1       └──────────────────┘
   usuario académico                  (10.0.2.10)        canal out-of-band
```

Antes del login, PC-TI es un dispositivo más: el controlador la conoce por el PACKET_IN de su primer tráfico, su MAC **no está** asociada a ninguna identidad, y su perfil es BASE.

## 2. Estado previo: las reglas del perfil BASE en S1

```text
S1 — tabla de flujos (perspectiva del pipeline)
┌────────────┬──────────────────────────────────────────┬────────────────┐
│ Prioridad  │ Match                                     │ Acción         │
├────────────┼──────────────────────────────────────────┼────────────────┤
│ 150        │ in_port=p3, ip_dst=10.0.0.5, tcp=443      │ ALLOW          │ ← excepción portal
│ 120        │ in_port=p3, eth_src=B1, ip_src=10.0.1.30  │ ALLOW          │ ← par aprendido
│ 110        │ in_port=p3, ip_src=10.0.1.30              │ DROP           │ ← IP con otra MAC
│ 100        │ in_port=p3, ip_dst=10.0.0.0/24            │ DROP           │ ← gestión denegada
│ 10         │ in_port=p3, UDP 67/68                     │ → DHCP (S2)    │
│ 10         │ in_port=p3, UDP dst=53                    │ → DNS          │
└────────────┴──────────────────────────────────────────┴────────────────┘
```

La entrada de prioridad **150 es la única puerta que el perfil BASE tiene hacia la red de gestión**: el portal (10.0.0.5:443). Todo lo demás de 10.0.0.0/24 muere en la prioridad 100. Sin esa excepción, nadie podría autenticarse jamás. El BASE no da nada más: los servicios académicos e Internet no están — llegan con la sesión (§4).

## 3. El tráfico del login (a nivel de red)

```text
PC-TI ── HTTPS(credenciales) ──► S1 ──► ... ──► portal (10.0.0.5)
   │            coincide prioridad 150
   │
Portal → IAM/AAA: paso 1, usuario + contraseña contra el repositorio propio
      de identidades privilegiadas (I6) · paso 2, código TOTP (obligatorio)
IAM → Policy Engine: identidad = ti_01, rol = TI,
      dispositivo = B1 (match con el registro), puerto = S1:p3,
      contexto = sala de operaciones, vigencia = sesión
Policy Engine → Controlador (northbound, comando con confirmación)
Controlador → FLOW_MOD en S1 (las reglas del paso 4)
IAM → evento SessionOpened → Auditoría
```

Ningún paquete de datos pasa por el controlador: el tráfico del login viaja por el plano de datos hasta el portal, igual que cualquier flujo, y solo las **reglas** cambian.

## 4. Las reglas después del login (el cambio en S1)

```text
S1 — entradas añadidas/modificadas para la sesión de ti_01
┌────────────┬──────────────────────────────────────────────────┬──────────────────────┐
│ Prioridad  │ Match                                             │ Acción               │
├────────────┼──────────────────────────────────────────────────┼──────────────────────┤
│ 200        │ in_port=p3, eth_src=B1, ip_dst=10.0.0.6, tcp=443  │ ALLOW (consola)      │
│ 200        │ in_port=p3, eth_src=B1, ip_dst=10.0.0.7, tcp=443  │ ALLOW (APIs)         │
│ 200        │ in_port=p3, eth_src=B1, ip_dst=10.0.0.0/24        │ DROP  ← el resto     │
│            │                                                  │        de gestión    │
│ (idle_timeout = duración de sesión · cookie = sesión-ti_01)   │                      │
└────────────┴──────────────────────────────────────────────────┴──────────────────────┘
```

Detalles a nivel de switch:

- **Prioridad 200** gana a la 150 y a la 100: la sesión manda sobre el perfil BASE, pero solo para lo que el rol puede alcanzar.
- **El TI NO alcanza los switches ni el controlador.** Sus entradas permiten únicamente la consola (10.0.0.6) y las APIs de incidentes/monitoreo (10.0.0.7). El SSH a los switches (10.0.0.11–13) y el northbound del controlador (10.0.0.2) siguen cubiertos por DROP: a nivel de red, el TI no tiene camino.
- **idle_timeout de sesión:** si la consola queda inactiva, la entrada expira sola en el switch y el dispositivo regresa a BASE sin intervención.
- **cookie:** todas las entradas de la sesión comparten cookie; el controlador las retira con un solo FLOW_MOD DELETE al cerrar.

## 5. Qué tráfico queda permitido y qué denegado (resumen por destino)

| Destino | Antes del login (BASE) | Con sesión TI |
|---|---|---|
| DHCP y DNS | ALLOW | ALLOW |
| Servicios académicos e Internet | — (no en BASE) | **ALLOW** |
| Portal (10.0.0.5:443) | ALLOW (excepción 150) | ALLOW |
| Consola de monitoreo (10.0.0.6:443) | DROP | **ALLOW (200)** |
| APIs de incidentes (10.0.0.7:443) | DROP | **ALLOW (200)** |
| SSH/SNMP a switches (10.0.0.11–13) | DROP | **DROP** |
| Controlador / northbound (10.0.0.2) | DROP | **DROP** |

## 6. El TI y las mitigaciones: sin tocar los switches

El Especialista de TI supervisa incidentes y ejecuta mitigaciones autorizadas, pero **nunca instala reglas directamente**: su acción en la consola se convierte en una decisión del Policy Engine, y es el controlador quien escribe los FLOW_MOD. El tráfico del TI y la regla que su acción produce son caminos distintos:

```text
TI (consola, por sus reglas de sesión) ──► aprueba mitigación
Policy Engine ──► Controlador ──► FLOW_MOD en el switch de ingreso
                 (el TI no participa de este camino)
```

## 7. Cierre de sesión y retorno a BASE

```text
Logout en la consola ──► IAM: evento SessionClosed
  → Controlador: FLOW_MOD DELETE (cookie = sesión-ti_01)
  → S1: quedan solo las reglas BASE (tabla del paso 2)

Inactividad ──► idle_timeout expira en S1
  → las entradas se eliminan solas → FLOW_REMOVED avisa al controlador
  → mismo resultado: perfil BASE
```

## 8. Lo que este flujo demuestra

- La autenticación **no abre la red entera**: abre el acceso de persona (servicios e Internet) y los destinos del rol, con prioridad acotada y expiración (P6, P10).
- La red distingue al TI del administrador **en las reglas**, no en las intenciones: el TI no tiene entrada hacia los switches (separación de funciones, fase A §2.6).
- Todo el recorrido queda registrado: `SessionOpened`, los comandos del Policy Engine y `SessionClosed` van a la auditoría (P11).
