# Límite del sistema

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** C — Contexto
**Estado:** Borrador formal para revisión

---

## 1. Qué es el sistema

El sistema es la **plataforma SDN de seguridad**: el conjunto de mecanismos que controla el acceso a la red, autoriza el uso de recursos, detecta y mitiga amenazas, y administra y registra esas decisiones, junto con la infraestructura SDN sobre la que se aplican.

El sistema no es la red del campus. Es la capa que decide qué ocurre en ella.

---

## 2. Criterio de delimitación

Un elemento pertenece al sistema si el proyecto lo despliega, lo configura y responde por él. Si existe con independencia del proyecto y el sistema solo intercambia información con él, queda fuera.

De ese criterio resultan cuatro categorías:

| Categoría | Definición |
|---|---|
| **Parte del sistema** | El proyecto lo despliega y lo opera; las decisiones de seguridad se aplican sobre él. |
| **Activo protegido** | Está fuera del sistema, pero es el objeto que el sistema protege. |
| **Sistema externo** | Existe con independencia del proyecto; el sistema se integra con él mediante una interfaz. |
| **Fuente de amenaza** | No coopera con el sistema: origina el tráfico o el comportamiento que debe detectarse y contenerse. |

---

## 3. Elementos en el límite

| Elemento | Categoría | Justificación |
|---|---|---|
| Controlador SDN | Parte del sistema | Es el plano de control; el proyecto lo despliega y lo configura. |
| Aplicaciones de seguridad (autorización, detección, mitigación, administración) | Parte del sistema | Implementan las decisiones que definen R1–R5. |
| Dispositivos SDN administrados | Parte del sistema | Ejecutan las reglas que el plano de control instala. |
| Consola de administración | Parte del sistema | Interfaz de operación de la plataforma. |
| Registros y almacenamiento de logs | Parte del sistema | Sostienen la trazabilidad exigida por R1.9, R2.9 y RNF-09. |
| Sistema de identidad institucional | Sistema externo | El sistema lo consulta para autenticar; no lo administra. |
| Firewall perimetral | Sistema externo o parte del sistema | **Por definir**: si el proyecto lo despliega, es parte del sistema; si ya existe, es un punto de integración. |
| IDS/IPS | Parte del sistema o sistema externo | **Por definir**: determina si la detección es propia o se consume de un servicio institucional. |
| Servidores y servicios institucionales | Activo protegido | El sistema no los administra: los protege. |
| Dispositivos de usuario final | Activo protegido | Están fuera del sistema, pero son el origen del tráfico que se controla y el punto donde puede aplicarse un aislamiento. |
| Internet y redes externas | Sistema externo y fuente de amenaza | Es a la vez origen de tráfico legítimo y de tráfico malicioso (R5). |
| Atacante externo, atacante interno y nodo comprometido | Fuente de amenaza | No cooperan con el sistema; su comportamiento es el objeto de R3–R5. |

---

## 4. Consecuencias de esta delimitación

- **R1 y R2 dependen de un sistema externo de identidad.** La autenticación no es propia; la autorización sí. La frontera está entre *quién es* el usuario y *qué puede hacer*.
- **R5 se satisface en el borde.** Si el firewall es externo, la solución debe integrarse con él, no sustituirlo.
- **Los activos protegidos quedan fuera del sistema pero dentro de su alcance de protección.** Al protegerlos, el sistema aplica políticas sobre la red que los conecta, no sobre los servidores mismos.
- **Un atacante no es un elemento del sistema ni un usuario de él.** Es una fuente de tráfico que el sistema observa, clasifica y contiene.

---

## 5. Cuestiones abiertas

- Ubicación del firewall y del IDS/IPS: propios o institucionales. Determina si son componentes del sistema o interfaces con sistemas externos.
- Si el sistema de identidad institucional existe en el entorno del prototipo o debe simularse (ver [`04_alcance_de_la_infraestructura.md`](04_alcance_de_la_infraestructura.md)).
- Si la consola de administración y el almacenamiento de registros forman parte del prototipo o se representan de forma simplificada.
