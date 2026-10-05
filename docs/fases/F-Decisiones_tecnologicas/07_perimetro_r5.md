# Perímetro (R5)

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** F — Decisiones tecnológicas
**Estado:** Borrador formal para revisión

---

El único hueco material del HLD ([`E-02`](../E-Validacion_del_HLD/02_requisitos_a_componentes.md) §5, CU-08): el perímetro y el bloque R5. Esta fase lo cierra: **evaluación IDS/IPS de R5.2, definición del perímetro (R5.1), determinación de indicadores maliciosos (R5.6) y demostración del bloqueo con la cadena SDN (R5.4, R5.5, R5.7)**. La arquitectura interna ya estaba lista para recibir eventos perimetrales (R5.7 no requiere nada nuevo: es la misma cadena R3/R4).

## 1. Qué exige el requerimiento

| Requisito | Qué pide |
|---|---|
| R5.1 | Definir los mecanismos de control entre redes externas e internas |
| R5.2 | **Evaluar** el uso de IDS, IPS o ambos |
| R5.3 | Analizar el tráfico externo relevante para identificar actividad maliciosa |
| R5.4 | Bloquear tráfico desde IP identificadas como maliciosas |
| R5.5 | Bloquear conexiones hacia destinos maliciosos |
| R5.6 | Definir cómo se determina que una IP, URL u otro indicador es malicioso |
| R5.7 | Que los eventos perimetrales generen políticas o acciones sobre la red SDN |
| R5.8 | Registrar los eventos |

R5 no es un requerimiento asignado: se **diseña por completo y se demuestra con un escenario representativo** (B-03 §3, P1), según lo permita el entorno.

## 2. Evaluación IDS/IPS (R5.2): IDS con enforcement SDN

**Decisión.** Detección perimetral con **IDS** —análisis de tráfico espejado, sin estar en el camino— y **bloqueo ejecutado por la red SDN**: el switch de borde descarta por orden del controlador. La función del IPS existe y se ejerce en cada bloqueo; lo que no existe es un **appliance inline**.

La evaluación que R5.2 pide, en términos de arquitectura:

| Criterio | Appliance inline (IPS) | IDS + enforcement SDN (elegido) |
|---|---|---|
| Separación detectar/decidir/ejecutar (P8) | Fusiona detección y ejecución en un punto | Cada función en su componente: el IDS observa, el Policy Engine decide, el switch ejecuta |
| Disponibilidad (RNF-02) | Es un punto único **en el camino**: su caída o saturación corta el tráfico externo | Fuera del camino: su caída degrada la detección, no el servicio |
| Integración SDN (R5.7) | El bloqueo vive fuera del controlador; la red no aprende | El bloqueo **es** la cadena SDN: evento → política → `FLOW_MOD` en el borde |
| Evidencia para el curso | — | La demostración perimetral ejercita el mismo pipeline que R4, con el borde como punto de aplicación |

Un IDS dedicado más el enforcement SDN **es** «IDS y el efecto de IPS», sin pagar el costo arquitectónico de un inline ni duplicar la función de ejecución que el switch ya cumple.

## 3. La arquitectura perimetral

```text
        RED EXTERNA (simulada en el prototipo)
              │
   ┌──────────▼──────────┐   espejo (SPAN)    ┌────────────────────┐
   │ switch de BORDE     │───────────────────►│ sensor IDS         │
   │ (Pica8/PicOS)       │   tráfico externo  │ (Suricata, IDS)    │
   │ reglas de bloqueo   │                    │ firmas + anomalías │
   └──────────┬──────────┘                    └─────────┬──────────┘
              │ segmento interno                          │ EVE JSON
              │                                           ▼
              │                                 adaptador del sensor
              │                                 (parte del Detection Engine)
              │                                           │ AnomalyDetected
              │                                           │ (origen = perímetro)
              │◄──────── FLOW_MOD DROP ──── Controlador ◄───┴─ Policy Engine
```

- **Punto de control (R5.1):** el switch de borde es el punto de enforcement; entre la red externa y el segmento interno no hay más camino que él. En el prototipo, la «red externa» es un segmento controlado del laboratorio que representa ese papel; los ataques perimetrales se generan dentro del entorno (RP-06/08).
- **Inspección (R5.3):** Suricata en modo IDS sobre el puerto espejo del borde: ve todo el tráfico externo relevante sin participar del reenvío. Sus alertas salen en formato **EVE JSON**.
- **Integración (R5.7):** un adaptador —que pertenece al Detection Engine como su **sensor perimetral**— convierte cada alerta en un `AnomalyDetected` con `origen = perímetro`, el mismo contrato que cualquier otra anomalía. Desde ahí, la cadena es la conocida: Incidente → Policy Engine → controlador → **drop en el switch de borde**.
- **Bloqueo (R5.4):** la mitigación instala un DROP del origen malicioso en el borde —el tráfico externo malicioso se descarta antes de entrar (P9 aplicado al perímetro).
- **Bloqueo hacia destinos (R5.5):** para un destino externo identificado como malicioso, el Policy Engine ordena el DROP de los flujos internos hacia ese destino —la dirección inversa del mismo mecanismo—.

**Qué NO cambia:** el IDS no decide ni ordena (P8); sus alertas son insumo. Y la cadena conserva la trazabilidad completa: una alerta del sensor es tan auditable como una anomalía interna (RA-06).

## 4. Determinación de indicadores (R5.6)

**Decisión.** Dos fuentes, una sola puerta:

1. **Veredicto de las firmas del IDS** sobre el tráfico observado: la actividad maliciosa se identifica en el hecho, con la regla que la detectó como evidencia.
2. **Lista de inteligencia propia de la plataforma**: entradas (**IP o URL maliciosa + origen + vigencia + responsable**) mantenidas desde la consola por los operadores, con TTL como todo estado del sistema (P10).

**La regla de promoción cierra el ciclo:** una alerta perimetral confirmada por un operador puede convertirse en entrada de la lista —con vigencia y responsable— y entonces el bloqueo ya no depende de volver a ver el ataque: el indicador conocido bloquea de entrada. La lista se consulta al decidir; nada se bloquea «para siempre»: cada entrada expira y se revisa.

**Alcance del prototipo:** firmas del IDS + lista propia. La suscripción a feeds externos de inteligencia es una **extensión de despliegue** (Fase H): el mecanismo —ingerir, evaluar, agregar con vigencia— es el mismo; la fuente cambia.

## 5. Registro (R5.8)

Toda alerta perimetral, toda decisión y todo bloqueo entran al `AuditRepository` con `origen = perímetro`, la firma o regla que detectó, el indicador involucrado y la cookie de la regla de bloqueo ([`05`](05_persistencia_auditoria_y_tiempo.md) §4). Los eventos perimetrales aparecen en la consola junto a los internos: una sola historia de la seguridad de la red.

## 6. Cierre del bloque R5

| Requisito | Cómo queda cubierto |
|---|---|
| R5.1 | Switch de borde como único punto de control entre red externa y interna (§3) |
| R5.2 | Evaluación hecha: IDS + enforcement SDN, con la comparación de §2 |
| R5.3 | Suricata en modo IDS sobre el espejo del borde (§3) |
| R5.4 | DROP del origen malicioso en el borde, por la cadena SDN (§3) |
| R5.5 | DROP de flujos internos hacia destinos maliciosos (§3) |
| R5.6 | Firmas + lista propia con vigencia y responsable (§4) |
| R5.7 | La alerta perimetral entra como `AnomalyDetected` y recorre la cadena existente (§3) |
| R5.8 | Registro con origen perimetral en la auditoría (§5) |

Con esto, el hueco CU-08 de [`E-01`](../E-Validacion_del_HLD/01_casos_de_uso_a_componentes.md) y el bloque R5 de E-02 quedan cerrados **por diseño**; la demostración en el prototipo depende de que el entorno la permita (B-03 §3).

## 7. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Ataque desde el segmento externo simulado → alerta del IDS → bloqueo en el borde | Latencia alerta → bloqueo; el ataque cesa en el borde | R5.3, R5.4, R5.7 |
| Bloqueo hacia un destino malicioso de la lista | Flujos internos hacia ese destino descartados | R5.5 |
| Entrada de lista: alta desde la consola, uso inmediato, expiración por vigencia | La lista es operativa y temporal | R5.6, P10 |
| Carga del espejo y descarte del IDS bajo tráfico externo alto | El sensor no degrada el reenvío (no está en el camino) | RNF-02 |
| Días de tráfico externo normal | Falsos positivos del sensor y de la lista | B-03 §5 |
