# Estado del proyecto

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** Implementación
**Estado:** Vivo — se actualiza en cada cierre

---

## 1. Avances

| Qué | Dónde | Fecha |
|---|---|---|
| Corpus de diseño A–H completo | [`../../docs/fases/`](../../docs/fases/) | cerrado |
| Etapa 0 de permisos cerrada: matriz 37 × 4, YAML y generador en verde | [`../../implementation/00_cierre_etapa_0_permisos.md`](../../implementation/00_cierre_etapa_0_permisos.md) | 2026-10-28 |
| Etapa 1 documentada: capacidades del switch e inventario del slice | [`../../implementation/04_capacidades_del_switch.md`](../../implementation/04_capacidades_del_switch.md), [`../../implementation/08_inventario_del_slice.md`](../../implementation/08_inventario_del_slice.md) | 2026-10-30 |
| Sondas en sw1: OpenFlow 1.3, 254 tablas, meters, groups, trunk, colas; espejo parcial | [`../../implementation/04_capacidades_del_switch.md`](../../implementation/04_capacidades_del_switch.md) §7 | 2026-10-31 |
| Plan de implementación: perfil de 4 switches (NC1/NC2/A1/A2), 14 VMs, topología L01–L10 | [`../../implementation/05_plan_de_implementacion.md`](../../implementation/05_plan_de_implementacion.md) | 2026-10-31 |
| Planes de trabajo: WP2.0–2.7 y WP3.1–3.8 | [`../../implementation/06_plan_de_trabajo_etapa_2.md`](../../implementation/06_plan_de_trabajo_etapa_2.md), [`../../implementation/07_plan_de_trabajo_etapa_3.md`](../../implementation/07_plan_de_trabajo_etapa_3.md) | cerrado |
| Plan de construcción y este repositorio | [`../../implementation/09_plan_de_construccion.md`](../../implementation/09_plan_de_construccion.md) | 2026-10-31 |
| Paso 0 cerrado: lock con digests, bundles listos (8 imágenes, 1.36 GB) | [`../deploy/images/`](../deploy/images/) | 2026-10-31 |
| Política validada: esquema JSON y validador en verde; YAML v3 (valores de dominio a inglés; `recurso_red` al catálogo; `hard_constraints.requires`); correspondencia corpus↔repo en [`../policy/README.md`](../policy/README.md) | [`../contracts/policy/`](../contracts/policy/), [`../policy/tools/validate.py`](../policy/tools/validate.py) | 2026-10-31 |
| Contratos de eventos: envoltura + 16 esquemas del catálogo | [`../contracts/events/`](../contracts/events/) | 2026-10-31 |
| OpenAPI de I2 (6 rutas) e I7 (14 rutas) | [`../contracts/api/`](../contracts/api/) | 2026-10-31 |
| Stack base S3/S4: Compose validados, roles `base`/`images`/`platform` y `site.yml` | [`../deploy/compose/`](../deploy/compose/), [`../deploy/ansible/`](../deploy/ansible/) | 2026-10-31 |
| Verificación local: PostgreSQL y RabbitMQ en verde (healthy, `bd_politicas`, UI 200) | laptop, con Compose + bundles | 2026-10-31 |
| Mapa del repositorio y tutorial de formatos para el equipo | [`01-mapa.md`](01-mapa.md), [`03-formatos.md`](03-formatos.md) | 2026-10-31 |
| Reglas de implementación y documentación para agentes y autores | [`../CLAUDE.md`](../CLAUDE.md) | 2026-10-31 |
| Pruebas de contrato en verde: 16 tipos + envoltura + rechazos + política (RNF-12) | [`../tests/contract/`](../tests/contract/) | 2026-10-31 |
| Auditoría de idioma: campos de contratos, rutas, valores y pruebas a inglés; correspondencia con el LLD en los README de `contracts/` | [`../CLAUDE.md`](../CLAUDE.md) | 2026-10-31 |
| Paso 3 escrito: roles `onos` (clúster de 3 nodos, `cluster.json` renderizado) y `switches` (OVS, VLANs, controladores); `site.yml` e inventario completos | [`../deploy/ansible/roles/`](../deploy/ansible/roles/) | 2026-10-31 |
| Paso 4, primera mitad: `sdn_common` (app, eventos validados, bus), servicio Portal con I3, Compose de S1 (FreeRADIUS + OpenLDAP); 49 pruebas en verde | [`../services/`](../services/), [`../contracts/api/i3-portal.openapi.yaml`](../contracts/api/i3-portal.openapi.yaml) | 2026-10-31 |
| Paso 4, segunda mitad: servicios IAM (verificación, sesiones, TOTP) y Registry (dispositivos, historial) con pruebas de servicio; 60 pruebas en verde | [`../services/iam/`](../services/iam/), [`../services/registry/`](../services/registry/), [`../tests/integration/`](../tests/integration/) | 2026-10-31 |
| Paso 4, integración: S1 completo en Compose (Portal + IAM + Registry construidos); corte vertical verificado en la laptop: login → sesión → logout extremo a extremo | [`../deploy/compose/s1-identity.yml`](../deploy/compose/s1-identity.yml) | 2026-10-31 |
| Paso 4 cerrado: rol `identity` (construye en la laptop, carga los bundles propios en S1 y levanta el corte); `site.yml` completo | [`../deploy/ansible/roles/identity/`](../deploy/ansible/roles/identity/) | 2026-10-31 |
| Paso 5, primera parte: S2 en Compose (Prometheus y Grafana verificados en la laptop; Suricata espera la NIC del espejo), consumidor del bus con cola, DLQ e idempotencia (roundtrip real: entrega confirmada y duplicado descartado) | [`../deploy/compose/s2-observability.yml`](../deploy/compose/s2-observability.yml), [`../services/common/sdn_common/bus.py`](../services/common/sdn_common/bus.py) | 2026-10-31 |
| Paso 5, ciclo de detección: Monitor y Detección construidos y verificados de extremo a extremo (ráfaga inyectada → `AnomalyDetected` capturado del bus); consumidor resiliente (reintenta si arranca antes del bus); 71 pruebas en verde | [`../services/monitor/`](../services/monitor/), [`../services/detection/`](../services/detection/) | 2026-10-31 |
| Paso 5, ciclo de respuesta: Incidentes y Políticas construidos; cadena completa verificada con contenedores reales — `MetricSample` (ráfaga) → `AnomalyDetected` → `IncidentOpened` (INC-0001) → `MitigationRequired` (RATE_LIMIT, ttl 300); 116 pruebas en verde y la regla de idioma ahora se auto-vigila con una prueba | [`../services/incidents/`](../services/incidents/), [`../services/policies/`](../services/policies/) | 2026-10-31 |
| Paso 5, servicios completos: Auditoría (comodín `#` verificado), Consola (alertas con SSO) y adaptador del sensor (EVE → `MetricSample`); los diez servicios construidos; 138 pruebas en verde | [`../services/`](../services/) | 2026-10-31 |
| Paso 5 cerrado: rol `verify` (salud de los servicios y conteo de switches desde onos1) y `profiles.yaml` derivado con su prueba de sincronía; 141 pruebas en verde y `site.yml` completo | [`../deploy/ansible/roles/verify/`](../deploy/ansible/roles/verify/), [`../policy/profiles.yaml`](../policy/profiles.yaml) | 2026-10-31 |
| IAM corregido al modelo de tres reinos del corpus: comunidad por RADIUS (I4) con accounting, operadores por repositorio propio (bcrypt + TOTP), invitados por registro efímero con TTL que se borra solo (lugar reservado); sesiones con vigencia por perfil (F-03 §5) e invalidación por `MAC_Moved`; 147 pruebas en verde | [`../services/iam/`](../services/iam/), [`../contracts/api/i3-portal.openapi.yaml`](../contracts/api/i3-portal.openapi.yaml) | 2026-10-31 |
| Último eslabón: adaptador I2 (órdenes → flujos ONOS con la escalera del LLD 06_reglas; retiro por cookie; `MitigationApplied`); Políticas envía el comando por I2 y el bus lleva el eco; 161 pruebas en verde | [`../services/controller_adapter/`](../services/controller_adapter/) | 2026-10-31 |
| Runbook del despliegue (el día-D, de las VMs entregadas al entorno verificado) y pruebas de servicio del Portal (11 nuevas; su elevación ahora valida el contrato antes de publicar); 172 pruebas en verde | [`runbooks/01-despliegue-del-slice.md`](runbooks/01-despliegue-del-slice.md), [`../tests/integration/test_portal_service.py`](../tests/integration/test_portal_service.py) | 2026-10-31 |
| VLAN canónica: 10 Usuarios, 20 Servidores, 30 Frontera, 100 Gestión | corpus | cerrado |

## 2. Pendientes

| Pendiente | Plan | Cuándo |
|---|---|---|
| H0: IPs de `ens3`, NICs, espejo hacia el sensor, Docker y Compose | [`04`](../../implementation/04_capacidades_del_switch.md) §5 y [`08`](../../implementation/08_inventario_del_slice.md) | con el slice |
| Re-sonda de cookie/timeouts y sFlow/NetFlow en sw1 | [`04`](../../implementation/04_capacidades_del_switch.md) §7 | con el slice |
| Ejecutar en el slice: clúster ONOS con quórum y 4 switches conectados (roles ya escritos) | [`06`](../../implementation/06_plan_de_trabajo_etapa_2.md) WP2.2–2.3 | paso 3, con el slice |
| Ejecutar en el slice: H0 (IPs, NICs, espejo, Docker) y campaña de la etapa 3 | [`07`](../../implementation/07_plan_de_trabajo_etapa_3.md) | con el slice |

## 3. Cómo se avanza

El orden de construcción está en [`09`](../../implementation/09_plan_de_construccion.md) §7: los pasos 0 y 1 no dependen del slice y se ejecutan ya; los pasos 2–5 se escriben ahora y se ejecutan cuando las 14 VMs estén disponibles. La primera acción con el slice es H0, antes de cualquier despliegue.
