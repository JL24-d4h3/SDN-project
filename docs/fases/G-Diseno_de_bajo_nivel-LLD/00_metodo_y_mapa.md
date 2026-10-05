# Método y mapa del LLD

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** G — Diseño de bajo nivel (LLD)
**Estado:** Borrador formal para revisión

---

La Fase D fijó **qué componentes existen y qué contrato los une**; la Fase F eligió **con qué tecnología se materializan**; esta fase escribe **cómo queda cada artefacto**: esquemas de datos definitivos, contratos de eventos al detalle de campo, estructura interna de cada servicio y configuración del pipeline del switch — exactamente lo que [`F-09`](../F-Decisiones_tecnologicas/09_sintesis_y_trazabilidad.md) §5 dejó para esta fase. Nada de lo escrito aquí cambia un contrato de D ni una decisión de F: los implementa.

## 1. La regla de lectura: de lo general a lo particular

Cada documento de esta fase respeta la misma estructura: abre con **el concepto general** —la familia de artefactos, su papel en el sistema, la jerarquía que lo ordena— y recién después baja al **detalle particular** —el endpoint, el campo, el valor—. El detalle no sustituye al concepto: lo aterriza. Primero la sesión como forma del SSO del operador; después, que la sesión es una cookie opaca ligada al dispositivo.

| Documento | Lo general | Lo particular |
|---|---|---|
| [`01`](01_apis.md) | La API como frontera síncrona del sistema: dos familias, I2 e I7 | Endpoints y esquemas JSON campo a campo |
| [`02`](02_eventos.md) | El bus como frontera asíncrona: el evento informa, el comando ejecuta | Catálogo de eventos al detalle de campo, enrutamiento y colas |
| [`03`](03_datos.md) | Un repositorio por servicio; tres clases de dato; correlación por identificadores | Esquema de cada base, tabla a tabla |
| [`04`](04_interfaces.md) | I1–I8 como los contratos entre componentes | La forma operativa de las interfaces que no son HTTP |
| [`05`](05_configuraciones.md) | Configuración como estado declarado y versionado; dos clases | Parámetro por parámetro, producto por producto |
| [`06`](06_reglas.md) | La jerarquía de prioridades como jerarquía de autoridad | El pipeline del switch, entrada a entrada |
| [`07`](07_detalles_de_implementacion.md) | Cada servicio: una responsabilidad, un ciclo de vida, una estructura en capas | Módulos y pseudocódigo de los bucles críticos |

## 2. Invariantes de esta fase

- **Los contratos de D** ([`07_interfaces_principales.md`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/07_interfaces_principales.md) y [`08_comunicacion.md`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/08_comunicacion.md)): separación síncrono/asíncrono, frontera de secretos, catálogo de eventos, reglas de confianza.
- **Las decisiones de F** ([`00`](../F-Decisiones_tecnologicas/00_metodo_de_decision.md)): productos, mecanismos y valores iniciales. El LLD detalla; si un detalle obligara a contradecir una decisión, se reabre la decisión en F — no se ajusta en silencio aquí.
- **La frontera de P12:** los valores numéricos de esta fase son iniciales y configurables; los definitivos los produce la medición del prototipo.

## 3. Qué cierra esta fase

| Cuestión abierta | Origen | Cierre |
|---|---|---|
| Esquemas de datos definitivos | F-09 §5 | [`03`](03_datos.md) |
| Contratos de eventos al detalle de campo | F-09 §5, D-08 §3 | [`02`](02_eventos.md) |
| Estructura interna de cada servicio | F-09 §5 | [`07`](07_detalles_de_implementacion.md) |
| Configuración del pipeline del switch | F-09 §5 | [`06`](06_reglas.md) |
| Métrica del costo por enlace | [`flows/05`](../../../flows/05_enrutamiento.md) §8 | [`06`](06_reglas.md) §4 |
| Prioridad concreta de las reglas de camino | [`flows/05`](../../../flows/05_enrutamiento.md) §8 | [`06`](06_reglas.md) §3 |
| Vía que declara el inventario de servicios | [`flows/05`](../../../flows/05_enrutamiento.md) §8 | [`01`](01_apis.md) §4 |
| Número de tablas del pipeline (plana o multi-tabla) | [`flows/01`](../../../flows/01_primitivas_openflow.md) (cuestiones abiertas) | [`06`](06_reglas.md) §2 |

## 4. Fronteras de esta fase

- **Fase H (despliegue):** qué máquinas, qué red y en qué orden — el LLD define qué corre **dentro** de cada máquina; H define las máquinas y cómo se unen ([`H-00`](../H-Despliegue/00_metodo_y_mapa.md)).
- **Prototipo (medición):** los valores finales cuantitativos (umbrales, tiempos, capacidades) salen de las mediciones ya comprometidas en [`F-09`](../F-Decisiones_tecnologicas/09_sintesis_y_trazabilidad.md) §4; este LLD es su punto de partida.
