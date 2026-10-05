# Método de decisión tecnológica

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** F — Decisiones tecnológicas
**Estado:** Borrador formal para revisión

---

La Fase D fijó **qué componentes existen y qué contrato los une**; esta fase elige **con qué tecnología se materializan**. Ninguna decisión de esta fase cambia la arquitectura: la implementa. Si una tecnología no puede cumplir un contrato ya fijado, se cambia la tecnología, no el contrato.

## 1. De dónde vienen las decisiones

Cada decisión de esta fase tiene origen en un lugar del corpus que la difirió explícitamente:

| Origen | Qué dejó pendiente |
|---|---|
| [B-03](../B-Drivers_de_arquitectura/03_priorizacion_de_drivers.md) §4 | El catálogo de decisiones que activa cada driver: controlador, norte/sur, umbrales, IDS/IPS, almacenamiento, virtualización, visualización |
| [C-04](../C-Contexto/04_alcance_de_la_infraestructura.md) §6 | Capacidad del dispositivo, representación del perímetro, hardware físico o virtual |
| [D-07](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/07_interfaces_principales.md) §4 | Forma concreta de I2 e I7; producto del broker (I5); frecuencia de I8 |
| [D-08](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/08_comunicacion.md) §4, §6 | Mecanismo de entrega ordenada; confirmación de comandos; retención de eventos en el broker |
| [D-04](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/04_descomposición_arquitectonica.md) §7 | Consolidación Monitor/Detección en el prototipo |
| [D-03](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/03_principios_arquitectonicos.md) §7 | Precedencia P9/P12 en caso extremo |
| [E-04](../E-Validacion_del_HLD/04_escenarios_de_fallo.md) §4 | Redundancia del plano de control; reconstrucción del intermediario; retención de registros |
| [E-05](../E-Validacion_del_HLD/05_escenarios_de_ataque.md) §3 | Fuente de tiempo común; cierre del perímetro (R5) |
| [E-02](../E-Validacion_del_HLD/02_requisitos_a_componentes.md) §5 | Elementos cuantitativos: R4.3/R4.4/4.10, RNF-03/04/11/12 |

## 2. Criterios de elección

Toda decisión de producto se justifica con cinco criterios, en este orden:

1. **Cumplimiento** — resuelve el requisito o driver que la origina (R1–R5, RT, RNF, RA).
2. **Verificabilidad** — permite producir las métricas que el curso exige (P12, RNF-12, RP-10); una alternativa sin medición no es una alternativa.
3. **Simplicidad justificada** — dimensionada al prototipo, no a producción (P4, RP-04, RP-07): contra el tamaño real del prototipo, no contra una universidad.
4. **Encaje con las restricciones** — Pica8/PicOS (RP-11), canal de control out-of-band (RP-02), IPv4 (RP-12), entorno del laboratorio.
5. **Separación de responsabilidades** — el producto no absorbe funciones de otro componente (RT-02, P3): elegir un producto no reasigna responsabilidades.

## 3. Formato de cada decisión

Cada documento de la serie sigue la misma estructura:

```text
Contexto      qué exige la arquitectura (con su origen documental)
Decisión      el producto o mecanismo elegido, en una frase
Justificación contra los cinco criterios, punto por punto
Configuración cómo queda en el prototipo (piezas, puertos, parámetros)
Límites       qué no decide esta fase y con qué fase se cierra
Verificación  qué prueba del prototipo cierra la decisión y qué mide
```

Cuando P12 obliga a decidir **con resultados** —meters nativos frente a degradación por controlador, redirección por grupo frente a `PACKET_OUT`— el documento no elige de antemano: fija las alternativas, el experimento y la regla de decisión. La medición decide; el documento registra qué se medirá.

## 4. Mapa de la serie

| Documento | Decide | Cierra |
|---|---|---|
| [`01_controlador_y_api_northbound.md`](01_controlador_y_api_northbound.md) | Producto del controlador; forma de I2; redundancia del plano de control | RA-02, RT-04, E-04 |
| [`02_plano_de_datos_pica8.md`](02_plano_de_datos_pica8.md) | Primitivas del plano de datos; verificación de PicOS; capacidad de reglas | RT-05, R4.6, C-04 §6 |
| [`03_identidad_sesiones_y_portal.md`](03_identidad_sesiones_y_portal.md) | Producto de I4; repositorio de operadores y TOTP; forma de la sesión; distinción de población; valores de vigencia | R1.2, I4, I7, I3 |
| [`04_mensajeria_y_eventos.md`](04_mensajeria_y_eventos.md) | Producto del broker; entrega ordenada; garantías; reconciliación | I5, D-08 §4, E-04 |
| [`05_persistencia_auditoria_y_tiempo.md`](05_persistencia_auditoria_y_tiempo.md) | Persistencia (I6); retención e integridad de registros; tiempo común; visualización | I6, RNF-09, E-04, E-05 |
| [`06_deteccion_y_mitigacion.md`](06_deteccion_y_mitigacion.md) | Algoritmo de detección; umbrales; frecuencia de I8; precedencia P9/P12; presupuesto de latencia | R3.1–R3.10, R4.1–R4.10, D-10 |
| [`07_perimetro_r5.md`](07_perimetro_r5.md) | Evaluación IDS/IPS; perímetro; inteligencia de amenazas | R5.1–R5.8, CU-08 |
| [`08_entorno_del_prototipo.md`](08_entorno_del_prototipo.md) | Virtualización y simulación; segmentos; generación de tráfico; reproducibilidad | RP-05, RNF-11, C-04 |
| [`09_sintesis_y_trazabilidad.md`](09_sintesis_y_trazabilidad.md) | Tabla decisión ↔ requisito ↔ verificación; pendientes que quedan | Todas |

## 5. Fronteras de esta fase

- **Valores finales cuantitativos** (umbrales, capacidades, tiempos): esta fase decide el mecanismo y el experimento; el número final lo produce el prototipo y se reporta como cierre de R4.10, RNF-03/04/11/12.
- **Detalle de implementación** (estructuras internas, librerías): Fase G.
- **Despliegue físico** (nodos, enlaces, redundancia real): Fase H.
- **Cada decisión conserva los contratos** de [`07_interfaces_principales.md`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/07_interfaces_principales.md) y [`08_comunicacion.md`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/08_comunicacion.md): formatos de eventos, separación síncrono/asíncrono y frontera de secretos no se negocian con el producto.
