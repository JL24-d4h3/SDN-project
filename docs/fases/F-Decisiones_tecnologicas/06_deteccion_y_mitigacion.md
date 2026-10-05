# Detección y mitigación

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** F — Decisiones tecnológicas
**Estado:** Borrador formal para revisión

---

El corazón de R3 y R4: **qué se observa, con qué frecuencia, con qué umbrales y con qué regla se pasa de la observación a la mitigación**. Esta fase decide el algoritmo de detección, la naturaleza de los umbrales, la frecuencia de I8, la precedencia P9/P12 que [`D-03`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/03_principios_arquitectonicos.md) §7 dejó abierta, y fija el presupuesto de latencia de D-10. Los **valores finales** de umbrales y tiempos no se inventan aquí: se calibran con el prototipo y cierran R4.3/R4.4/R4.10.

## 1. Qué exige la arquitectura

| Exigencia | Origen |
|---|---|
| Obtener del tráfico la información suficiente para detectar scanning, spoofing, anomalías y ataques distribuidos | R3.1–R3.5 |
| Línea base del servicio protegido e indicadores (pps, solicitudes/s, flujos nuevos, fuentes) | R4.1–R4.3 |
| Criterios cuantitativos que distingan tráfico normal de malicioso, con medición de detección, mitigación e impacto | R4.4, R4.10 |
| La cadena nunca salta: detector observa → Policy Engine decide → controlador traduce → switch ejecuta | P8, RA-06 |
| Contadores OpenFlow como única fuente de observación del plano de datos | P11 |
| Mitigar cerca del origen, limitar antes que bloquear, preservar el servicio legítimo | P9, R4.6–R4.8 |

## 2. Observación: qué lee el monitor y con qué frecuencia (I8)

El Monitor nunca habla con los switches: lee a través del controlador (`OFPMP_PORT_STATS`, `OFPMP_FLOW`, I8) y solo contadores (P11). **Decisión de frecuencia:**

| Régimen | Alcance | Frecuencia por defecto |
|---|---|---|
| **Conjunto caliente** | Recursos protegidos y sus puertos/reglas de ingreso | **5 s** |
| **Barrido completo** | Inventario completo de flujos y puertos | **60 s** |

Ambos valores son **configurables**, y esa configurabilidad es en sí la decisión: el presupuesto de carga sobre el plano de control (D-11) y la latencia de detección (D-10) están en tensión, y la resolución se mide — el experimento de sobrecarga de sondeo (RNF-03) prueba 5/30/60 s y reporta carga y latencia resultantes. El barrido completo existe para lo que no está en el conjunto caliente: un destino que despierta interés entra al conjunto caliente a partir del siguiente barrido.

```text
Monitor (observa, no decide)
  cada 5 s   pps · bps · flujos nuevos/s por destino protegido
             y por origen: nº de destinos distintos, flujos nuevos/s
  cada 60 s  inventario completo (flujos y puertos)
        │ métricas y features por el broker (D-04: la materia prima)
        ▼
Detection Engine (clasifica, no ordena)
        │ AnomalyDetected (tipo, objetivo, origen, severidad propuesta)
        ▼
Incidente → Policy Engine → Controlador → Switch   (P8)
```

**Monitor y Detección: dos servicios, también en el prototipo** (cierre de la cuestión de D-04 §7). El Monitor observa y mantiene la línea base; la Detección juzga y clasifica; las métricas viajan del Monitor a la Detección por el broker —el contrato que D-04 ya fija—. Se mantienen separados: la frontera «observar no es juzgar» (P8) es la que la validación comprobó, separarla cuesta dos contenedores, y consolidarlos difuminaría en la demostración el mismo límite que E-01/E-02 trazaron.

## 3. Línea base y umbrales: dinámicos con piso estático

**Decisión.** La línea base por destino protegido es una **media móvil exponencial (EWMA)** del indicador —pps, bps, flujos nuevos— con su varianza también suavizada. El umbral de disparo es **relativo** (la desviación sobre la media, en múltiplos de la desviación típica) y lleva **piso absoluto** (un mínimo por debajo del cual nada dispara) y **histéresis** (cuesta más entrar que salir, para no oscilar). La confirmación exige **N ventanas sostenidas**.

**Por qué así y no un umbral fijo:** el tráfico del campus no es estacionario —varía por hora, por día, por actividad académica—; un umbral fijo calibrado en el peor momento ciega al detector en hora valle y produce falsos positivos en hora punta. La EWMA se adapta sola. El **piso** existe porque la adaptación tiene un punto ciego: un servicio silencioso no debe disparar por pasar de 3 a 6 pps — el piso es estático por diseño. La combinación cierra la pregunta «umbrales estáticos o dinámicos» de B-03 §4: **el mecanismo es dinámico; los pisos y los valores iniciales son estáticos y conservadores; la calibración final sale de las mediciones.**

Valores iniciales del prototipo — punto de partida explícito, ajustado con mediciones (R4.4):

| Parámetro | Valor inicial | Papel |
|---|---|---|
| α (suavizado EWMA) | 0,2 | memoria de la línea base (~5 ventanas) |
| Ventana | 5 s | igual al pulso del conjunto caliente |
| N (ventanas sostenidas) | 3 | confirmación: 15 s antes de proponer acción |
| k de entrada / salida | 4σ / 2σ | histéresis |
| Piso por destino protegido | 200 pps · 2 Mbps | evita disparos triviales |
| Calentamiento | 30 min | antes de él rigen los pisos; el detector observa y alerta, no actúa solo |

## 4. Clasificación por patrón

Cada clase del catálogo ([`D-11.1`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/11.1_catalogo_de_ataques_y_amenazas.md)) tiene su firma de features:

| Clase | Features | Regla de clasificación |
|---|---|---|
| **Flood volumétrico / DDoS** (R4) | pps/bps hacia destino protegido | ≥ k·σ sobre la línea base **y** sobre el piso, sostenido N ventanas |
| **Ataque distribuido** (R3.5) | nº de fuentes distintas contra el mismo destino | ≥ 10 fuentes en 60 s con tasa agregada sobre el umbral: se clasifica distribuido y se mitiga **por switch de ingreso de cada origen** (P9) |
| **Brute-force** (R4) | solicitudes/s por origen hacia puertos de aplicación (portal) | ≥ 20 solicitudes/s por origen sostenidas, con tasa de nuevas conexiones alta |
| **Scanning** (R3.2) | nº de destinos distintos por origen, con volumen por destino muy bajo | > 20 destinos distintos en 60 s: patrón de barrido |
| **Spoofing y `MAC_Moved`** (R3.3) | *no son estadísticos* | El controlador compara contra la asociación aprendida: incoherencia = hecho determinista, no umbral (P7) |

Las detecciones deterministas (última fila) tienen severidad propia y **no esperan confirmación estadística**: una incoherencia sostenida es un hecho, no una tendencia.

## 5. De la severidad a la respuesta: qué se automatiza

La escalera de respuestas ya está fijada: `RATE_LIMIT → BLOCK_SOURCE → ISOLATE_DEVICE → QUARANTINE` ([`D-04`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/04_descomposición_arquitectonica.md)). La decisión de esta fase es **qué peldaños se ejecutan sin humano**:

| Peldaño | Automatización | Fundamento |
|---|---|---|
| `RATE_LIMIT` (meter) | **Automático** ante anomalía confirmada | Mínima intervención; preserva el servicio legítimo (P9); reversible por timeout (P10) |
| `BLOCK_SOURCE` (drop del origen) | **Automático** si la anomalía persiste pese al límite, o si el patrón es inequívoco | El origen ya mostró el comportamiento; el bloqueo es por origen, no por destino (P9); TTL corto |
| `ISOLATE_DEVICE` | **Automático solo ante detección determinista** (spoofing sostenido, `MAC_Moved`) | No depende de umbrales: es un hecho verificado contra la asociación; con TTL y auditoría inmediata |
| `QUARANTINE` (bloqueo total de alto impacto) | **Aprobación humana** | Regla ya fijada en D-03 §5: el bloqueo total de alto impacto exige aprobación del operador |

La frontera automático/humano sigue una regla única: **se automatiza lo reversible y proporcional; lo total y de alto impacto pasa por una persona.**

## 6. Precedencia P9/P12 (cierre de la cuestión abierta)

Si una mitigación que preserva el tráfico legítimo no alcanza las métricas exigidas —el ataque baja, pero no a los valores de la línea base—, **prima P9 en la ejecución automática**: el sistema no sube la fuerza para «mejorar la métrica» a costa del servicio. **P12 gobierna la evaluación**: la brecha entre el resultado y la métrica esperada se mide, se registra y **escala a revisión humana** — el operador decide si el peldaño siguiente corresponde. Así la disponibilidad y la métrica no compiten: la métrica obliga a mirar, la disponibilidad decide sin humano solo hasta donde es reversible.

## 7. Presupuesto de latencia (D-10)

| Etapa | Presupuesto provisional | Cómo se cumple |
|---|---|---|
| Ataque → detección | ≤ 15 s | 3 ventanas de 5 s (N=3); patrones inequívocos pueden confirmar antes |
| Detección → orden confirmada | ≤ 5 s | cadena de eventos + orden sincrónica con confirmación ([`01`](01_controlador_y_api_northbound.md) §4.4) |
| Orden → efecto en el plano de datos | < 1 s | meter nativo; la ejecución no depende del controlador (P2) |
| **Total percibido** | **≤ 20 s en el peor caso de patrón lento** | Los valores finales se miden y reportan (R4.10) |

## 8. Verificación

**Protocolo de escenarios** (tráfico legítimo en paralelo, siempre — sin él no se mide R4.8):

| Escenario | Mide | Cierra |
|---|---|---|
| Flood volumétrico controlado (RP-06/08) | Tiempo de detección, de mitigación y de retiro; tasa efectiva del meter | R4.2, R4.5, R4.6, R4.10 |
| Flood con tráfico legítimo simultáneo | Peticiones legítimas exitosas durante la mitigación (impacto, R4.8) | R4.8, P9 |
| Ataque distribuido desde varios orígenes | Detección por nº de fuentes; mitigación por switch de ingreso | R3.5 |
| Scanning y `brute-force` controlados | Detección por patrón; escalera hasta BLOCK | R3.2, R4 |
| Spoofing e `MAC_Moved` | Detección determinista; aislamiento automático | R3.3, P7 |
| Días de tráfico de fondo sin ataques | **Falsos positivos** por día; ajuste de α, k y pisos | B-03 §5, D-14 |
| Barrido de frecuencias de sondeo (5/30/60 s) | Carga sobre el plano de control y latencia resultante | RNF-03, D-11 |
| Umbral estático calibrado vs. adaptativo | Comparación cuantitativa de detección y falsos positivos | D-14, comparación de alternativas |

El resultado de estos escenarios es el **cierre cuantitativo de R4.3/R4.4/R4.10, RNF-03 y RNF-04**, y la calibración final de los valores iniciales de §3.
