# Flujo de tráfico — Superadministrador

**Proyecto:** Solución de seguridad para una red de campus académico
**Serie:** Flujos por rol — 3 de 4
**Estado:** Borrador formal para revisión

---

El tráfico asociado a la autenticación del Superadministrador, a nivel de red y de reglas en los switches, incluida la variante de **acceso remoto** — la única diferencia de conectividad real frente al Administrador de Red, que en lo demás comparte sus reglas.

## 1. Escenario y topología

```text
 PC-SA (10.0.1.32, MAC B3:..)                     red de gestión 10.0.0.0/24
   │  puerto p5                                      ┌──────────────────┐
   ▼                                                 │ portal   10.0.0.5 │
 ┌────────┐          ┌────────┐        ┌────────┐    │ consola  10.0.0.6 │
 │   S1   │──────────│   S2   │────────│   S3   │    │ APIs     10.0.0.7 │
 └───┬────┘          └────────┘        └───┬────┘    │ control. 10.0.0.2 │
     │                                     │         │ sw mgmt .11-.13   │
   HostA (10.0.1.25)                    SRV-1       └──────────────────┘
   usuario académico                  (10.0.2.10)        canal out-of-band
```

Dos escenarios: el **local** (PC-SA conectada al puerto p5, idéntico al del Administrador) y el **remoto** (el SA autenticándose desde fuera del campus), que es la variante contemplada solo para este rol.

## 2. Escenario local: perfil BASE y login

Misma maquinaria que los roles anteriores:

```text
S1 — antes del login (PC-SA en p5)
┌────────────┬──────────────────────────────────────────┬────────────────┐
│ Prioridad  │ Match                                     │ Acción         │
├────────────┼──────────────────────────────────────────┼────────────────┤
│ 150        │ in_port=p5, ip_dst=10.0.0.5, tcp=443      │ ALLOW          │
│ 120        │ in_port=p5, eth_src=B3, ip_src=10.0.1.32  │ ALLOW          │
│ 110        │ in_port=p5, ip_src=10.0.1.32              │ DROP           │
│ 100        │ in_port=p5, ip_dst=10.0.0.0/24            │ DROP           │
│ 10         │ in_port=p5, UDP 67/68, 53                 │ ALLOW          │
└────────────┴──────────────────────────────────────────┴────────────────┘
```

```text
PC-SA ── HTTPS ──► S1 (prioridad 150) ──► portal
Portal → IAM/AAA (paso 1: repositorio propio de identidades privilegiadas ·
      paso 2: TOTP) → Policy Engine (rol = SUPER_ADMIN, match B3)
Policy → Controlador → FLOW_MOD en S1
```

Después del login, el SA recibe la misma regla que el Administrador — alcance total sobre la gestión:

```text
S1 — sesión del SA
┌────────────┬──────────────────────────────────────────┬────────────────┐
│ Prioridad  │ Match                                     │ Acción         │
├────────────┼──────────────────────────────────────────┼────────────────┤
│ 200        │ in_port=p5, eth_src=B3, ip_dst=10.0.0.0/24│ ALLOW          │
│            │  (idle_timeout = sesión · cookie = sesión-SA)               │
└────────────┴──────────────────────────────────────────┴────────────────┘
```

La diferencia con el Administrador **no está en la tabla de flujos** — está en los permisos de la API (P24, P26) y en la auditoría: el SA es el único que registra Administradores y Superadministradores, modifica roles y toca la configuración global. La red le da el mismo alcance; los servicios le dan más poderes, registrándolos todos.

## 3. Escenario remoto: la variante exclusiva del SA

El SA puede autenticarse **sin estar en el campus** (fase A §2.5). A nivel de red esto significa que el tráfico llega desde el segmento externo, donde rige R5:

```text
SA remoto ──► Internet ──► PERÍMETRO (segmento externo, representado)
     │                          │
     │ HTTPS                    │ regla perimetral: solo 10.0.0.5:443
     ▼                          ▼
        ──► S3 ──► S2 ──► S1 ──► portal (10.0.0.5)
```

Reglas que hacen posible este camino **sin abrir la gestión al exterior**:

```text
Perímetro:  match ip_src=EXTERNO, ip_dst=10.0.0.5, tcp=443  → ALLOW
            match ip_src=EXTERNO, ip_dst=10.0.0.0/24         → DROP
S3/S2/S1:   match ip_dst=10.0.0.5, tcp=443 (desde el borde)  → ALLOW (prioridad 150)
            match ip_dst=10.0.0.0/24 (desde el borde)        → DROP  (prioridad 100)
```

El exterior solo alcanza el **portal**; nunca la consola, el controlador ni los switches. La elevación remota funciona igual que la local: el Policy Engine instala las reglas de sesión **en el switch del borde** (S3), no en un switch de acceso:

```text
S3 — sesión remota del SA (tras login en el portal)
┌────────────┬──────────────────────────────────────────┬────────────────┐
│ Prioridad  │ Match                                     │ Acción         │
├────────────┼──────────────────────────────────────────┼────────────────┤
│ 200        │ ip_src=IP_remota, ip_dst=10.0.0.0/24      │ ALLOW          │
│            │  (idle_timeout = sesión · cookie = sesión-SA-remota)        │
└────────────┴──────────────────────────────────────────┴────────────────┘
```

Detalle importante: la entrada remota matchea por **IP de origen** (no hay MAC del campus), con idle_timeout más corto y con el registro de la sesión remota marcado en la auditoría. Si la sesión remota se cierra, el exterior regresa a la única regla que tenía: el portal.

## 4. Comparación de los tres roles en la tabla de flujos

| Destino en gestión | TI | Administrador de Red | Superadministrador |
|---|---|---|---|
| Consola / APIs | ALLOW (entradas puntuales) | ALLOW (10.0.0.0/24) | ALLOW (10.0.0.0/24) |
| Controlador northbound | DROP | ALLOW | ALLOW |
| Switches (SSH/SNMP) | DROP | ALLOW | ALLOW |
| Acceso remoto | — | — | **Sí (solo portal → sesión en el borde)** |

El SA se distingue del Administrador por: acceso remoto, permisos globales (P24, P26) y la auditoría de todo lo anterior.

## 5. Cierre de sesión (local y remoto)

```text
Logout / inactividad ──► SessionClosed ──► FLOW_MOD DELETE (cookie)
                     ──► local:  S1 vuelve a BASE
                     ──► remoto:  S3 vuelve a "solo portal desde el exterior"
```

## 6. Lo que este flujo demuestra

- El rol de mayor privilegio **sigue siendo una sesión con expiración**: ni el SA tiene reglas permanentes (P10).
- El acceso remoto no debilita el perímetro: se abre el portal, nunca la gestión; la sesión remota se instala en el switch del borde con timeouts más cortos (P6, RA-09).
- Las diferencias entre los tres roles privilegiados quedan visibles en tres niveles: reglas de red (TI vs Admin/SA), permisos de API (Admin vs SA) y auditoría (todo).
