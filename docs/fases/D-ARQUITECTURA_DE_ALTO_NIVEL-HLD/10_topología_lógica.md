# Topología lógica

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** D — Arquitectura de alto nivel (HLD)
**Estado:** Borrador formal para revisión

---

La topología lógica de referencia: los segmentos, el direccionamiento propuesto y el despliegue del prototipo. Es una **propuesta de referencia** — la definición definitiva de segmentación pertenece a la Fase H; aquí se fija la estructura mínima que los flujos (doc 12) necesitan.

## 1. Segmentos de referencia

| Segmento | Población | Propósito | Protección |
|---|---|---|---|
| **Acceso académico** | Usuarios académicos (perfil BASE) | Conectividad de consumo: DHCP, DNS, servicios académicos, Internet | Perfil BASE + deny by default |
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

- Los **hosts académicos** se conectan a puertos de acceso; reciben perfil BASE.
- El **host atacante** es tráfico controlado dentro del entorno (RP-06, RP-08): se conecta como un académico más y genera el tráfico de ataque de R3/R4.
- **SRV-1** representa el activo protegido (destino de R2 y de los ataques).
- Los **servicios base** (DHCP/DNS) sirven al flujo de arranque (serie de flujo, parte 2).

## 3. Direccionamiento propuesto

| Segmento | Subred propuesta | Nota |
|---|---|---|
| Acceso académico | 10.0.1.0/24 | Hosts con DHCP; el controlador aprende MAC/IP/puerto |
| Servidores | 10.0.2.0/24 | SRV-1 y servicios institucionales |
| Administración y gestión | 10.0.0.0/24 | Controlador y servicios; inalcanzable desde BASE |
| Canal de control (out-of-band) | red de gestión propia | Separada de las anteriores |

El direccionamiento es una propuesta de trabajo: el diseño de reglas usa rangos por segmento (`ip_dst = 10.0.0.0/24` para denegar la gestión), no direcciones sueltas.

## 4. El prototipo: qué se despliega

| Elemento | Despliegue en el prototipo | Referencia |
|---|---|---|
| Controlador SDN | Se despliega (servidor de control) | Decisión tecnológica: Fase G |
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

- **Número exacto de switches y hosts** (3 switches y 3–4 hosts es el mínimo propuesto; depende de la capacidad del laboratorio).
- **Hardware físico vs virtual.** La topología lógica es la misma; cambia el despliegue (Fase H).
- **Perímetro.** Si el segmento perimetral se representa con un firewall, con reglas de borde o no se representa (fase C).
- **In-band.** Si el canal de control adopta la VLAN de gestión sobre los enlaces de datos.
