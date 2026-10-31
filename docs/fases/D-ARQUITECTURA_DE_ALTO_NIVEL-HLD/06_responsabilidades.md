# Responsabilidades

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** D — Arquitectura de alto nivel (HLD)
**Estado:** Borrador formal para revisión

---

Este documento fija, por componente, qué responsabilidad tiene y qué **explícitamente no tiene** (P3), y qué rol humano opera cada componente. Complementa a [`05_componentes_principales.md`](05_componentes_principales.md) (descripción funcional) con la dimensión de autoridad.

## 1. Responsabilidad y no-responsabilidad por componente

| Componente | Responsable de | No es responsable de |
|---|---|---|
| **Monitor** | Obtener contadores; construir la línea base; verificar el efecto de las mitigaciones. | Detectar ataques; decidir respuestas; instalar reglas. |
| **Detection Engine** | Determinar si hay anomalía; clasificarla. | Registrar incidentes; decidir la mitigación; tocar la red. |
| **Incident Manager** | Registrar el incidente; llevar su ciclo de vida hasta CLOSED. | Calcular umbrales; elegir la respuesta; ejecutar reglas. |
| **Policy Engine** | Decidir la respuesta ante incidentes y las elevaciones de privilegios, con contexto y vigencia. | Observar el tráfico; ejecutar la decisión; administrar usuarios. |
| **Controlador SDN** | Traducir decisiones a reglas; mantener topología y asociaciones; retirar reglas. | Decidir políticas; juzgar si hay ataque; autenticar operadores. |
| **IAM/AAA** | Autenticar a las poblaciones; autorizar sesiones; registrar accounting. | Catalogar dispositivos; decidir mitigaciones; gestionar políticas. |
| **Registro de dispositivos** | Mantener el catálogo de dispositivos privilegiados y su auditoría de altas. | Conceder privilegios por sí mismo (P7); registrar dispositivos académicos. |
| **Auditoría** | Registrar acciones y decisiones; responder quién, qué, cuándo y por qué. | Participar en la cadena de decisión; bloquear o permitir (P11). |
| **Switches** | Ejecutar las reglas instaladas; reportar eventos y contadores. | Decidir qué reglas instalar; juzgar tráfico. |
| **Consola** | Exponer operación y consultas según el rol de la sesión. | Guardar estado; aplicar permisos por su cuenta. |

## 2. La cadena de R4 como cadena de responsabilidades

La tabla anterior se recorre de extremo a extremo en R4 — cada eslabón entrega el trabajo al siguiente y ninguno lo retiene:

```text
Monitor            observa y entrega métricas
   → Detection     juzga y entrega AnomalyDetected
   → Incident      registra y entrega IncidentOpened
   → Policy        decide y entrega MitigationRequired
   → Controlador   traduce y entrega FLOW_MOD
   → Switch        ejecuta y entrega contadores de vuelta
   → Monitor       verifica y entrega MitigationVerified
   → Incident      cierra el ciclo
   → Auditoría     registra todo el recorrido
```

Esta cadena cumple RA-06 (evento → detección → evaluación → decisión → política → aplicación → resultado) con un responsable identificable por etapa.

## 3. Matriz de roles humanos sobre los componentes

Qué puede hacer cada rol sobre cada componente, según los permisos de la fase A:

| Componente | Usuario académico | Especialista de TI | Administrador de Red | Superadministrador |
|---|---|---|---|---|
| Monitor / Detección | — | Consultar métricas y eventos (P06–P09) | Consultar y ajustar umbrales dentro del rango (P33) | Todo + límites globales (P33) |
| Incident Manager | — | Analizar, clasificar, escalar (P10, P11) | Gestionar incidentes y aprobar acciones de alto impacto (P32) | Todo |
| Policy Engine | Solicitar elevación (P28) | Ejecutar mitigaciones autorizadas (P12) | Crear/modificar políticas; aprobar elevaciones (P17, P29) | Todo (P26) |
| Controlador SDN | — | Consultar estado (P22-OP, solo lectura) | Operar y administrar reglas y topología (P19, P22-OP) | Todo, incluida la configuración (P22-CFG) |
| IAM/AAA | Autenticarse en el portal (perfil ACADÉMICO) | Autenticarse como operador | Autenticarse como operador | Autenticarse como operador |
| Registro de dispositivos | — | — | Registrar dispositivos con delegación (P30) | Registrar + auditar (P30, P25) |
| Auditoría | — | Consultar eventos y logs (P08) | Consultar | Consultar y auditar todo (P25) |
| Consola | — (no la usa) | Uso con su rol | Uso con su rol | Uso con su rol |

El usuario académico solo aparece en dos celdas: **autenticarse en el portal** y **solicitar elevación**. Todo lo demás le está denegado —en BASE y en ACADÉMICO— y la red lo garantiza con entradas DROP hacia la infraestructura, no con la buena voluntad de la consola.

## 4. Separación de funciones entre roles

Ningún rol concentra definir, aplicar y evaluar una política sin control (fase A, §2.6), y la asignación de componentes la refuerza:

```text
Administrador de Red   crea la política (Policy Engine)
Superadministrador     puede modificarla o revocarla (mismo componente, más permiso)
Especialista de TI     detecta sus efectos y gestiona el incidente
                       (no la modifica)
Auditoría              registra quién hizo qué, independiente de ambos
```

El mismo componente puede ser operado por dos roles con permisos distintos: la separación la imponen los permisos y su registro, no la duplicación de componentes (P4).

## 5. Acciones que exigen intervención humana

La automatización (RT-08) tiene un tope deliberado (P8, P9):

| Acción | Quién la ejecuta | Condición |
|---|---|---|
| RATE_LIMIT ante anomalía leve | Sistema (Policy → Controlador) | Automático, notificado |
| BLOCK ante DDoS severo | Sistema + supervisión del Especialista de TI | Automático con notificación |
| Aislar un segmento completo | Administrador de Red | **Requiere aprobación P32** |
| Elevación temporal de un académico | Administrador de Red | **Requiere aprobación** (P29) |
| Alta en el registro de dispositivos | Administrador de Red / Superadministrador | Requiere registro formal (P30) |
| Política global de la plataforma | Superadministrador | Solo el SA |

## 6. Cuestiones abiertas

- **Delegación del registro de Especialistas de TI.** El Superadministrador puede delegar en el Administrador de Red el registro de Especialistas de TI y sus dispositivos (P30) y la gestión de sus cuentas (P24), con alcance limitado a TI, vigencia explícita y auditoría. La delegación no permite crear otros Administradores de Red ni elevar privilegios propios.
- **Umbrales como política o como configuración técnica.** El Especialista de TI ajusta los umbrales dentro del rango aprobado (P33); el Administrador de Red fija el rango (P33); el Superadministrador fija los límites globales. Cada cambio registra valor anterior, valor nuevo, responsable, fecha y resultado.
