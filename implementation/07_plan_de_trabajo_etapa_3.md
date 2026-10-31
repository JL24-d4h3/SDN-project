# Plan de trabajo de la etapa 3 — Ejecución y medición

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** Implementación — Etapa 3
**Estado:** Borrador formal para revisión

---

## 1. Propósito

Convertir el entorno reproducible de la etapa 2 en **evidencia verificable**: ejecutar los flujos F1–F7, la campaña de R4, la suite de permisos L0–L6, las pruebas de resiliencia y las mediciones de capacidad y latencia; ajustar lo que corresponda y cerrar con un registro de resultados y límites.

La etapa no añade arquitectura nueva. Si una medición contradice una decisión, el cambio se documenta y se versiona; no se improvisa durante la prueba.

## 2. Condiciones de entrada

- Etapa 2 cerrada: entorno reproducible, clúster ONOS sano, switches configurados y servicios base con `/health`.
- Capacidades del slice confirmadas y desviaciones registradas ([`04_capacidades_del_switch.md`](04_capacidades_del_switch.md)).
- Datos de prueba, cuentas y dispositivos de laboratorio disponibles.
- Relojes sincronizados; logs, contadores y auditoría recolectando.
- Guiones de ataque y tráfico legítimo preparados **dentro del entorno del proyecto** (RP-06/08).

## 3. Resultado esperado

La etapa se considera terminada cuando se cumplen estos criterios:

| # | Criterio | Evidencia |
|---|---|---|
| 1 | F1–F7 ejecutados de extremo a extremo, con trazas y estados finales correctos | Informe de flujos con fechas, trazas y tablas de flujo |
| 2 | R4 completo: detección, decisión, enforcement, verificación y recuperación | Informe R4 con línea base, contadores y tiempos |
| 3 | Suite de permisos L0–L6 en verde con los umbrales de [`03`](03_plan_de_pruebas_permisos.md) | Informe de cobertura y mutación |
| 4 | Resiliencia RD1–RD4 ejecutada; M3/M4 registrados | Informe de resiliencia y línea base de tiempos |
| 5 | Capacidad y latencia dentro del presupuesto o con desviación declarada | Informe de capacidad y latencia |
| 6 | Seguridad validada: anti-spoofing, cuarentena, aislamiento, auditoría y secretos | Informe de validación de seguridad |
| 7 | Paquete de evidencia completo y reproducible | Índice de evidencia y etiqueta de liberación |
| 8 | Límites, ajustes y trabajo futuro documentados | Informe de cierre de etapa |

## 4. Paquetes de trabajo

### WP3.1 — Integración de F1–F7

**Objetivo:** conectar los servicios y el controlador en los siete flujos arquitectónicos.

Tareas:

1. Completar los servicios que en la etapa 2 eran esqueletos: Detección, Incidentes, Políticas, Auditoría y Adaptador.
2. Conectar el bus de eventos con contratos, idempotencia y DLQ.
3. Verificar la máquina de estados del incidente y la correlación por `incident_id`, `session_id` y `device_id`.
4. Ejecutar F1 (descubrimiento), F2 (BASE), F3 (login), F5 (registro) y F4 (elevación).
5. Preparar F6 (R4) y F7 (recuperación) para la campaña de WP3.2.

**Entregable:** informe de integración F1–F7.
**Aceptación:** cada flujo termina en el estado declarado; los eventos se correlacionan; no quedan incidentes huérfanos ni reglas sin cookie.

### WP3.2 — Campaña R4

**Objetivo:** demostrar el ciclo completo de detección y mitigación.

Tareas:

1. Medir la línea base del servidor protegido con tráfico legítimo.
2. Ejecutar flood volumétrico controlado, ataque distribuido y `brute-force`.
3. Verificar detección, decisión, instalación de meter o DROP, verificación por contadores y retiro.
4. Medir el impacto sobre el tráfico legítimo durante la mitigación.
5. Registrar falsos positivos en ventanas sin ataque.
6. Ejecutar la recuperación y confirmar que no quedan reglas residuales.

**Entregable:** informe R4 con línea de tiempo, contadores y decisión por severidad.
**Aceptación:** detección ≤ 15 s; detección → orden ≤ 5 s; orden → efecto < 1 s; total ≤ 20 s en el peor caso lento; el tráfico legítimo sobrevive; la mitigación se instala en el switch de ingreso; no hay residuo.

### WP3.3 — Suite de permisos L0–L6

**Objetivo:** demostrar que el modelo de permisos decide y aplica correctamente.

Tareas:

1. L0: validar YAML, IDs y matriz con [`policy/generar_matriz.py`](policy/generar_matriz.py).
2. L1: unidad de decisión para los cuatro roles, contexto, vigencia y estado.
3. L2: las 15 invariantes de [`03`](03_plan_de_pruebas_permisos.md).
4. L3: integración de API por servicio y permiso; 401/403/200 y step-up.
5. L4: enforcement en switch para BASE, ACADÉMICO, operador, elevación y mitigación.
6. L5: escenarios extremo a extremo.
7. L6: cobertura y mutación.

**Entregable:** informe de pruebas con cobertura y mutación.
**Aceptación:** 100 % de permisos con caso allow y deny; 100 % de condiciones con caso que falla; ramas ≥ 90 %; mutantes ≥ 80 %; 100 % de asignaciones cubiertas; 15/15 invariantes.

### WP3.4 — Resiliencia RD1–RD4

**Objetivo:** medir qué sostiene la red cuando falla una pieza.

Tareas:

1. RD1: caída de un enlace de acceso o de núcleo; convergencia y caminos alternos. RD1 se define en este plan; RD2–RD4 provienen de [`H-01`](../docs/fases/H-Despliegue/01_infraestructura_fisica.md).
2. RD2: caída de un nodo ONOS durante un login; re-maestría y `FLOW_MOD` del nuevo maestro.
3. RD3: caída de un enlace o del nodo del núcleo que conecta el bloque de servicios; continuidad por la segunda NIC o por el otro nodo del núcleo (L01). La caída de un servidor completo no se compensa con otro: no hay replicación activa-activa, el servicio se reinicia y el límite se registra.
4. RD4: caída de dos nodos ONOS; lo permitido sigue, lo nuevo espera quórum.
5. Medir M3 (re-maestría) y M4 (latencia de I2 por nodo).
6. Verificar reconciliación: reinstalar lo faltante, no borrar lo vigente.

**Entregable:** informe de resiliencia con tiempos y estado de reglas.
**Aceptación:** RD2 completa el login; RD4 conserva lo permitido; no aparecen reglas fantasma ni duplicadas; M3/M4 quedan registrados como línea base.

### WP3.5 — Capacidad y rendimiento

**Objetivo:** comprobar que el diseño cabe en el switch y en el controlador.

Tareas:

1. Medir el llenado de tablas por switch y el total del slice.
2. Comparar con el sobre de 420–520 entradas de la referencia y con la suposición de 2 000 por switch.
3. Medir la latencia de `FLOW_MOD` y de la orden I2.
4. Medir CPU y RAM del controlador y de los servicios.
5. Medir la carga del sondeo I8 en 5/30/60 s.
6. Probar el crecimiento: añadir un host y, si el slice lo permite, un switch.

**Entregable:** informe de capacidad y latencia.
**Aceptación:** sin desbordamiento de tablas; el sobre se cumple o la desviación se explica; la latencia entra en el presupuesto; el crecimiento no rompe perfiles ni prioridades.

### WP3.6 — Validación de seguridad

**Objetivo:** comprobar que los controles se aplican y que la auditoría no se puede eludir.

Tareas:

1. Anti-spoofing: IP con MAC ajena y `MAC_Moved`.
2. Cuarentena automática de nodo y aislamiento de segmento con aprobación P32.
3. Break-glass y cuentas locales fuera de P14.
4. Integridad de la cadena de auditoría y exportación.
5. Análisis de secretos en repositorio, imágenes y eventos.
6. Intento de acceso directo a la gestión desde BASE y desde VLAN 30.
7. Verificar que OpenFlow solo acepta a los endpoints del clúster.

**Entregable:** informe de validación de seguridad.
**Aceptación:** los controles deniegan lo que deben; no hay bypass crítico; la auditoría cubre las acciones; no hay secretos expuestos.

### WP3.7 — Observabilidad y evidencia

**Objetivo:** dejar rastro verificable de cada prueba.

Tareas:

1. Paneles de Grafana para estado, tráfico, incidentes y sesiones.
2. Alertas de prueba y verificación de llegada.
3. Retención y exportación de logs y auditoría.
4. Índice de evidencia: prueba, fecha, etiqueta, entorno, comando, resultado y enlace al log.
5. Capturas o grabaciones de las demostraciones.

**Entregable:** paquete de evidencia `tests/evidence/etapa_3/`.
**Aceptación:** cada criterio de §3 tiene evidencia enlazada; los paneles reflejan las pruebas; la evidencia se reproduce con la etiqueta registrada.

### WP3.8 — Ajuste y cierre

**Objetivo:** corregir lo que la medición justifique y cerrar la etapa.

Tareas:

1. Ajustar umbrales, ventanas y prioridades con los valores medidos.
2. Actualizar documentos y configuración afectados.
3. Registrar límites y trabajo futuro.
4. Etiquetar la liberación final y ejecutar la retrospectiva.

**Entregable:** informe de cierre y etiqueta `v1.0-prototipo`.
**Aceptación:** la matriz de aceptación está completa; las desviaciones están declaradas; no queda ningún crítico abierto.

## 5. Dependencias y secuencia

```text
WP3.1 ──► WP3.2 ──► WP3.4 ──► WP3.7 ──► WP3.8
   │          │          │
   ├──► WP3.3 ─┴──► WP3.5 ─┘
   │          │
   └──────────┴──► WP3.6 ──► WP3.7
```

- **Camino crítico:** WP3.1 → WP3.2 → WP3.4 → WP3.7 → WP3.8.
- WP3.3 puede avanzar en paralelo con WP3.2 después de WP3.1.
- WP3.5 requiere WP3.2 y WP3.3; WP3.6 requiere WP3.3 y WP3.4.
- WP3.8 exige todos los paquetes anteriores.

## 6. Calendario

| Semana | Hito | Paquetes |
|---|---|---|
| 4 | H4 — perfiles, elevación y mitigación | WP3.1, inicio de WP3.2 y WP3.3 |
| 5 | R4 y permisos | WP3.2, WP3.3, WP3.4 |
| 5–6 | H5 — extremo a extremo y observabilidad | WP3.5, WP3.6 |
| 6–7 | H6 — medición y ajuste | WP3.7, WP3.8 |
| 7–8 | H7 — documentación y demostración | WP3.8 |

Los identificadores `Hn` son los hitos de [`05`](05_plan_de_implementacion.md) §12; `M3` y `M4` son las mediciones de re-maestría y de latencia de I2 definidas en [`F-01`](../docs/fases/F-Decisiones_tecnologicas/01_controlador_y_api_northbound.md) §6. Son nomenclaturas distintas aunque compartan letra.

El calendario se ajusta a la ventana real del slice; la prioridad es R4, permisos y switch, y después la interfaz y los servicios no críticos.

## 7. Matriz de pruebas y mediciones

| Prueba | Qué demuestra | Requisito | Evidencia |
|---|---|---|---|
| F1 Descubrimiento | Topología y caminos por destino | RT-05, RP-02 | Tabla de topología y flujos |
| F2 BASE | Mínimo pre-login y DROP a gestión | R1, R2 | Tabla de flujos del host |
| F3 Login | Identidad, perfil y sesión | R1.2, R1.9, RA-09 | Traza de sesión y auditoría |
| F4 Elevación | Permiso temporal con TTL y aprobación | R1.3, R1.5, P28–P29 | Orden, regla y expiración |
| F5 Registro | Registro no concede privilegios | R1.7, P24, P30 | Alta y auditoría |
| F6 R4 | Detección, decisión y mitigación | R4, RA-06, RT-08 | Informe R4 |
| F7 Recuperación | Retiro y restauración | R4.9, RT-10 | `FLOW_REMOVED` y contadores |
| Permisos L0–L6 | Decisión y enforcement | RNF-12, RA-09 | Informe de cobertura |
| RD1–RD4 | Resiliencia y re-maestría | RA-07, R4.10, E-04 | Informe de resiliencia |
| Capacidad | Flujos, tablas y latencia | RNF-05, RA-08 | Informe de capacidad |
| Seguridad | Controles y auditoría | R3, R4, R5 | Informe de seguridad |
| Observabilidad | Métricas, logs y alertas | RNF-08, RNF-09 | Paneles e índice |

| Medición | Método | Unidad | Dónde se registra |
|---|---|---|---|
| Detección de ataque | Primera ventana que confirma el patrón | s | Informe R4 |
| Decisión a orden confirmada | Marca de tiempo del evento y de la respuesta I2 | s | Informe R4 |
| Orden a efecto en el plano de datos | Contador antes/después y `BARRIER` | ms | Informe R4 |
| Total percibido | Suma del peor caso lento | s | Informe R4 |
| Re-maestría (M3) | Caída del nodo a `MASTER` del nuevo | s | Informe de resiliencia |
| Latencia I2 (M4) | p50 y p95 por nodo | ms | Informe de resiliencia |
| Llenado de tablas | Flujos por switch y total | entradas | Informe de capacidad |
| Latencia de `FLOW_MOD` | Orden a `BARRIER_REPLY` | ms | Informe de capacidad |
| Carga de sondeo | Consultas por barrido y CPU del controlador | % / consultas | Informe de capacidad |
| Falsos positivos | Alertas por día sin ataque | alertas/día | Informe R4 |
| Cobertura de permisos | Casos allow/deny y mutantes | % | Informe de pruebas |

## 8. Criterios de aceptación

| Área | Criterio | Fuente |
|---|---|---|
| Permisos | 100 % allow/deny, 100 % condiciones, ramas ≥ 90 %, mutantes ≥ 80 %, 15/15 invariantes | [`03`](03_plan_de_pruebas_permisos.md) §L6 |
| R4 | Detección ≤ 15 s; decisión ≤ 5 s; efecto < 1 s; total ≤ 20 s | [`F-06`](../docs/fases/F-Decisiones_tecnologicas/06_deteccion_y_mitigacion.md) §7 |
| Resiliencia | RD2 completa el login; RD4 conserva lo permitido; M3/M4 registrados | [`H-01`](../docs/fases/H-Despliegue/01_infraestructura_fisica.md) §5 |
| Capacidad | Sin desbordamiento; sobre 420–520 o desviación explicada; 2 000 por switch verificado o corregido | [`G-06`](../docs/fases/G-Diseno_de_bajo_nivel-LLD/06_reglas.md) §4 |
| Seguridad | Sin bypass crítico; auditoría completa; sin secretos | [`F-06`](../docs/fases/F-Decisiones_tecnologicas/06_deteccion_y_mitigacion.md) §8 |
| Evidencia | Cada criterio con prueba, fecha, etiqueta y log | Este documento |

## 9. Evidencia y reproducibilidad

Cada prueba se registra con:

```text
tests/evidence/etapa_3/
  <ID>/
    README.md        # objetivo, entorno, etiqueta, comando, resultado
    salida.log       # salida cruda
    captura.png      # panel o tabla, si aplica
```

Reglas:

- La etiqueta de liberación identifica el código y la configuración exactos.
- Los fixtures no contienen secretos; las credenciales se generan al arrancar y se destruyen al terminar.
- Una prueba que no se puede repetir no cuenta como evidencia.
- Las desviaciones se registran con causa, impacto y trabajo futuro.

## 10. Riesgos y contingencias

| Riesgo | Señal | Mitigación | Respaldo |
|---|---|---|---|
| Umbrales mal calibrados | Falsos positivos o detección tardía | Ajustar con la línea base y las ventanas medidas | Declarar el valor como provisional y repetir |
| Espejo insuficiente | Pérdida de eventos del sensor | sFlow/NetFlow o tap en el host | Degradar R5 y declararlo |
| Clúster en un solo host | Una caída apaga los tres nodos | Distribuir nodos si el slice lo permite | Documentar el límite y medir caída de proceso |
| Ataques afectan otros slices | Tráfico fuera del entorno | Contención, límites y ventana acordada | Detener y repetir con menos intensidad |
| Tiempo insuficiente | WP3.7 no cierra | Priorizar R4, permisos y switch | Posponer consola y paneles no críticos |
| Pruebas no reproducibles | Resultado distinto al repetir | Guiones, fixtures y etiqueta fija | Repetir y registrar la diferencia |

## 11. Fuera de alcance

- Producción y alta disponibilidad geográfica.
- La topología de referencia de diez switches.
- Kubernetes, 802.1X en puertos sensibles y P35/P36 a nivel funcional.
- Pruebas de penetración fuera del entorno del proyecto.
- Integración con el IdP institucional de producción.

## 12. Trazabilidad

| Documento | Relación |
|---|---|
| [`03_plan_de_pruebas_permisos.md`](03_plan_de_pruebas_permisos.md) | Niveles, invariantes y umbrales de la suite |
| [`04_capacidades_del_switch.md`](04_capacidades_del_switch.md) | Capacidades y respaldos que condicionan las pruebas |
| [`05_plan_de_implementacion.md`](05_plan_de_implementacion.md) | Diseño del entorno que se ejecuta |
| [`06_plan_de_trabajo_etapa_2.md`](06_plan_de_trabajo_etapa_2.md) | Entorno de entrada y criterios de la etapa anterior |
| [`../flows/`](../flows/) | Flujos F1–F7 paso a paso |
| [`../docs/fases/F-Decisiones_tecnologicas/06_deteccion_y_mitigacion.md`](../docs/fases/F-Decisiones_tecnologicas/06_deteccion_y_mitigacion.md) | Presupuesto de latencia de R4 |
