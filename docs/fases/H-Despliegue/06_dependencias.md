# Dependencias

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** H — Despliegue
**Estado:** Borrador formal para revisión

---

El **orden de arranque es un grafo de dependencias**, y el grafo sigue un principio de capas: **tiempo → identidad → estado → política → observación.** Primero lo que firma los registros (el tiempo), después lo que guarda y transporta (persistencia e intermediario), después lo que gobierna la red (controlador y switches), después lo que decide (identidad y servicios), después lo que observa y muestra. El apagado es el inverso, con una excepción: la auditoría exporta su retención antes de detenerse.

La razón de fondo es el **arranque degradado** (P2): la red no depende de los servicios — un servicio que no arranca no tumba lo que ya está instalado en los switches. El grafo describe quién espera a quién **para arrancar correctamente**, no quién detiene a quién al fallar. El grafo y las tablas hablan de **papeles**; los productos que materializan cada papel están en la columna «Se materializa con» y en §4.

## 2. El grafo

```text
TIEMPO ──────────────► PERSISTENCIA ────────► IDENTIDAD (IdP simulado)
   │                       │                        │
   │                       ├──────► INTERMEDIARIO   │
   │                       │           │            │
   ▼                       ▼           ▼            ▼
(todos los nodos     CONTROLADOR + switches    SERVICIOS DE LA PLATAFORMA
 con hora común)     (canal de control)        (IAM · Registro · Incidentes ·
                                               Políticas · Auditoría · Monitor ·
                                               Detección · Portal · Consola)
                                                        │
                                SENSOR PERIMETRAL + VISUALIZACIÓN ──► verificación
```

| Componente | Se materializa con | Depende de | Si falta su dependencia |
|---|---|---|---|
| Tiempo | chrony | nada | Los servicios que firman tiempo **esperan** — no se firma tiempo falso (P11) |
| Persistencia | PostgreSQL | Tiempo (timestamps de transacción) | Los servicios quedan en *not ready*; la red opera igual (P2) |
| Intermediario | RabbitMQ | Tiempo | Los publicadores operan con buffer local y huecos declarados ([`G-02`](../G-Diseno_de_bajo_nivel-LLD/02_eventos.md) §5) |
| Controlador + switches | ONOS + PicOS | red de gestión | Sin controlador, los switches conservan lo instalado y todo expira por timeout (P2, P10) — no hay decisiones nuevas hasta el re-registro |
| Identidad institucional | FreeRADIUS + OpenLDAP | Persistencia (sus datos) | El login de la comunidad falla; el reino operadores (repositorio propio) sigue |
| IAM | imagen propia | Persistencia, Intermediario, Identidad | Sin sesiones nuevas; las vigentes siguen hasta su timeout |
| Registro, Incidentes, Políticas, Auditoría | imagen propia | Persistencia, Intermediario | Sin su base no arrancan (*not ready*); la cadena de detección espera, la red no |
| Monitor, Detección | imagen propia | Intermediario (Monitor además: I2) | Sin observación no hay detección nueva; las mitigaciones vigentes siguen |
| Portal, Consola | imagen propia | IAM (sesiones), sus bases | Sin login ni consola; el plano de datos no se entera |
| Sensor perimetral y su adaptador | Suricata + adaptador propio | espejo activo, Intermediario | Sin sensor, el perímetro pierde detección (R5) — declarado, no silencioso |
| Visualización | Grafana | bd_monitor, bd_auditoria (lectura) | Sin tableros; la observación cruda sigue |

## 3. La secuencia de arranque

1. **Tiempo (chrony)** — todos los nodos sincronizan antes de operar; el desfase se verifica (RNF-09).
2. **Persistencia (PostgreSQL)** — las seis bases; chequeo `pg_isready` por base.
3. **Intermediario (RabbitMQ)** — vhost `plataforma`, exchange, colas y políticas ([`G-02`](../G-Diseno_de_bajo_nivel-LLD/02_eventos.md) §4).
4. **Controlador (ONOS) + switches (PicOS)** — configuración scriptada del plano de datos (modo OpenFlow, canal, espejo), `HELLO`/`FEATURES_REPLY`, whitelist; el esqueleto de dispositivos conocidos se reinstala.
5. **Identidad institucional (FreeRADIUS + OpenLDAP)** — cuentas de prueba, `radtest` de control.
6. **Servicios de la plataforma** — IAM, Registro, Incidentes, Políticas, Auditoría, Monitor, Detección, Portal, Consola; cada uno declara `/health` *ready*.
7. **Sensor perimetral + visualización** — el sensor confirma el espejo; los tableros cargan sus datasources.
8. **Verificación de arranque** — un `PACKET_IN` de prueba recorre aprendizaje → esqueleto → portal; un evento de prueba recorre el bus end-to-end. Recién entonces el entorno se declara operativo.

**El apagado** invierte el orden, con la auditoría antes que su base: export JSONL del rango pendiente, cierre del bus (drenaje de colas), parada de servicios, del controlador y de la persistencia.

## 4. Versiones fijadas

Cada papel se materializa con un producto, y cada producto queda **fijado por versión** en la definición versionada del despliegue (RNF-11) — punto de partida, registrado en el primer despliegue:

| Papel | Producto | Versión (punto de partida) |
|---|---|---|
| Controlador | ONOS | 2.7 LTS |
| Persistencia | PostgreSQL | 16 |
| Intermediario | RabbitMQ | 3.13 |
| Identidad | FreeRADIUS · OpenLDAP | 3.2 · 2.6 |
| Sensor | Suricata | 7 |
| Tiempo | chrony | 4.5 |
| Visualización | Grafana | 11 |
| Servicios propios | Python | 3.12 |

Una repetición futura no compara contra otro software ([`F-08`](../F-Decisiones_tecnologicas/08_entorno_del_prototipo.md) §4); un cambio de versión es un cambio de despliegue, registrado como tal.

## 5. Las ventanas del laboratorio

El hardware del laboratorio no está siempre disponible (RP-11): la secuencia de arranque **física** corre dentro de las ventanas planificadas ([`01`](01_infraestructura_fisica.md) §2); fuera de ellas, el apoyo virtual ([`F-08`](../F-Decisiones_tecnologicas/08_entorno_del_prototipo.md) §1) levanta la misma secuencia con sus límites declarados — las pruebas de primitivas y capacidad se firman siempre contra el switch físico.

## 6. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Arranque completo desde cero con la secuencia de §3 | Tiempo total; todo *ready* en orden | RNF-11 |
| Apagado ordenado y re-arranque | Nada corrupto; auditoría exportada antes de detenerse | F-05 |
| Arranque degradado: sin intermediario | Publicadores con buffer local; huecos declarados | P13, E-04 |
| Arranque degradado: sin controlador | Lo instalado sigue operando y expira por timeout | P2, P10 |
| Caída y retorno del Incident Manager | Reconciliación contra el plano de datos | E-04, P10 |
| Desfase de reloj tras el arranque | Todos los nodos con hora común | RNF-09 |
