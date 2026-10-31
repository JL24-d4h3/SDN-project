# Despliegue del slice

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** Implementación — Despliegue
**Estado:** Vivo — se ajusta con lo que el slice confirme

---

Procedimiento completo para llevar campus-sdn a las 14 VMs del slice: desde las VMs recién entregadas hasta el entorno verificado. Cada fase tiene su criterio de salida; no se abre la siguiente sin cerrar la anterior. Los comandos se ejecutan en la laptop (nodo de control), salvo que se indique lo contrario.

## 1. Prerrequisitos

| Prerrequisito | Cómo se confirma |
|---|---|
| Acceso VPN al slice y credenciales SSH | poder entrar a una VM |
| Ansible en la laptop (`ansible-playbook`) | `ansible-playbook --version` |
| Bundles de imágenes listos | `make images-verify` en verde |
| `.venv` del repositorio | `make test` en verde |
| Inventario real `slice.yml` con las IPs de `ens3` | fase 2 |
| Secretos en Ansible Vault o en el entorno | fase 2 |

## 2. Fase H0 — inventario y capacidades

Con las 14 VMs entregadas, antes de tocar nada:

1. **Inventario por nodo.** Copiar y ejecutar [`inventario_slice.sh`](../../implementation/inventario/inventario_slice.sh) en cada VM y cada switch (en switches, con `sudo`), como indica [`08_inventario_del_slice.md`](../../implementation/08_inventario_del_slice.md) §3. Guardar cada salida.
2. **Re-sonda del switch** (`sw1` u OVS del slice): `sudo ./inventario_slice.sh --probe` — cierra las pendientes de cookie/timeouts y sFlow/NetFlow de [`04_capacidades_del_switch.md`](../../implementation/04_capacidades_del_switch.md) §7.
3. **NIC del espejo.** Confirmar qué interfaz de S2 recibe el tráfico del espejo (L09, NC2 → S2). Si el hipervisor no la expone, aplicar el orden de reemplazo de [`04_capacidades_del_switch.md`](../../implementation/04_capacidades_del_switch.md) §4.3.
4. **Registro.** Volcar los resultados en la tabla de verificación de `04` §7 (columna Verificado y Fecha) y en [`02-estado.md`](../02-estado.md).

**Sale de H0:** inventario completo y las capacidades críticas confirmadas (OpenFlow 1.3, tablas, VLAN trunk, Docker).

## 3. Fase 2 — inventario y secretos

1. Copiar la plantilla y completar con los datos reales:

   ```bash
   cp deploy/ansible/inventory/slice.example.yml deploy/ansible/inventory/slice.yml
   ```

   - `ansible_host` de cada una de las 14 VMs (IP de `ens3`).
   - `switch_ports` con las NIC de datos reales (todo lo que no sea `ens3`).
   - `MIRROR_IFACE` en `.env` con la interfaz del espejo (fase H0).
2. Crear `.env` desde `.env.example` con los secretos reales (jamás por git) o dejarlos en Ansible Vault. **`STUB_VERIFY` debe quedar vacío.**
3. Conectividad:

   ```bash
   make ping
   ```

**Sale de la fase 2:** `make ping` responde en las 14 VMs.

## 4. Fase 3 — base, imágenes y plataforma

```bash
make deploy TAGS=base
make deploy TAGS=images
make deploy TAGS=platform
make status
```

- `base` instala Docker, Compose, chrony y DNS; **no** instala Docker en switches ni h2/h3.
- `images` copia, verifica, carga y limpia los bundles (el disco es la restricción).
- `platform` levanta S1–S4 con sus Compose; los servicios propios de S1 llegan con la fase 5.

**Sale de la fase 3:** `make status` muestra S3 (PostgreSQL) y S4 (RabbitMQ) sanos.

## 5. Fase 4 — plano de control y datos

```bash
make deploy TAGS=onos
make deploy TAGS=switches
make status
```

1. **Quórum ONOS:** en onos1, `curl -u karaf:karaf http://127.0.0.1:8181/onos/v1/cluster` — tres nodos y maestro elegido. Si no hay quórum: revisar `cluster.json` y que las tres IPs de `ens3` se alcancen entre sí.
2. **Switches:** `make status` debe mostrar `is_connected: true` en el `ovs-ofctl show` de NC1/NC2/A1/A2 y ONOS viendo **4 dispositivos**.

**Sale de la fase 4:** quórum de 3 y 4 switches conectados — el criterio H3.

## 6. Fase 5 — identidad

```bash
make build          # construye las once imágenes propias
make deploy TAGS=identity
make status
```

Verificación del corte vertical, en este orden:

1. `curl http://<s1>:8080/health` — Portal vivo.
2. Login de comunidad contra RADIUS **real** (con `STUB_VERIFY` vacío): fallo con credenciales inventadas, éxito con una cuenta del directorio de prueba.
3. Login de operador con TOTP (provisionado por la cadena SA→Admin→TI).
4. Autoregistro de invitado y rechazo tras vencer el TTL.

**Sale de la fase 5:** el login extremo a extremo funciona por los tres reinos.

## 7. Fase 6 — cadena completa y cierre

```bash
make status            # los once servicios propios en verde
```

Con el espejo confirmado (H0), la cadena completa queda operativa: tráfico del espejo → `MetricSample` → `AnomalyDetected` → `IncidentOpened` → decisión → **I2 → flujos ONOS** → `MitigationApplied` → `MitigationVerified`, con la Auditoría viéndolo todo.

**Sale de la fase 6:** entorno completo verificado — es el punto de partida de la campaña de la etapa 3 ([`07_plan_de_trabajo_etapa_3.md`](../../implementation/07_plan_de_trabajo_etapa_3.md)).

## 8. Contingencias

| Sorpresa | Respuesta |
|---|---|
| El espejo no llega al sensor | Orden de reemplazo de `04` §4.3; documentar la limitación |
| Docker sin demonio en una VM | `systemctl start docker` y `enable`; si no existe, `make deploy TAGS=base` lo instala |
| ONOS sin quórum | Revisar `cluster.json` en las tres VMs y la conectividad entre `ens3` |
| `TABLE_FULL` en el llenado de flujos | Medir y reportar (RNF-05); reducir caminos o agrupar destinos |
| Disco lleno tras cargar imágenes | Los bundles se limpian solos; borrar `/tmp/campus-custom` si quedó |

## 9. Desviaciones

Toda desviación del diseño se registra en el anexo del slice y en [`02-estado.md`](../02-estado.md) — jamás se silencia (P11).
