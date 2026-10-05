# Configuraciones

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** G — Diseño de bajo nivel (LLD)
**Estado:** Borrador formal para revisión

---

La **configuración es el estado declarado del sistema**: todo lo que no es código queda en configuración, versionada y reproducible ([`F-08`](../F-Decisiones_tecnologicas/08_entorno_del_prototipo.md) §4, RNF-11). Dos clases, con reglas distintas:

- **Identidad y seguridad** — secretos, credenciales y claves. **Nunca** en el repositorio del código ni en texto claro en disco compartido: variables de entorno o almacén de secretos del entorno, y rotación por procedimiento.
- **Comportamiento** — parámetros que este LLD fija con **valores iniciales** (los definitivos los calibra la medición, P12) y que se ajustan por la vía administrativa (I7), quedando **quién** los cambió en auditoría.

Todo parámetro de este documento lleva su origen: nada se inventa aquí, se aterriza lo que F decidió.

**La jerarquía de cada sección** es la de toda la fase: primero el **papel** que el sistema necesita y, entre paréntesis, el **producto** que lo materializa — el papel manda, el producto lo sirve. Las dos clases de §1 atraviesan todos los productos.

## 2. El controlador (ONOS)

| Parámetro | Valor inicial | Origen |
|---|---|---|
| Modo de operación | OpenFlow 1.3, un pipeline por dispositivo | [`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §2 |
| Endpoints de control (switches) | `tcp:10.0.0.20:6653` + dos endpoints de reserva del clúster (documentados, no desplegados) | [`F-01`](../F-Decisiones_tecnologicas/01_controlador_y_api_northbound.md) §6 |
| Northbound (I2) | REST habilitado solo en la interfaz de gestión; clave de servicio por cliente | [`01`](01_apis.md) §2 |
| Registro de cookies | tabla string ↔ 64 bits, persistida | [`06`](06_reglas.md) §3 |
| Inventario de servicios | anclajes declarados por I2, base del grafo | [`01`](01_apis.md) §4 |
| Registro de asociaciones | MAC ↔ switch:puerto ↔ IP por dispositivo aprendido | P7, [`F-01`](../F-Decisiones_tecnologicas/01_controlador_y_api_northbound.md) §5 |

## 3. El plano de datos (PicOS)

| Parámetro | Valor inicial | Origen |
|---|---|---|
| Modo | OpenFlow 1.3 dedicado (el pipeline SDN no convive con L2 autónomo en los puertos de acceso) | [`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §2 |
| Canal de control | interfaz `ma1`, whitelist del controlador, `ECHO` 5 s | [`04`](04_interfaces.md) §2 |
| Puerto espejo | replicación del segmento externo hacia el puerto del sensor | [`F-07`](../F-Decisiones_tecnologicas/07_perimetro_r5.md) §3 |
| Buffer | `PACKET_IN` con `buffer_id` utilizable (V7); la redirección usa el mecanismo que V3/V4 firme | [`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §4 |
| Tablas | una por etapa del pipeline si V1 confirma multi-tabla; si no, entradas compuestas | [`06`](06_reglas.md) §2 |

## 4. El intermediario (RabbitMQ)

| Parámetro | Valor inicial | Origen |
|---|---|---|
| Vhost / exchange | `plataforma` / exchange `plataforma` (topic, durable) | [`F-04`](../F-Decisiones_tecnologicas/04_mensajeria_y_eventos.md) §3 |
| Usuarios | uno por servicio, permisos solo sobre sus colas | P3 |
| Política de colas por servicio | durable; límite de longitud 100 000; DLX hacia su `dlq.<cola>` | [`02`](02_eventos.md) §5 |
| Política de colas por incidente | `inc.*` durable, TTL de respaldo 24 h, auto-borrado al cierre | [`F-04`](../F-Decisiones_tecnologicas/04_mensajeria_y_eventos.md) §3 |
| Confirmación de publicación | activada; buffer local del cliente 10 000 | [`F-04`](../F-Decisiones_tecnologicas/04_mensajeria_y_eventos.md) §4 |
| Reintentos | 5 con retroceso 1 s → 60 s, luego DLQ | [`02`](02_eventos.md) §5 |

## 5. La persistencia (PostgreSQL)

| Parámetro | Valor inicial | Origen |
|---|---|---|
| Instancias | una única instancia, seis bases, un usuario por base sin grants cruzados | [`F-05`](../F-Decisiones_tecnologicas/05_persistencia_auditoria_y_tiempo.md) §2 |
| Conexiones | pool por servicio, límite por usuario | P3 |
| Respaldo | `pg_dump` diario del volumen; drill de restauración programado | [`F-05`](../F-Decisiones_tecnologicas/05_persistencia_auditoria_y_tiempo.md) §4 |
| Retenciones | auditoría 90 días; contadores 24 h / 7 días agregados | [`03`](03_datos.md) §3 |

## 6. La identidad (FreeRADIUS + OpenLDAP)

| Parámetro | Valor inicial | Origen |
|---|---|---|
| Cliente RADIUS | solo el IAM, con secreto compartido propio | [`04`](04_interfaces.md) §3 |
| Puertos | 1812/1813 UDP, segmento de gestión | [`04`](04_interfaces.md) §3 |
| Accounting | `Interim` cada 300 s; `Acct-Session-Id = sesion_id` | [`04`](04_interfaces.md) §3 |
| Directorio | bind de solo lectura; árbol `ou=comunidad` con cuentas de prueba; índice `uid` | [`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §2 |
| TOTP | RFC 6238, ventana ±1, secreto cifrado en `bd_iam` | [`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §3 |

## 7. El sensor perimetral y su adaptador

| Parámetro | Valor inicial | Origen |
|---|---|---|
| Modo | IDS sobre interfaz de espejo; nunca en el camino (ni IPS inline) | [`F-07`](../F-Decisiones_tecnologicas/07_perimetro_r5.md) §2 |
| Reglas | lista propia con `vigencia` y `responsable` por firma; la regla de promoción de nuevas firmas | [`F-07`](../F-Decisiones_tecnologicas/07_perimetro_r5.md) §4 |
| Salida | `eve.json` → adaptador → evento `AnomalyDetected` con origen `perimetro` | [`F-07`](../F-Decisiones_tecnologicas/07_perimetro_r5.md) §3 |
| Feeds externos | ninguno en el prototipo (RP-06); el punto de integración queda para el despliegue | [`F-07`](../F-Decisiones_tecnologicas/07_perimetro_r5.md) §4 |

## 8. Sesión, portal y consola

| Parámetro | Valor inicial | Origen |
|---|---|---|
| Cookie de sesión | opaca, `HttpOnly` · `Secure` · `SameSite=Lax`; validez en servidor | [`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §4 |
| Token derivado | vida corta, misma vigencia y ligadura que la sesión | [`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §4 |
| Vigencias | ACADÉMICO 30 min idle / 12 h tope · operador 15 min / 8 h · elevación 1 h | [`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §5 |
| TLS | certificados del laboratorio en gestión; el portal es HTTPS siempre | RA-09 |
| Selector | explícito, en la entrada del portal; no concede nada | [`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §6 |

## 9. Observación y visualización

| Parámetro | Valor inicial | Origen |
|---|---|---|
| Frecuencias de I8 | conjunto caliente 5 s · barrido 60 s · configurables | [`F-06`](../F-Decisiones_tecnologicas/06_deteccion_y_mitigacion.md) §2 |
| Detección | α = 0,2 · ventana 5 s · N = 3 · k 4σ/2σ · piso 200 pps / 2 Mbps · calentamiento 30 min | [`F-06`](../F-Decisiones_tecnologicas/06_deteccion_y_mitigacion.md) §3 |
| Clasificación | flood ≥ k·σ + piso · distribuido ≥ 10 fuentes/60 s · brute-force ≥ 20 req/s · scanning > 20 destinos/60 s | [`F-06`](../F-Decisiones_tecnologicas/06_deteccion_y_mitigacion.md) §4 |
| Tiempo | chrony, fuente 10.0.0.25, UTC en todo registro | [`F-05`](../F-Decisiones_tecnologicas/05_persistencia_auditoria_y_tiempo.md) §5 |
| Grafana | datasources `bd_monitor` y `bd_auditoria` con usuario de **solo lectura**; dashboards versionados | [`F-05`](../F-Decisiones_tecnologicas/05_persistencia_auditoria_y_tiempo.md) §6 |

## 10. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Recrear todo el entorno desde la definición versionada | Sin pasos manuales | RNF-11 |
| Ajustar un umbral por I7 | El cambio aplica, se audita con su autor | P12, R1.9 |
| Acceso con credenciales de configuración fuera de gestión | Rechazo | RA-09 |
| Drill de restauración de la persistencia | Recuperación completa en el tiempo medido | F-05, E-04 |
| Desfase de reloj entre nodos | El máximo observado | RNF-09 |
