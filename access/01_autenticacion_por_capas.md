# Autenticación por capas

**Proyecto:** Solución de seguridad para una red de campus académico
**Serie:** Control de acceso — 1
**Estado:** Borrador formal para revisión

---

Dónde vive cada protocolo y servicio asociado a la autenticación en el modelo de capas: qué se negocia en aplicación, qué en el enlace, y por qué en red no hay nada. Incluye la posición de **EAPOL/802.1X** en el diseño. Complementa a [`01_autenticacion.md`](../docs/componentes/01_autenticacion.md) §7 (tecnología decidida) y [`04_identidades_y_poblaciones.md`](../docs/componentes/04_identidades_y_poblaciones.md). El flujo completo, mensaje a mensaje, está en [`plan/auth`](../plan/auth/v1_flujo_por_capas.md).

## 1. La pila de la autenticación

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ CAPA 7 · APLICACIÓN — aquí vive casi toda la autenticación                 │
│                                                                            │
│   identidad de la persona (I3/I4)                                          │
│     HTTPS ......... portal cautivo: credenciales y sesión                  │
│     RADIUS ........ AAA contra el IdP (UDP 1812/1813)                      │
│     LDAP(S) ....... directorio del IdP — detrás de RADIUS                  │
│     TOTP .......... 2.º factor de operadores                               │
│                                                                            │
│   soporte del estado pre-sesión (BASE)                                     │
│     DHCP .......... dirección para poder llegar al portal                  │
│     DNS ........... nombre del portal                                      │
├────────────────────────────────────────────────────────────────────────────┤
│ CAPA 5/6 · SESIÓN/PRESENTACIÓN                                             │
│     TLS ........... dentro de HTTPS (I3) y LDAPS (I4): confidencialidad    │
│                     en tránsito; no autentica personas por sí solo         │
├────────────────────────────────────────────────────────────────────────────┤
│ CAPA 4 · TRANSPORTE — no autentica: solo entrega                           │
│     TCP 443 HTTPS · TCP 389/636 LDAP(S)                                    │
│     UDP 1812/1813 RADIUS · UDP 67/68 DHCP · UDP 53 DNS                     │
├────────────────────────────────────────────────────────────────────────────┤
│ CAPA 3 · RED — sin protocolo de autenticación                              │
│     IP: localizador, jamás credencial. El par MAC/IP aprendido se usa      │
│     para anti-spoofing (match ip_src en las reglas), no para autenticar    │
├────────────────────────────────────────────────────────────────────────────┤
│ CAPA 2 · ENLACE — el único protocolo de autenticación de enlace            │
│                                                                            │
│     EAPOL / 802.1X — autentica el PUERTO antes de que exista IP:           │
│                                                                            │
│       suplicante ──EAPOL──► switch (autenticador) ──EAP/RADIUS──► IdP      │
│       (el cliente)          (no abre el puerto      (el que sabe)          │
│                             hasta el veredicto)                            │
│                                                                            │
│       dentro viajan los métodos EAP (EAP-TLS, PEAP, EAP-TTLS…)             │
│       no en el prototipo — puertos sensibles del despliegue real           │
│                                                                            │
│     MAB (por MAC) — variante de compatibilidad sin suplicante:             │
│       el switch usa la MAC como usuario/contraseña; débil por definición   │
│     MAC — atributo y clave de correlación (MAC_MOVE), no credencial        │
├────────────────────────────────────────────────────────────────────────────┤
│ CAPA 1 · FÍSICA                                                            │
│     presencia física (conectar el cable) → perfil BASE (RP-13)             │
└────────────────────────────────────────────────────────────────────────────┘
```

## 2. El conteo

| Capa | Protocolos/servicios asociados | Cuántos |
|---|---|---|
| **7 · Aplicación** | HTTPS, RADIUS, LDAP(S), TOTP, DHCP, DNS | **6** |
| 5/6 · Sesión/Presentación | TLS (soporte, no autenticación por sí solo) | 1 de soporte |
| 4 · Transporte | ninguno propio (solo puertos que entregan) | 0 |
| **3 · Red** | ninguno — IP solo localiza | **0** |
| **2 · Enlace** | EAPOL/802.1X (+MAB como variante); MAC como atributo | **1** |
| 1 · Física | presencia (no es protocolo) | — |

Lectura del conteo: **casi toda la autenticación vive en aplicación** (los 6); en **enlace hay exactamente uno** —EAPOL/802.1X, solo para puertos sensibles—; en **red no hay ninguno**: la dirección IP es un localizador, no una identidad.

## 3. ¿Se está considerando EAPOL? — No en el prototipo; reservado a puertos sensibles

- **Qué es:** 802.1X es la autenticación por puerto de capa 2; **EAPOL** es el protocolo que la transporta entre el suplicante y el switch; los métodos **EAP** (EAP-TLS, PEAP…) viajan dentro. Su fuerza: autentica **antes de dar IP** — el puerto nace cerrado y solo se abre con el veredicto. Radiografía:

```text
   suplicante            switch                    servidor
   (cliente 802.1X)      (autenticador)            (RADIUS → IdP)
        │  EAPOL            │                          │
        │──────────────────►│  EAP encapsulado         │
        │                   │─────────────────────────►│  valida contra
        │                   │◄─────────────────────────│  el directorio
        │◄──────────────────│  veredicto               │
        │  puerto ABIERTO   │  (o sigue cerrado)       │
```

- **Por qué no es el mecanismo principal:** exige un **suplicante** en cada dispositivo (cliente/configuración 802.1X que no todos los equipos traen listos). El portal cautivo, en cambio, funciona con cualquier equipo que tenga navegador — el caso real del campus.
- **Dónde sí:** **puertos sensibles** (cuartos de comunicaciones, gabinetes, puertos de infraestructura), donde el equipo conectado es controlado y vale la pena cerrar el puerto antes de IP. **MAB** cubre a los equipos sin suplicante, asumiendo su debilidad (la MAC se falsifica).
- **Relación con el modelo:** 802.1X ocurriría **antes** del portal y de DHCP: cambiaría el punto donde nace la identidad (enlace en vez de aplicación), no el resto — la decisión sigue siendo del Policy Engine y la ejecución del switch.

## 4. Nota: el enforcement cruza capas (no es la pila del usuario)

Las reglas que resultan de un login se ejecutan en el switch matcheando campos de **varias capas** a la vez — `eth_src` (enlace), `ip_src` (red), puerto TCP/UDP (transporte) — y el canal que las instala (OpenFlow, controlador ↔ switches, TCP 6653) es el **plano de control**, no un protocolo de autenticación del usuario: la autenticación es de aplicación; la ejecución es la escalera de flujos ([doc 02](../docs/componentes/02_autorizacion.md) §6).