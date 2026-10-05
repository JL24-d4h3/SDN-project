# Interfaces

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** G — Diseño de bajo nivel (LLD)
**Estado:** Borrador formal para revisión

---

Las **interfaces son los contratos entre componentes** ([`D-07`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/07_interfaces_principales.md)): I1 a I8 definen qué fluye entre qué partes. Las que hablan HTTP quedaron en [`01`](01_apis.md) (I2, I3, I7), el bus en [`02`](02_eventos.md) (I5) y la persistencia en [`03`](03_datos.md) (I6). Este documento detalla **la forma operativa de las restantes** —las que hablan protocolos de infraestructura—: el southbound (I1), la identidad institucional (I4), la observación (I8), y los dos canales auxiliares del perímetro y del tiempo que el sistema necesita para operar.

## 2. I1 — Southbound: el canal de control

**Lo general:** el controlador habla con los switches por OpenFlow 1.3 sobre TCP 6653, fuera de banda (RP-02). Es un canal de **comandos con confirmación y eventos asíncronos**: el controlador ordena, el switch confirma y reporta (D-07 I1).

**La forma operativa:**

| Aspecto | Valor inicial |
|---|---|
| Transporte | TCP 6653, por las interfaces de gestión (`ma1`) de cada switch — nunca por el plano de datos |
| Autorización | El switch acepta control solo de los endpoints de controlador configurados (whitelist); una conexión desde otra interfaz se rechaza (verificación V6, [`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §4) |
| Latido | `ECHO` cada 5 s; sin respuesta en 3 latidos, el canal se declara caído |
| Confirmación de aplicación | `OFPT_BARRIER_REQUEST/REPLY` tras cada lote de instalación — es lo que sostiene el nivel `APLICADA` de I2 ([`01`](01_apis.md) §2) |
| Cookies | El controlador mantiene el **registro string ↔ 64 bits**: la cookie que los servicios nombran (`SES-…`, `INC-…`) se traduce al valor OpenFlow; el retiro por cookie usa la traducción inversa ([`06`](06_reglas.md) §3) |
| Multipart | `OFPMP_PORT_STATS`, `OFPMP_FLOW`, `OFPMP_METER_CONFIG`, `OFPMP_GROUP_DESC` — la única fuente de observación del plano de datos (P11) |
| Failover (clúster) | Cada switch lleva configurados los tres endpoints del clúster ONOS ([`F-01`](../F-Decisiones_tecnologicas/01_controlador_y_api_northbound.md) §6); en el prototipo uno solo está desplegado — el mecanismo se documenta, no se ejerce |

La negociación inicial (`HELLO`, `FEATURES_REPLY`) fija lo que el switch **declara** soportar; el controlador no puede ordenar más de lo declarado (P1, RP-11). Las verificaciones V1–V7 de [`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §4 son el acta de esa negociación contra el dispositivo real.

## 3. I4 — Identidad institucional: RADIUS y el directorio

**Lo general:** el IAM consume la identidad de la comunidad del IdP institucional; el prototipo **simula al IdP, no al protocolo** — FreeRADIUS con OpenLDAP detrás, lo mismo que una universidad real ejecuta ([`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §2).

**La forma operativa:**

| Aspecto | Valor inicial |
|---|---|
| Puertos | `1812/udp` (autenticación), `1813/udp` (accounting), en el segmento de gestión |
| Cliente RADIUS | Solo el IAM, con secreto compartido propio; otro origen se descarta |
| Autenticación | `Access-Request` (usuario, contraseña) → FreeRADIUS valida contra OpenLDAP → `Access-Accept/Reject` |
| Atributos | `Access-Accept` devuelve el perfil como atributo (`Class` o VSA del prototipo) — el IAM traduce identidad + atributos a la tupla del Policy Engine (D-07 I4) |
| Accounting | `Accounting-Request` `Start` · `Interim` cada 300 s · `Stop`, con `Acct-Session-Id = sesion_id` — el registro AAA que R1.9 exige y que correlaciona la auditoría |
| Directorio | Bind de servicio **de solo lectura**; árbol del prototipo (`ou=comunidad` con las cuentas de prueba); índice sobre `uid` |
| Timeouts | 3 s por intento, 2 reintentos, y el login falla — el IdP es síncrono, la persona espera (D-08 §2) |

Las credenciales de la comunidad nunca atraviesan la plataforma más allá de este intercambio: el IAM no las almacena (D-07 I4). El reino de operadores no usa esta interfaz: vive en el repositorio propio con TOTP ([`03`](03_datos.md) §3).

## 4. I8 — Observación: el sondeo de contadores

**Lo general:** el Monitor observa el plano de datos **solo a través del controlador** — nunca habla con los switches (P1, D-07 I8). Su producto es la materia prima de la Detección.

**La forma operativa:**

| Aspecto | Valor inicial |
|---|---|
| Camino | Monitor → I2 (`GET /api/v1/contadores`) → controlador → `MULTIPART` → switch |
| Conjunto caliente | Cada **5 s**: contadores de los destinos protegidos y de sus puertos de ingreso ([`F-06`](../F-Decisiones_tecnologicas/06_deteccion_y_mitigacion.md) §2) |
| Barrido completo | Cada **60 s**: inventario completo de flujos y puertos |
| Lote | Una consulta por switch, no una por flujo — la carga sobre el plano de control es la que RNF-03 mide |
| Tolerancia | Si el controlador no responde en 2 s, la ventana se registra como **hueco de observación** — la línea base no se inventa (P11) |
| Frecuencias | Configurables por parámetro (I7) — el barrido 5/30/60 s es el experimento de RNF-03 |

Un destino que despierta interés entra al conjunto caliente a partir del siguiente barrido completo.

## 5. Canales auxiliares: el espejo del perímetro y el tiempo

**El espejo** alimenta al sensor perimetral: un puerto del switch de borde replica el tráfico del segmento externo hacia la interfaz dedicada de la máquina virtual del sensor — materializada con Suricata ([`F-07`](../F-Decisiones_tecnologicas/07_perimetro_r5.md) §3). El sensor está **fuera del camino de reenvío** (P8): recibe una copia, nunca interpone. Su NIC de espejo es de solo recepción — el sensor no emite por donde observa. La asignación física del puerto está en [`H-05`](../H-Despliegue/05_puertos.md).

**El tiempo** firma todo registro (RNF-09): un servidor chrony del prototipo es la fuente; todos los nodos son clientes; todo timestamp es UTC ([`F-05`](../F-Decisiones_tecnologicas/05_persistencia_auditoria_y_tiempo.md) §5). El tiempo **no** viaja por el plano de datos: la sincronización va por el segmento de gestión. Un servicio que no puede sincronizar no firma tiempo — no firma tiempo falso (P11).

## 6. Qué no son interfaces

Sin cambios respecto de D-07 §3: ningún servicio habla con los switches directamente; la Consola no toca bases; la Detección no ordena al controlador; 802.1X queda reservado para puertos sensibles de un despliegue real ([`H-01`](../H-Despliegue/01_infraestructura_fisica.md) §4). Lo que este documento detalla da forma operativa a los contratos de D — no crea ninguno nuevo.

## 7. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| `FEATURES_REPLY` y negociación contra el switch real | Lo declarado = lo usado (V1) | P1, RP-11 |
| Conexión de control rechazada desde otra interfaz (V6) | El canal es solo de gestión | RA-09 |
| `Access-Request` con accounting completo | Sesión con `Acct-Session-Id` correlacionable | R1.9, I4 |
| Sondeo 5/60 s con hueco simulado (controlador detenido) | Hueco declarado, línea base intacta | P11, RNF-03 |
| Desfase de reloj de todos los nodos | Máximo desfase observado (NTP) | RNF-09, E-05 |
| Espejo activo con tráfico externo generado | El sensor ve una copia fiel y no interpone | R5, P8 |
