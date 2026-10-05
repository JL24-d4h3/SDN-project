# Síntesis y trazabilidad

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** F — Decisiones tecnológicas
**Estado:** Borrador formal para revisión

---

La vista completa de la fase: qué se decidió, contra qué requisito responde cada decisión, dónde se verifica y qué queda pendiente. Los documentos de la serie son el detalle; este es el mapa.

## 1. Las decisiones, de un vistazo

| Papel | Decisión | Documento |
|---|---|---|
| Controlador SDN | ONOS, instancia única; API de órdenes sobre su REST | [`01`](01_controlador_y_api_northbound.md) |
| Plano de datos | PicOS OpenFlow 1.3; primitivas verificadas contra el dispositivo | [`02`](02_plano_de_datos_pica8.md) |
| Identidad | FreeRADIUS + OpenLDAP (I4); repositorio propio con TOTP para operadores | [`03`](03_identidad_sesiones_y_portal.md) |
| Sesión | Cookie opaca ligada al dispositivo; I7 = REST por servicio con rol validado en servidor | [`03`](03_identidad_sesiones_y_portal.md) |
| Portal | Un servicio, selector explícito de población | [`03`](03_identidad_sesiones_y_portal.md) |
| Bus de eventos | RabbitMQ; cola por incidente para la entrega ordenada; at-least-once con DLQ | [`04`](04_mensajeria_y_eventos.md) |
| Persistencia | PostgreSQL, una base por servicio; auditoría con export JSONL encadenado | [`05`](05_persistencia_auditoria_y_tiempo.md) |
| Tiempo | chrony, fuente propia del prototipo; UTC en todo registro | [`05`](05_persistencia_auditoria_y_tiempo.md) |
| Visualización | Consola (administración) + tableros de observabilidad en lectura | [`05`](05_persistencia_auditoria_y_tiempo.md) |
| Detección | EWMA con umbral relativo, piso absoluto e histéresis; frecuencias 5 s / 60 s | [`06`](06_deteccion_y_mitigacion.md) |
| Automatización | Escalera automática hasta lo reversible; cuarentena con humano | [`06`](06_deteccion_y_mitigacion.md) |
| Perímetro | Suricata IDS sobre espejo + enforcement SDN en el borde | [`07`](07_perimetro_r5.md) |
| Entorno | Contenedores por servicio; VMs de hosts; Pica8 físico como plano de datos | [`08`](08_entorno_del_prototipo.md) |

## 2. Trazabilidad: decisión → requisito → verificación

| Decisión | Requisitos y drivers | Verificación en el prototipo |
|---|---|---|
| Controlador ONOS | RA-02, RT-03, RT-05, D-06 | Orden de perfil extremo a extremo; caída y reinstalación ([`01`](01_controlador_y_api_northbound.md) §8) |
| API de órdenes (I2) | RT-04, R2.10, RNF-04 | Latencia orden → confirmación; rechazo de órdenes inválidas |
| Redundancia y failover | RA-07, D-09, E-04 | Convergencia ante corte de enlace y caída de switch (desplegado: ocho switches dual-homed); clúster del controlador documentado, no desplegado |
| Primitivas PicOS | RT-05, R4.6, R4.7, C-04 §5 | Checklist V1–V7 ([`02`](02_plano_de_datos_pica8.md) §4) |
| Capacidad de reglas | RNF-05, RA-08, D-11 | Experimento de llenado de tabla ([`02`](02_plano_de_datos_pica8.md) §5) |
| I4 RADIUS + LDAP | R1.2, R1.9 | Login de comunidad con accounting ([`03`](03_identidad_sesiones_y_portal.md) §7) |
| Operadores: repositorio + TOTP | R1.2, R1.8 | Login con segundo factor; alta auditada |
| Sesión ligada al dispositivo | RNF-01, P10, componentes/03 §4 | Cookie desde otro dispositivo → rechazo; `MAC_Moved` → cierre |
| Vigencias por perfil | R1.3, P10 | Expiración por inactividad → BASE ([`03`](03_identidad_sesiones_y_portal.md) §5) |
| Selector de población | I3, RNF-01 | Ruta de verificación por población; cruce falla y se audita |
| Broker RabbitMQ y orden por incidente | I5, P13, D-08 §4 | Consumidor detenido; orden bajo ráfaga; DLQ ([`04`](04_mensajeria_y_eventos.md) §8) |
| Reconciliación tras fallo | RA-07, E-04 | Drill: caída + expiración + retorno ([`04`](04_mensajeria_y_eventos.md) §6) |
| PostgreSQL por servicio | I6, D-04 §6 | Aislamiento entre bases; drill de restauración |
| Auditoría: retención e integridad | RT-07, RNF-09, P11 | Verificador de cadena de hash; consulta por rol |
| Tiempo común | RNF-09, E-05 | Desfase NTP por nodo |
| Visualización | RT-06, RNF-08 | Tableros con línea base y métricas R4.10 |
| Detección EWMA + pisos | R3.1–R3.5, R4.1–R4.4 | Escenarios de ataque + días de fondo (falsos positivos) |
| Frecuencia de I8 | RNF-03, D-11 | Barrido 5/30/60 s: carga y latencia |
| Escalera automático/humano | R3.7, R3.8, RT-08, P8, P9 | Escenarios R4/R3 hasta cada peldaño |
| Precedencia P9/P12 | D-03 §7 | Mitigación que preserva servicio con métrica no alcanzada → escala a humano |
| Presupuesto de latencia | RNF-04, D-10, R4.10 | Tiempos medidos por escenario |
| Perímetro IDS + SDN | R5.1–R5.8 | Ataque desde el segmento externo → bloqueo en el borde ([`07`](07_perimetro_r5.md) §7) |
| Entorno del prototipo | RP-05, RNF-11, C-04 | Repetición de escenarios con parámetros registrados |

## 3. Lo que esta fase cierra

Cada cuestión que el corpus difirió a la Fase F, con su cierre:

| Cuestión diferida | Origen | Cierre |
|---|---|---|
| Producto del controlador | RA-02, B-03 D-06 | [`01`](01_controlador_y_api_northbound.md) §2 |
| Forma de I2 y esquema de la orden de perfil | D-07 §4, access/00 §6 | [`01`](01_controlador_y_api_northbound.md) §4 |
| Forma de I7 | D-07 §4 | [`03`](03_identidad_sesiones_y_portal.md) §4 |
| Redundancia del plano de control | E-04 §4 | [`01`](01_controlador_y_api_northbound.md) §6 |
| Verificación de primitivas y capacidad de reglas | C-04 §6; flows/01 y flows/04 | [`02`](02_plano_de_datos_pica8.md) §4–§5 |
| Producto de I4 | componentes/01 §7 | [`03`](03_identidad_sesiones_y_portal.md) §2 |
| Forma de la sesión; ligadura al dispositivo | componentes/01 §8, componentes/03 §8 | [`03`](03_identidad_sesiones_y_portal.md) §4 |
| Aprovisionamiento del TOTP | componentes/04 §4 | [`03`](03_identidad_sesiones_y_portal.md) §3 |
| Distinción de población en el portal | componentes/01 §8, componentes/04 §8 | [`03`](03_identidad_sesiones_y_portal.md) §6 |
| Vigencias por perfil | componentes/02 §4 | [`03`](03_identidad_sesiones_y_portal.md) §5 |
| Producto del broker; entrega ordenada; retención en el broker | D-08 §4/§6 | [`04`](04_mensajeria_y_eventos.md) §2, §3, §7 |
| Reconciliación tras fallo del intermediario | E-04 §2 | [`04`](04_mensajeria_y_eventos.md) §6 |
| Confirmación de los comandos northbound (aplicado vs verificado) | D-08 §6 | [`01`](01_controlador_y_api_northbound.md) §4.4 |
| Consolidación Monitor/Detección en el prototipo | D-04 §7 | [`06`](06_deteccion_y_mitigacion.md) §2 |
| Persistencia (I6) | C-02 §4, D-07 §4 | [`05`](05_persistencia_auditoria_y_tiempo.md) §2 |
| Retención, integridad y recuperación de registros | E-04 §3, componentes/03 §8, A-02 §4 | [`05`](05_persistencia_auditoria_y_tiempo.md) §4 |
| Fuente de tiempo común (NTP) | E-05 §3 | [`05`](05_persistencia_auditoria_y_tiempo.md) §5 |
| Visualización | B-03 D-08/D-13 | [`05`](05_persistencia_auditoria_y_tiempo.md) §6 |
| Algoritmo de detección; umbrales estáticos o dinámicos | B-03 D-03/D-04 | [`06`](06_deteccion_y_mitigacion.md) §3 |
| Frecuencia de I8 | D-07 §4 | [`06`](06_deteccion_y_mitigacion.md) §2 |
| Precedencia P9/P12 | D-03 §7 | [`06`](06_deteccion_y_mitigacion.md) §6 |
| Presupuesto de latencia | B-03 §6 (D-10) | [`06`](06_deteccion_y_mitigacion.md) §7 |
| IDS, IPS o ambos; inteligencia de amenazas | R5.2, R5.6, E-05 §3 | [`07`](07_perimetro_r5.md) §2, §4 |
| Virtualización o simulación | B-03 D-06/D-11, C-04 §6 | [`08`](08_entorno_del_prototipo.md) §1 |

## 4. Deuda cuantitativa: qué mide el prototipo

Los pendientes que [`E-02`](../E-Validacion_del_HLD/02_requisitos_a_componentes.md) §5 registró no se cierran con documentos sino con mediciones; esta fase deja cada uno con su experimento:

| Pendiente | Experimento | Se reporta como cierre de |
|---|---|---|
| Valores de R4.3/R4.4 (indicadores y umbrales) | Escenarios R4 + días de fondo → calibración de α, k, pisos ([`06`](06_deteccion_y_mitigacion.md) §8) | R4.3, R4.4 |
| R4.10 (tiempos e impacto) | Cronometría por escenario | R4.10, RNF-04 |
| RNF-03 (sobrecarga) | Barrido de frecuencias de sondeo + carga del espejo | RNF-03 |
| RNF-11/12 (reproducibilidad y verificabilidad) | Repetición de escenarios con parámetros registrados ([`08`](08_entorno_del_prototipo.md) §4) | RNF-11, RNF-12 |
| Capacidad y escala (R1.10, RA-08) | Llenado de tablas + carga creciente sobre los ocho switches | RA-08, R1.10 |
| Tiempos de recuperación (RA-07) | Corte de enlace y caída de switch con caminos alternativos; caída del controlador; drill de restauración; reconciliación | RA-07 |

## 5. Fronteras: qué queda para las fases siguientes

- **Fase G (LLD):** esquemas de datos definitivos, estructura interna de cada servicio, contratos de eventos al detalle de campo, configuración del pipeline del switch.
- **Fase H (despliegue):** escrita — la topología física quedó fijada en ocho switches dual-homed ([`H-01`](../H-Despliegue/01_infraestructura_fisica.md) §3); lo que queda como análisis de referencia: clúster del controlador y multi-controlador en operación, feeds externos de inteligencia, cifrado en reposo y política de respaldo de un despliegue real, canal in-band.
- **Prototipo (medición):** todo lo de §4 — la fase F decidió el mecanismo y el experimento; el número final es un resultado, no un supuesto.
