# Recursos de red, servidores y servicios

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** A — Modelo de dominio
**Estado:** Borrador formal para revisión

---

## 1. Criterio de clasificación

**Recurso:** entidad con valor para la institución que el sistema debe proteger. Incluye servidores, datos, dispositivos, configuraciones y registros.

**Servicio:** recurso que se ofrece a un actor a través de la red. Un servicio es, por tanto, un recurso con consumidores identificables.

El catálogo se organiza en **tres clases de destino** —según quién los consume y qué privilegio exigen— y cada recurso recibe además un nivel de protección según el impacto de su compromiso:

| Clase de destino | Definición |
|---|---|
| **Recursos de usuario** | Servicios que consume el usuario académico con su perfil ACADÉMICO tras autenticarse: servicios académicos e Internet. Ninguno es alcanzable en BASE: allí solo existe la habilitación mínima del dispositivo (DHCP, DNS y portal). |
| **Recursos restringidos** | Servicios que exigen una elevación aprobada: laboratorios, repositorios e investigación. |
| **Infraestructura** | Los componentes que sostienen la propia solución: plano de control, gestión de identidad y observabilidad. El usuario académico tiene el acceso denegado por defecto. |

| Nivel | Significado | Equivalencia con R2.2 |
|---|---|---|
| **Crítico** | Su compromiso afecta a toda la red o a la autoridad del sistema. | Crítico |
| **Alto** | Contiene información sensible o habilita la operación de la red. | Privilegiado |
| **Medio** | Sirve a un grupo de usuarios; su caída degrada el servicio. | General |
| **Bajo** | Servicio de uso general, sin información sensible. | General |

---

## 2. Catálogo

### 2.1 Recursos de usuario

| Recurso o servicio | Tipo | Descripción | Nivel |
|---|---|---|---|
| Conectividad base del dispositivo | Servicio | Habilitación inicial del perfil BASE, como lista cerrada: DHCP, ARP y el segmento de acceso. No da acceso a los servicios de la intranet — eso lo decide la autenticación. | Bajo |
| Acceso a Internet | Servicio | Salida a redes externas, si la arquitectura lo contempla. | Bajo |
| Resolución de nombres (DNS) | Servicio | Servicio de nombres; forma parte de la lista cerrada del perfil BASE. | Bajo |
| Servicios públicos e institucionales | Servicio | Servicios abiertos a toda la comunidad autenticada. | Medio |
| Servicios y servidores académicos | Servicio | Plataformas de apoyo a la docencia y al estudio (LMS y equivalentes) y otros recursos de la universidad, como la nube privada. | Medio |
| Servicios administrativos | Servicio | Sistemas de gestión institucional. | Alto |
| Base de datos institucional | Recurso | Almacenamiento de la información de los servicios anteriores. | Crítico |

### 2.2 Recursos restringidos

| Recurso o servicio | Tipo | Descripción | Nivel |
|---|---|---|---|
| Repositorios y recursos de investigación | Servicio | Repositorios especiales y recursos de los grupos de investigación. | Alto |
| Servicios técnicos internos | Servicio | Servicios internos no disponibles para el perfil BASE. | Alto |

### 2.3 Infraestructura

| Recurso o servicio | Tipo | Descripción | Nivel |
|---|---|---|---|
| Controlador SDN | Recurso | Plano de control; concentra las decisiones de la red. | Crítico |
| Consola de administración SDN | Servicio | Interfaz de gestión del controlador y de las políticas. | Crítico |
| Dispositivos de red (switches) | Recurso | Plano de datos; ejecutan las reglas instaladas. | Crítico |
| Reglas de flujo y configuración de segmentación | Recurso | Estado de forwarding y aislamiento vigente en la red. | Alto |
| Segmentos de red (VLAN) | Recurso | Dominios de segmentación que separan poblaciones y recursos. | Alto |
| Canal de control (red de gestión) | Recurso | Conectividad entre controlador y switches; out-of-band, con la variante in-band como objetivo (ver flujo §2.6). | Crítico |

### 2.4 Seguridad y observabilidad

| Recurso o servicio | Tipo | Descripción | Nivel |
|---|---|---|---|
| Monitor | Recurso | Recopila counters y estadísticas del plano de datos. | Alto |
| Detection Engine | Recurso | Determina si existe comportamiento anómalo (R3, R4): la función de detección interna (IDS); la mitigación (función IPS) la ejecutan Policy Engine y controlador. El IDS/IPS perimetral de R5.2 es evaluación tecnológica. | Crítico |
| Incident Manager | Recurso | Registra y gestiona los incidentes de seguridad. | Alto |
| Policy Engine | Recurso | Decide la respuesta ante incidentes y solicitudes de elevación. | Crítico |
| Políticas de seguridad | Recurso | Reglas que definen el comportamiento permitido de la red. | Crítico |
| Consola de monitoreo | Servicio | Visualización de estado de red, eventos y alertas. | Alto |
| Logs de seguridad | Recurso | Registro de eventos y decisiones de seguridad. | Alto |
| Almacenamiento de registros | Recurso | Persistencia de logs para análisis e investigación. | Alto |
| Logs operativos | Recurso | Registro de operación y cambios administrativos. | Medio |

### 2.5 Identidad y control de acceso

| Recurso o servicio | Tipo | Descripción | Nivel |
|---|---|---|---|
| Perfiles de acceso | Recurso | Definición de los perfiles (BASE, ACADÉMICO, LABORATORIO, INVESTIGACIÓN, TI, ADMIN_RED, SUPER_ADMIN) y sus reglas de red asociadas. | Crítico |
| Registro de dispositivos privilegiados | Recurso | Base de datos de los dispositivos de operadores (MAC, tipo, titular, rol, vigencia, responsable). Solo los dispositivos privilegiados se registran; lo que no hace match recibe perfil BASE. Sirve además de auditoría del alta de dispositivos. | Crítico |
| AAA / RADIUS | Recurso | Autenticación, autorización y accounting de las poblaciones: la comunidad (contra el IdP) y los operadores (contra el repositorio propio). No cataloga dispositivos: autentica personas. | Crítico |
| Portal cautivo | Servicio | Punto de autenticación de la red: la comunidad obtiene el perfil ACADÉMICO; los operadores, su sesión de rol. | Alto |
| Sistema de identidad institucional (IdP/LDAP) | Recurso externo | Backend de identidad consultado por AAA; no lo administra el proyecto. | Crítico |
| Roles y permisos | Recurso | Definición de autorizaciones del sistema. | Crítico |
| Sesiones y estado de acceso | Recurso | Sesiones activas, perfiles vigentes y su TTL. | Alto |

### 2.6 Dispositivos de usuario final

| Recurso o servicio | Tipo | Descripción | Nivel |
|---|---|---|---|
| Dispositivos de usuario | Recurso | Equipos que se conectan a la red; origen de los flujos. Los académicos no se registran; los de operadores figuran en el registro de dispositivos privilegiados. | Medio |

---

## 3. Recursos críticos

Los siguientes recursos concentran el mayor impacto y son los candidatos naturales a protección diferenciada (R2.8):

| Recurso | Nivel |
|---|---|
| Controlador SDN | Crítico |
| Consola de administración SDN | Crítico |
| Dispositivos de red | Crítico |
| Canal de control | Crítico |
| Detection Engine | Crítico |
| Policy Engine | Crítico |
| Políticas de seguridad | Crítico |
| Base de datos institucional | Crítico |
| Registro de dispositivos privilegiados | Crítico |
| AAA / RADIUS | Crítico |
| Sistema de identidad institucional | Crítico |
| Perfiles de acceso | Crítico |
| Roles y permisos | Crítico |
| Logs de seguridad | Alto |
| Segmentos de red (VLAN) | Alto |

---

## 4. Cuestiones abiertas

- **Frontera entre niveles.** La distinción exacta entre *medio* y *alto* —es decir, qué convierte a un recurso en privilegiado en el sentido de R2— todavía no está fijada.
- **Límite del sistema.** Si el firewall perimetral es parte de la solución o un sistema externo es materia de la Fase C. La cadena de detección (Monitor, Detection, Incident, Policy) sí es parte del sistema; el IdP institucional es externo.
- **Dispositivos de usuario final.** Definir si son recursos protegidos o únicamente orígenes de tráfico sujetos a observación.
- **Red inalámbrica y red de invitados.** Confirmar si están dentro del alcance del prototipo.
- **Retención de registros.** Dónde se almacenan los logs y por cuánto tiempo.
- **Acceso remoto.** Definir la política de acceso remoto de los operadores (contemplado para el Superadministrador).

---

La matriz Actor → Recurso se construye sobre este catálogo y se documenta en `03_permisos.md`.
