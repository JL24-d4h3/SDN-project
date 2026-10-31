# Plan de pruebas del modelo de permisos

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** Implementación — Etapa 0
**Estado:** Borrador formal para revisión

---

## 1. Objetivo

Demostrar que el modelo de permisos decide correctamente, que las decisiones se aplican en los servicios y en el switch, y que las invariantes de seguridad se cumplen incluso cuando fallan atributos o componentes. El plan cubre la lógica de decisión y su enforcement; no cubre el rendimiento de la plataforma, que se mide en la fase de prototipo.

## 2. Alcance

| Incluido | Excluido |
|---|---|
| Catálogo P01–P36 y matriz de 78 asignaciones | Interfaz gráfica del portal |
| Condiciones C1–C11 y estados de seguridad | IdP institucional real |
| Decisiones PERMITIR, DENEGAR, ELEVAR y CUARENTENA | Carga y estrés |
| Obligaciones de auditoría y TTL | Pruebas de penetración externas |
| Enforcement en el switch para cinco flujos | Rendimiento del controlador |
| Perfiles BASE, ACADÉMICO, OPERADOR_* y ELEVACIÓN | Disponibilidad geográfica |

## 3. Niveles de prueba

```text
L0  Esquema y consistencia del YAML
L1  Unidad de decisión (condiciones, roles, recursos)
L2  Invariantes de seguridad (propiedades que nunca se violan)
L3  Integración de API (cada servicio, cada permiso)
L4  Enforcement en el switch (perfil → FLOW_MOD)
L5  Extremo a extremo (flujos completos de la plataforma)
L6  Cobertura y mutación (calidad de la suite)
```

### L0. Esquema y consistencia

- El YAML se valida con `generar_matriz.py`: claves obligatorias, tipos, enumeraciones y referencias.
- No hay identificadores duplicados de permisos, roles, condiciones ni asignaciones.
- Toda asignación referencia un rol, un permiso y condiciones existentes.
- Toda celda `Cxx` de la matriz existe en el YAML.
- Todo permiso P01–P36 y P22-CFG aparece exactamente una vez en el catálogo.
- La matriz del documento coincide con las asignaciones del YAML (`generar_matriz.py --check`).

Herramientas: `pytest`, `jsonschema` cuando el entorno lo provea, `generar_matriz.py`.

### L1. Unidad de decisión

Cada prueba construye un sujeto, una acción, un recurso, un contexto, un estado y una vigencia, y compara la decisión con la esperada.

| Grupo | Casos representativos |
|---|---|
| Académico | P03 permitido con C9; P03 denegado si el recurso no está en su lista; P06 denegado; P28 permitido. |
| TI | P12 permitido con C7; P12 denegado si la severidad supera el umbral y no hay P32; P22-OP permitido solo en lectura; P15 denegado. |
| Administrador | P13 permitido; P24 denegado sin delegación; P24 permitido con delegación vigente; P29 denegado si es el solicitante. |
| Superadministrador | P22-CFG permitido en ventana; denegado fuera de ventana sin emergencia; P25 permitido; P36 permitido. |
| Contexto | P22-CFG denegado si `time_window` no es mantenimiento ni emergencia; P31 denegado si la sesión no es propia. |
| Vigencia | Elevación denegada si el TTL expiró; aprobación denegada si expiró; delegación denegada si `valid_until` pasó. |
| Estado | Sujeto en cuarentena denegado para P03; permitido para el portal de remediación; segmento aislado denegado; incidente activo exige P32. |

### L2. Invariantes

Las invariantes se prueban con propiedades generadas sobre el YAML, no con casos aislados.

| ID | Invariante | Prueba |
|---|---|---|
| I-01 | Denegación por defecto | Un rol sin asignación para Pxx recibe DENEGAR. |
| I-02 | Precedencia de denegación | Si coexisten permit y deny, gana deny. |
| I-03 | Sin autoaprobación | Para todo par (solicitante, aprobador) con el mismo id, P29 y P32 deniegan. |
| I-04 | Sin autoelevación | P15, P16 y P24 deniegan cuando el sujeto es el objetivo. |
| I-05 | Sin privilegio por unión | La unión de roles no produce permisos fuera del mayor nivel. |
| I-06 | Delegación vigente | P14, P24 y P30 sin delegación vigente deniegan para el Administrador. |
| I-07 | TTL obligatorio | Toda elevación o mitigación sin TTL deniega. |
| I-08 | Estado de seguridad | Sujeto comprometido, en cuarentena o suspendido no recibe permisos privilegiados. |
| I-09 | Fallo seguro | Si falta un atributo obligatorio, la decisión es DENEGAR con motivo `atributo_faltante`. |
| I-10 | Auditoría | Toda decisión PERMITIR o DENEGAR produce un registro con sujeto, permiso, recurso y motivo. |
| I-11 | Sin secretos | Los eventos y logs no contienen claves, tokens ni contraseñas. |
| I-12 | Break-glass | P14 deniega sobre cuentas break-glass. |
| I-13 | Registro no concede | P30 y P35 no cambian el rol ni el perfil del dispositivo. |
| I-14 | Detección separada | TI no puede ejecutar P18 ni desactivar la detección. |
| I-15 | Auditoría separada | Solo el Superadministrador posee P25 y P36. |

### L3. Integración de API

Cada servicio expone sus operaciones y cada operación declara el permiso que exige. La prueba recorre el mapa `endpoint → permiso` y verifica:

- Sin sesión: 401.
- Sesión sin permiso: 403 con motivo.
- Sesión con permiso: 200 y obligación de auditoría.
- Permiso condicional: 200 solo con los atributos que cumplen la condición.
- Permiso con step-up: 403 con `requiere_step_up` y, tras completar el paso, 200.
- Recurso de otro ámbito: 403.
- Sesión expirada: 401.
- Estado de seguridad bloqueante: 403.

| Servicio | Permisos principales |
|---|---|
| Portal | P01, P02, P03 |
| IAM | P01, P15, P31 |
| Registro | P30, P35 |
| Monitor | P04, P06, P07 |
| Detección | P08, P09, P33 |
| Incidentes | P10, P11, P12, P13, P32 |
| Políticas | P17, P18, P19, P20, P23 |
| Auditoría | P25, P36 |
| Consola | P03, P04, P05 |
| Adaptador del sensor | P08, P09 |

La prueba usa `httpx` contra el servicio en un contenedor y una base PostgreSQL efímera. Los eventos se publican en RabbitMQ y se verifica su entrega y su idempotencia.

### L4. Enforcement en el switch

La decisión de red se materializa como FLOW_MOD. La prueba verifica la regla instalada, no solo la respuesta de la API.

| Flujo | Verificación |
|---|---|
| BASE | Portal con prioridad 150, DHCP/DNS con 10, DROP a gestión con 100, anti-spoofing con 110. |
| ACADÉMICO | Regla de sesión con prioridad 190, cookie `0x01`, `idle_timeout` configurado. |
| OPERADOR | Regla de sesión con prioridad 200, match de dispositivo y destino de gestión. |
| ELEVACIÓN | Regla temporal con prioridad 200, cookie `0x01`, `hard_timeout` igual al TTL. |
| Mitigación | Regla con prioridad 1000, cookie `0x02`, `hard_timeout` igual al TTL; vence a la sesión. |
| Retiro | Al expirar o revocar, la regla desaparece y no quedan residuos. |

Interfaz de prueba:

```text
SwitchClient
  add_flow(switch, flow)
  delete_flow(switch, cookie)
  dump_flows(switch)
  dump_meters(switch)
  dump_groups(switch)
```

Implementaciones: `OvsSwitchClient` para el laboratorio con OVS y `PicosSwitchClient` para Pica8. En integración continua se usa un simulador de flujos; la aceptación se hace contra el switch real del slice.

### L5. Extremo a extremo

| Escenario | Resultado esperado |
|---|---|
| Académico se autentica en el portal | Sesión, perfil ACADÉMICO, regla 190, auditoría. |
| Académico sin registro intenta consola | Denegado; solo portal. |
| TI detecta y mitiga un nodo | Alerta, incidente, mitigación 1000, TTL, auditoría. |
| TI intenta una acción de alto impacto | Step-up P32; sin aprobación, denegado. |
| Administrador aprueba una cuarentena | Aprobación vinculada, ejecución, cierre, auditoría. |
| Administrador intenta aprobar su propia solicitud | Denegado por C4. |
| Académico solicita elevación de laboratorio | P28, aprobación P29, perfil ELEVACIÓN con TTL 30 min. |
| Elevación expira | La regla se retira; el perfil vuelve a ACADÉMICO. |
| Superadministrador configura el controlador | Permitido en ventana, cambio registrado. |
| Superadministrador configura fuera de ventana | Denegado; emergencia declarada permite con auditoría reforzada. |
| Dispositivo en cuarentena intenta acceder | Denegado; solo portal de remediación. |
| Sujeto suspendido intenta autenticarse | Denegado salvo P01. |

### L6. Cobertura y mutación

| Métrica | Umbral |
|---|---|
| Permisos con al menos un caso allow y uno deny | 100 % |
| Condiciones con al menos un caso que falla | 100 % |
| Cobertura de ramas del evaluador | ≥ 90 % |
| Mutantes del evaluador detectados | ≥ 80 % |
| Asignaciones cubiertas por una prueba | 100 % |
| Invariantes con prueba automática | 15 de 15 |

## 4. Datos de prueba

```text
fixtures/
  roles.yaml          # 4 roles con atributos
  resources.yaml      # recursos por tipo, propietario y ámbito
  contexts.yaml       # sesión, ambiental y recurso
  states.yaml         # estados de seguridad del sujeto y del entorno
  delegations.yaml    # delegación vigente y vencida
  requests.yaml       # pares (sujeto, permiso, recurso) esperados
```

Los fixtures no contienen secretos. Las credenciales de prueba se generan en el arranque y se destruyen al terminar.

## 5. Entornos de ejecución

| Entorno | Qué ejecuta | Dónde |
|---|---|---|
| Local | L0, L1, L2, L6 | Máquina de desarrollo, sin red |
| Integración | L3, L5 | Contenedores con PostgreSQL y RabbitMQ |
| Laboratorio | L4 | Switch del slice y controlador |
| Aceptación | L0–L5 | Slice completo |

Comandos:

```bash
pytest -m "l0 or l1 or l2"        # rápido, sin red
pytest -m "l3 or l5"             # requiere contenedores
pytest -m "l4"                   # requiere switch y controlador
pytest --cov=policy --cov-report=term-missing
```

## 6. Criterios de aceptación

1. L0 pasa sin errores y el YAML valida contra el esquema.
2. Las 78 asignaciones tienen al menos una prueba de allow y una de deny.
3. Las 11 condiciones tienen al menos una prueba de fallo.
4. Las 15 invariantes pasan.
5. Los 12 escenarios extremo a extremo pasan en el slice.
6. Los 6 flujos de enforcement se verifican en el switch real.
7. La cobertura de ramas del evaluador es ≥ 90 % y la mutación ≥ 80 %.
8. No hay secretos en eventos, logs ni fixtures.
9. La matriz generada desde el YAML coincide con la matriz revisada.

## 7. Riesgos de la suite

| Riesgo | Mitigación |
|---|---|
| El switch del slice no soporta alguna función | Prueba de capacidades previa y degradación documentada en [`04_capacidades_del_switch.md`](04_capacidades_del_switch.md). |
| El controlador no expone todos los contadores | Verificar por `ovs-ofctl` o por el CLI del switch. |
| Los contenedores no tienen PostgreSQL | Usar una base efímera en el host de pruebas. |
| El IdP no está disponible | Usar el repositorio local de identidades del prototipo. |
| Las pruebas de switch son lentas | Ejecutarlas en el laboratorio, no en cada commit. |

## 8. Trazabilidad

| Requisito | Prueba |
|---|---|
| Control de acceso por rol | L1, L2, L3 |
| Separación de funciones | I-03, I-04, L5 |
| Elevación temporal | I-07, L4, L5 |
| Mitigación con prioridad | L4, L5 |
| Auditoría | I-10, L3, L5 |
| Cuarentena | I-08, L5 |
| Perfiles de red | L4, L5 |
| Registro de dispositivos | I-13, L3 |
| Detección y respuesta | L3, L5 |
