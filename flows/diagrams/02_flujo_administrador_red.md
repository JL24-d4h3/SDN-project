# Flujo de tráfico — Administrador de Red

**Proyecto:** Solución de seguridad para una red de campus académico
**Serie:** Flujos por rol — 2 de 4
**Estado:** Borrador formal para revisión

---

El tráfico asociado a la autenticación del Administrador de Red, a nivel de red y de reglas en los switches. Comparte la maquinaria del Especialista de TI (perfil BASE → portal → sesión) y se distingue en **qué destinos de la gestión quedan abiertos** — aquí es donde la diferencia de roles se convierte en reglas distintas.

## 1. Escenario y topología

```text
 PC-ADMIN (10.0.1.31, MAC B2:..)                     red de gestión 10.0.0.0/24
   │  puerto p4                                        ┌──────────────────┐
   ▼                                                   │ portal   10.0.0.5 │
 ┌────────┐          ┌────────┐        ┌────────┐      │ consola  10.0.0.6 │
 │   S1   │──────────│   S2   │────────│   S3   │      │ APIs     10.0.0.7 │
 └───┬────┘          └────────┘        └───┬────┘      │ control. 10.0.0.2 │
     │                                     │           │ sw mgmt .11-.13   │
   HostA (10.0.1.25)                    SRV-1         └──────────────────┘
   usuario académico                  (10.0.2.10)          canal out-of-band
```

## 2. Estado previo: perfil BASE en S1 (idéntico para todo dispositivo)

```text
S1 — tabla de flujos antes del login
┌────────────┬──────────────────────────────────────────┬────────────────┐
│ Prioridad  │ Match                                     │ Acción         │
├────────────┼──────────────────────────────────────────┼────────────────┤
│ 150        │ in_port=p4, ip_dst=10.0.0.5, tcp=443      │ ALLOW          │ ← excepción portal
│ 120        │ in_port=p4, eth_src=B2, ip_src=10.0.1.31  │ ALLOW          │ ← par aprendido
│ 110        │ in_port=p4, ip_src=10.0.1.31              │ DROP           │ ← IP con otra MAC
│ 100        │ in_port=p4, ip_dst=10.0.0.0/24            │ DROP           │ ← gestión denegada
│ 10         │ in_port=p4, UDP 67/68, 53                 │ → DHCP/DNS     │
└────────────┴──────────────────────────────────────────┴────────────────┘
```

Aunque PC-ADMIN esté **en la sala de administración**, antes del login es un dispositivo BASE: su MAC (B2) está en el registro de dispositivos privilegiados, pero el registro solo habilita la posibilidad de elevar — no concede nada (P7).

## 3. El tráfico del login

```text
PC-ADMIN ── HTTPS(credenciales) ──► S1 ──► portal (10.0.0.5)
            coincide prioridad 150 (única puerta hacia gestión)

Portal → IAM/AAA: paso 1, usuario + contraseña contra el repositorio propio
      de identidades privilegiadas (I6) · paso 2, código TOTP (obligatorio)
IAM → Policy Engine: identidad = admin_01, rol = ADMIN_RED,
      dispositivo = B2 (match con el registro), puerto = S1:p4,
      vigencia = sesión
Policy Engine → Controlador (comando northbound con confirmación)
Controlador → FLOW_MOD en S1 (paso 4)
IAM → SessionOpened → Auditoría
```

## 4. Las reglas después del login

```text
S1 — entradas de la sesión de admin_01
┌────────────┬──────────────────────────────────────────────────┬──────────────────────┐
│ Prioridad  │ Match                                             │ Acción               │
├────────────┼──────────────────────────────────────────────────┼──────────────────────┤
│ 200        │ in_port=p4, eth_src=B2, ip_dst=10.0.0.0/24        │ ALLOW                │
│            │  (idle_timeout = sesión · cookie = sesión-admin_01)                      │
└────────────┴──────────────────────────────────────────────────┴──────────────────────┘
```

A diferencia del Especialista de TI (que recibió dos entradas puntuales), el Administrador recibe **una entrada sobre toda la red de gestión**: su rol alcanza, a nivel de red:

```text
10.0.0.5   portal (renovación de sesión)
10.0.0.6   consola de administración
10.0.0.7   APIs (políticas, registro de dispositivos, incidentes)
10.0.0.2   controlador (northbound: consultar/administrar reglas y topología)
10.0.0.11–13   switches (SSH/SNMP de administración)
```

Detalles a nivel de switch:

- La prioridad 200 gana a la 100 (DROP de gestión): la sesión abrió lo que el perfil BASE cerraba, **solo para el puerto y la MAC de la sesión** — otro dispositivo del mismo puerto con otra MAC sigue bajo el DROP 100.
- **idle_timeout de sesión:** la inactividad devuelve la PC a BASE automáticamente, y FLOW_REMOVED lo informa.
- **cookie:** un solo FLOW_MOD DELETE retira toda la sesión al hacer logout.

## 5. La diferencia con el TI está en las reglas, no en la consola

| Destino en gestión | TI | Administrador de Red |
|---|---|---|
| Consola / APIs (10.0.0.6–7) | ALLOW | ALLOW |
| Controlador northbound (10.0.0.2) | DROP | **ALLOW** |
| Switches (10.0.0.11–13, SSH/SNMP) | DROP | **ALLOW** |

Ambos pasan por el mismo portal y el mismo Policy Engine; lo único distinto es el conjunto de entradas que el controlador instala. La red misma aplica la separación de funciones: al TI no le sirve de nada saber la contraseña de un switch — no tiene ruta.

## 6. Lo que el Administrador NO puede hacer (y dónde se le frena)

- **Crear Administradores de Red ni Superadministradores** (fase A §2.4): a nivel de red ya alcanza todo; esta restricción vive en los **permisos de la API** (P24 es del SA) y en la auditoría de cada alta, no en una regla de flujo. El diseño lo asume explícitamente: la red distingue roles para la conectividad; los permisos finos distinguen dentro de lo conectado.
- **Aprobar elevaciones sin registro:** toda aprobación produce evento `ElevationGranted` → Auditoría; la regla temporal lleva TTL y cookie (P10, P11).
- **Tocar la red sin dejar huella:** sus FLOW_MOD pasan por el Policy Engine y quedan en el registro de acciones.

## 7. Cierre de sesión

```text
Logout ──► IAM: SessionClosed
        ──► Controlador: FLOW_MOD DELETE (cookie = sesión-admin_01)
        ──► S1: regresan las reglas BASE (paso 2)

Inactividad ──► idle_timeout expira ──► FLOW_REMOVED ──► BASE
```

## 8. Lo que este flujo demuestra

- El rol se materializa como **reglas con alcance de destino, prioridad y expiración** — no como "la PC del admin".
- La sala de administración no concede nada: la ubicación no es un match field (P6).
- La diferencia TI vs Administrador es visible en las tablas de flujo: dos sesiones, mismo mecanismo, destinos distintos.
