# Planos y capas

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** D — Arquitectura de alto nivel (HLD)
**Estado:** Borrador formal para revisión

---

Este documento distingue dos organizaciones que conviene no confundir: los **planos SDN** (dónde vive cada función respecto de la red) y las **capas** del estilo arquitectónico (cómo se organiza el software, doc 01). La superposición de ambas es el mapa completo del sistema.

## 1. Los tres planos SDN

| Plano | Función | Componentes |
|---|---|---|
| **Plano de datos** | Reenviar, descartar, limitar y medir el tráfico, según las reglas instaladas. | Switches (pipeline, groups, meters, contadores), hosts, servidores protegidos. |
| **Plano de control** | Mantener el conocimiento de la red y traducir decisiones a reglas. | Controlador SDN. |
| **Plano de gestión** | Definir políticas, observar, decidir y administrar; el cerebro de la seguridad. | Servicios de la plataforma (IAM, Registro, Monitor, Detección, Incidentes, Políticas, Auditoría), consola y portal. |

La separación de planos es P1: el plano de datos ejecuta, el de control traduce, el de gestión decide. Ningún componente cruza su plano: los servicios no hablan OpenFlow; los switches no deciden; el controlador no define políticas.

## 2. Las cinco capas del estilo

Las capas (doc 01, §3.1) organizan el software de arriba hacia abajo según la distancia al problema de red:

| Capa | Contenido |
|---|---|
| **Interacción** | Consola de administración, portal cautivo, northbound API. |
| **Aplicación** | IAM/AAA, Registro de dispositivos, gestión de incidentes, monitoreo. |
| **Seguridad** | Detección, políticas y decisión (Monitor, Detection, Incident, Policy). |
| **Control SDN** | Controlador SDN. |
| **Infraestructura** | Switches, hosts, servidores protegidos. |

La regla de dependencia entre capas: **cada capa depende solo de la inmediatamente inferior**, con una excepción explícita — los eventos cruzan capas a través del broker, sin crear dependencia directa (P13).

## 3. Superposición: capas × planos

```text
                     PLANO DE           PLANO DE          PLANO DE
                     GESTIÓN            CONTROL           DATOS
                ┌──────────────┐
 Interacción   │ Consola ·    │
               │ Portal · API │
               ├──────────────┤
 Aplicación    │ IAM · Regis- │
               │ tro · Inci-  │
               │ dentes ·     │
               │ Monitoreo    │
               ├──────────────┤
 Seguridad     │ Detección ·  │
               │ Políticas ·  │
               │ Decisión     │
               └──────┬───────┘
                      │ northbound
               ┌──────▼───────┐
 Control SDN   │ Controlador  │
               └──────┬───────┘
                      │ OpenFlow (canal de control)
               ┌──────▼───────┐
 Infraestructura│  Switches   │────────────► hosts y
               │  (pipeline)  │              servidores
               └──────────────┘
```

- Las tres capas superiores viven íntegramente en el **plano de gestión**.
- La capa de control SDN **es** el plano de control.
- La capa de infraestructura **es** el plano de datos (con los activos protegidos y los hosts).
- El tráfico de usuario cruza solo el plano de datos; las decisiones cruzan de gestión a control a datos; la observación sube en sentido inverso.

## 4. Por qué la separación gestión/control importa aquí

En SDN es común hablar solo de "plano de control y plano de datos", con las aplicaciones dentro del control. En esta solución, la plataforma de seguridad es demasiado grande para eso: tiene autenticación, registro, incidentes y auditoría que **no son** funciones de control de red. Separar el plano de gestión del plano de control:

- hace explícito que las aplicaciones **no tocan los switches** (P1) y que el controlador no define políticas (P8);
- permite desplegar los servicios como microservicios (doc 04) sin tocar el controlador;
- alinea la protección del plano de control (RA-09): solo el controlador y los operadores autenticados alcanzan la red de gestión; los servicios hablan con el controlador por la northbound API, no por el canal de datos.

## 5. La realización física de los planos

- **Plano de datos:** la red del campus del prototipo (tráfico de hosts y servidores).
- **Plano de control:** el canal OpenFlow por la **red de gestión out-of-band** (RP-11; variante in-band en la serie de flujo, parte 2).
- **Plano de gestión:** el servidor de control que aloja los servicios y la consola, alcanzable solo por operadores autenticados (RA-09).

La topología lógica que materializa estos planos está en [`10_topología_lógica.md`](10_topología_lógica.md).

## 6. Cuestiones abiertas

- **Ubicación de la consola.** Si la consola vive en la red de gestión (solo operadores) o es alcanzable desde la red académica con autenticación — la primera opción es la coherente con RA-09; decidir en Fase H.
- **In-band.** Si el canal de control comparte la infraestructura de datos (VLAN de gestión), los planos de datos y control comparten enlaces físicos aunque sigan lógicamente separados.
