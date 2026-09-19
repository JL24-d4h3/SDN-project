# Recursos de red, servidores y servicios

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** A — Modelo de dominio
**Estado:** Borrador inicial — la delimitación de recursos requiere validación

---

## 1. Criterio de clasificación

**Recurso:** entidad con valor para la institución que el sistema debe proteger. Incluye servidores, datos, dispositivos, configuraciones y registros.

**Servicio:** recurso que se ofrece a un actor a través de la red. Un servicio es, por tanto, un recurso con consumidores identificables.

El nivel de protección se asigna según el impacto de su compromiso:

| Nivel | Significado | Equivalencia con R2.2 |
|---|---|---|
| **Crítico** | Su compromiso afecta a toda la red o a la autoridad del sistema. | Crítico |
| **Alto** | Contiene información sensible o habilita la operación de la red. | Privilegiado |
| **Medio** | Sirve a un grupo de usuarios; su caída degrada el servicio. | General |
| **Bajo** | Servicio de uso general, sin información sensible. | General |

---

## 2. Catálogo

### 2.1 Acceso y conectividad

| Recurso o servicio | Tipo | Descripción | Nivel |
|---|---|---|---|
| Intranet general | Servicio | Conectividad base y servicios institucionales de uso común. | Bajo |
| Acceso a Internet | Servicio | Salida a redes externas, si la arquitectura lo contempla. | Bajo |
| Segmentos de red (VLAN) | Recurso | Dominios de segmentación que separan poblaciones y recursos. | Alto |

### 2.2 Servicios y servidores institucionales

| Recurso o servicio | Tipo | Descripción | Nivel |
|---|---|---|---|
| Servicios públicos e institucionales | Servicio | Servicios abiertos a toda la comunidad. | Medio |
| Servicios y servidores académicos | Servicio | Plataformas de apoyo a la docencia y al estudio. | Medio |
| Recursos compartidos docentes | Servicio | Servidores y almacenamiento de uso docente. | Medio |
| Servidor de notas y sistemas de calificaciones | Servicio | Información académica sensible de los estudiantes. | Alto |
| Servicios administrativos | Servicio | Sistemas de gestión institucional. | Alto |
| Base de datos institucional | Recurso | Almacenamiento de la información de los servicios anteriores. | Crítico |

### 2.3 Infraestructura SDN

| Recurso o servicio | Tipo | Descripción | Nivel |
|---|---|---|---|
| Controlador SDN | Recurso | Plano de control; concentra las decisiones de la red. | Crítico |
| Consola de administración SDN | Servicio | Interfaz de gestión del controlador y de las políticas. | Crítico |
| Dispositivos de red (switches) | Recurso | Plano de datos; ejecutan las reglas instaladas. | Crítico |
| Reglas de flujo y configuración de segmentación | Recurso | Estado de forwarding y aislamiento vigente en la red. | Alto |

### 2.4 Seguridad y observabilidad

| Recurso o servicio | Tipo | Descripción | Nivel |
|---|---|---|---|
| Sistema IDS/IPS | Recurso | Detección y prevención de amenazas. | Crítico |
| Políticas de seguridad | Recurso | Reglas que definen el comportamiento permitido de la red. | Crítico |
| Consola de monitoreo | Servicio | Visualización de estado de red, eventos y alertas. | Alto |
| Logs de seguridad | Recurso | Registro de eventos y decisiones de seguridad. | Alto |
| Almacenamiento de registros | Recurso | Persistencia de logs para análisis e investigación. | Alto |
| Logs operativos | Recurso | Registro de operación y cambios administrativos. | Medio |

### 2.5 Identidad y control de acceso

| Recurso o servicio | Tipo | Descripción | Nivel |
|---|---|---|---|
| Credenciales y base de identidad | Recurso | Identidades de usuarios y su autenticación. | Crítico |
| Roles y permisos | Recurso | Definición de autorizaciones del sistema. | Crítico |
| Sesiones y estado de acceso | Recurso | Sesiones activas y estado de conexión de los usuarios. | Alto |

### 2.6 Dispositivos de usuario final

| Recurso o servicio | Tipo | Descripción | Nivel |
|---|---|---|---|
| Dispositivos de usuario | Recurso | Equipos que se conectan a la red; origen de los flujos. | Medio |

---

## 3. Recursos críticos

Los siguientes recursos concentran el mayor impacto y son los candidatos naturales a protección diferenciada (R2.8):

| Recurso | Nivel |
|---|---|
| Controlador SDN | Crítico |
| Consola de administración SDN | Crítico |
| Dispositivos de red | Crítico |
| Sistema IDS/IPS | Crítico |
| Políticas de seguridad | Crítico |
| Base de datos institucional | Crítico |
| Credenciales y base de identidad | Crítico |
| Roles y permisos | Crítico |
| Servidor de notas | Alto |
| Logs de seguridad | Alto |
| Segmentos de red (VLAN) | Alto |

---

## 4. Cuestiones abiertas

- **Frontera entre niveles.** El catálogo propone un nivel por recurso, pero la distinción exacta entre *medio* y *alto* —es decir, qué convierte a un recurso en privilegiado en el sentido de R2— todavía no está fijada.
- **Límite del sistema.** Si el firewall perimetral, el IDS/IPS y la base de identidad institucional forman parte de la solución o son sistemas externos con los que se integra es materia de la Fase C (límite del sistema). De esa decisión depende si se clasifican como recursos propios o como dependencias.
- **Dispositivos de usuario final.** Definir si son recursos protegidos o únicamente orígenes de tráfico sujetos a observación.
- **Red inalámbrica y red de invitados.** Confirmar si están dentro del alcance del prototipo.
- **Retención de registros.** Dónde se almacenan los logs y por cuánto tiempo.
- **Servicios administrativos.** Confirmar qué rol los consume (ver la cuestión abierta sobre *personal administrativo* en [`01_actores-roles_y_agentes.md`](01_actores-roles_y_agentes.md)).

---

La matriz Actor → Recurso se construye sobre este catálogo y se documenta en `03_permisos.md`.
