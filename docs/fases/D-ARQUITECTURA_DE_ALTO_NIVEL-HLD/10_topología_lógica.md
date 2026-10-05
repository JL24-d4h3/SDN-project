# Topología lógica

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** D — Arquitectura de alto nivel (HLD)
**Estado:** Borrador formal para revisión

---

La topología lógica de referencia: los segmentos, el direccionamiento propuesto y el despliegue del prototipo. Es una **propuesta de referencia** — la definición definitiva de segmentación pertenece a la Fase H; aquí se fija la estructura mínima que los flujos (doc 12) necesitan.

## 1. Segmentos de referencia

| Segmento | Población | Propósito | Protección |
|---|---|---|---|
| **Acceso académico** | Usuarios académicos (BASE; ACADÉMICO tras el login) | Conectividad de consumo: en BASE, DHCP, DNS y portal; tras el login, servicios académicos e Internet | Perfil BASE + deny by default |
| **Servidores** | Servicios institucionales y académicos | Alojar los activos protegidos (R2) | Acceso según política; objetivo de R3/R4 |
| **Administración y gestión** | Controlador, servicios de la plataforma, consolas de operadores | Sostener el plano de control y de gestión | Solo operadores autenticados (RA-09) |
| **Perimetral** | Borde con redes externas | Punto de aplicación de R5 | Por definir (fase C) |

El canal de control (OpenFlow) usa una **red de gestión separada** (out-of-band); la variante in-band lo llevaría a una VLAN dedicada sobre los enlaces de datos (serie de flujo, parte 2).

## 2. Diagrama lógico

```text
                       ┌──────────────────────────────┐
                       │  SERVIDOR DE CONTROL         │
                       │  controlador SDN + servicios │
                       │  (plano de control y gestión)│
                       └──────────────┬───────────────┘
                                      │ canal de control out-of-band
             ┌────────────────────────┼────────────────────────┐
             │                        │                        │
      ┌──────┴──────┐          ┌──────┴──────┐          ┌──────┴──────┐
      │  SWITCH S1  │──────────│  SWITCH S2  │──────────│  SWITCH S3  │
      └──┬───────┬──┘          └──────┬──────┘          └──────┬──────┘
         │       │                    │                        │
    ┌────┴───┐   └─────────┐   ┌──────┴─────┐            ┌─────┴─────┐
    │ HostA  │  HostB      │   │  HostC     │            │  SRV-1    │
    │(académ.│  (académ.   │   │ (atacante  │            │ (servidor │
    │  p1)   │   p2)       │   │ controlado)│            │ protegido)│
    └────────┘             │   └────────────┘            └───────────┘
                     ┌─────┴──────────────┐
                     │  SRV-DHCP/DNS      │
                     │  (servicios base)  │
                     └────────────────────┘
```

- Los **hosts académicos** se conectan a puertos de acceso; reciben perfil BASE; tras el login en el portal, el perfil ACADÉMICO (o la sesión de rol, si son operadores).
- El **host atacante** es tráfico controlado dentro del entorno (RP-06, RP-08): se conecta como un académico más y genera el tráfico de ataque de R3/R4.
- **SRV-1** representa el activo protegido (destino de R2 y de los ataques).
- Los **servicios base** (DHCP/DNS) sirven al flujo de arranque (serie de flujo, parte 2).

### 2.1 Los tres niveles de la referencia

La topología de referencia se organiza en **tres niveles**:

```text
        ACCESO                 DISTRIBUCIÓN                NÚCLEO
   ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
   │  switches    │        │  switches    │        │  switches    │
   │  de acceso   │────────│  de distribu-│────────│  de núcleo   │──── servicios
   │              │        │  ción        │        │              │     (portal · DHCP/DNS ·
   └──────┬───────┘        └──────────────┘        └──────────────┘      servidores)
          │
       hosts
   (BASE · ACADÉMICO)
```

- **Acceso** — donde se conectan los dispositivos; aloja la política: perfil BASE, escalera de prioridades, anti-spoofing y portal.
- **Distribución** — agregación: une los accesos entre sí y con el núcleo; es el ámbito natural de los caminos.
- **Núcleo** — la troncal: conecta los servicios de infraestructura y los caminos principales.

Cuántos switches tiene cada nivel, cómo se conectan y qué redundancia existe quedó fijado en la Fase H: **ocho switches — dos núcleo, dos distribución, cuatro acceso — dual-homed, con 13 enlaces** ([`H-01`](../H-Despliegue/01_infraestructura_fisica.md) §3). El diagrama de arriba es la vista de niveles; las cantidades y los enlaces concretos viven en la Fase H. El cálculo de caminos por destino que opera sobre estos niveles está en la serie de flujo, parte 5.

## 3. Direccionamiento propuesto

| Segmento | Subred propuesta | Nota |
|---|---|---|
| Acceso académico | 10.1.0.0/24 | Hosts con IP estática en el prototipo; el controlador aprende MAC/IP/puerto |
| Servidores | 10.2.0.0/24 | SRV-1 y servicios institucionales |
| Administración y gestión | 10.0.0.0/24 | Controlador y servicios; inalcanzable desde BASE |
| Canal de control (out-of-band) | red de gestión propia | Separada de las anteriores |

El direccionamiento definitivo del prototipo quedó fijado en la Fase H ([`H-03`](../H-Despliegue/03_red.md)); el diseño de reglas usa rangos por segmento (`ip_dst = 10.0.0.0/24` para denegar la gestión), no direcciones sueltas.

## 4. El prototipo: qué se despliega

| Elemento | Despliegue en el prototipo | Referencia |
|---|---|---|
| Controlador SDN | Se despliega (servidor de control) | Decisión tecnológica: Fase F |
| Switches | Se despliegan (Pica8/PicOS, virtuales o físicos) | RP-11 |
| Servicios de la plataforma | Se despliegan consolidados en el servidor de control | doc 04 §6, RP-04 |
| Hosts académicos | Se simulan (mínimo 2, para demostrar tráfico entre pares) | C-04 |
| Servidor protegido (SRV-1) | Se simula | Activo protegido |
| Servicios base (DHCP/DNS) | Del propio entorno virtual | C-04 |
| Host atacante | Se simula, tráfico controlado | RP-06, RP-08 |
| Segmento externo | Se representa | C-04 |

La topología rígida admite la aparición de dispositivos nuevos: todo lo que conecte y no esté en el registro privilegiado recibe perfil BASE (P5, P7).

## 5. Lo que esta topología garantiza

- **R1/R2 demostrables:** los DROP hacia 10.0.0.0/24 desde el segmento académico son medibles con contadores.
- **R3/R4 demostrables:** el host atacante y los académicos comparten el segmento; el ataque hacia SRV-1 recorre el camino real del plano de datos y la mitigación se instala en el switch de ingreso (P9).
- **Observación completa:** cada flujo relevante pasa por un switch con contadores (P11).

## 6. Cuestiones abiertas

- **Número de switches por nivel, conexiones y resiliencia** — cerrado en la Fase H: ocho switches dual-homed ([`H-01`](../H-Despliegue/01_infraestructura_fisica.md)); el efecto de un fallo sobre los caminos instalados se resuelve con recálculo o grupos fast-failover ([`G-06`](../G-Diseno_de_bajo_nivel-LLD/06_reglas.md) §4).
- **Hardware físico vs virtual.** La topología lógica es la misma; cambia el despliegue (Fase H).
- **Perímetro.** Si el segmento perimetral se representa con un firewall, con reglas de borde o no se representa (fase C).
- **In-band.** Si el canal de control adopta la VLAN de gestión sobre los enlaces de datos.
