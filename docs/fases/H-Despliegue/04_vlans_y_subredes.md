# VLANs y subredes

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** H — Despliegue
**Estado:** Borrador formal para revisión

---

El **segmento lógico se materializa en una VLAN con su subred**: la VLAN agrupa en capa 2 y disciplina el direccionamiento; la subred le da el espacio IPv4 (RP-12). Es el mecanismo de despliegue que el modelo de dominio ya registró como recurso — «Segmentos de red (VLAN)», gestión P20 ([`A-02`](../A-Modelo_de_dominio/02_recursos_y_servicios.md))—. Y con una frontera explícita: **la VLAN no concede nada.** El aislamiento y los permisos viven en las reglas del pipeline ([`G-06`](../G-Diseno_de_bajo_nivel-LLD/06_reglas.md)); la VLAN es agrupación y direccionamiento — la política manda sobre ella, no al revés (P8).

## 2. La correspondencia segmento ↔ VLAN ↔ subred

| VLAN | Segmento | Subred | Vive en | Nota |
|---|---|---|---|---|
| 10 | USUARIOS | `10.1.0.0/24` | Puertos de acceso de A1 y A2; trunks hacia la distribución | Hosts académicos, operadores, atacante interno |
| 20 | GESTIÓN | `10.0.0.0/24` | Trunk del servidor en A3; transita hacia la distribución y el núcleo | Los servicios de la plataforma; alcanzable por el plano de datos **solo** por la frontera de reglas ([`03`](03_red.md) §2) |
| 30 | SERVIDORES | `10.2.0.0/24` | Puertos de acceso de A3; transita hacia la distribución y el núcleo | Los activos protegidos de R2 |
| 40 | EXTERNA | `10.3.0.0/24` | Puerto de A4 (y trunk del servidor para la VM atacante) | Origen de los escenarios R5 |

- **Tagging:** untagged en los puertos de acceso (los hosts no etiquetan); tagged (802.1Q) en los trunks, que transportan varias VLAN — los enlaces acceso–distribución llevan 10, 20 y 30 (40 en el borde); los enlaces distribución–núcleo y el enlace de núcleo llevan todas las VLAN de datos. La asignación puerto a puerto está en [`05`](05_puertos.md).
- **El tránsito de la VLAN 20 es deliberado:** el segmento de gestión cruza los trunks para que la frontera de reglas exista — BASE intenta alcanzarlo, la prioridad 100 lo niega, la elevación (200) lo abre para quien corresponde (R1.6, RA-09). El **canal de control**, en cambio, no es esta VLAN: son las interfaces `ma1`, fuera de banda (RP-02).
- **DHCP:** los hosts del prototipo usan IP estática (reproducibilidad, RNF-11); DHCP queda reservado para la referencia. La regla de DHCP del esqueleto existe para que el diseño no dependa de esa reserva.

## 3. La cuarentena y el canal in-band: dos reservas

- **VLAN de cuarentena:** la variante de contención que mueve un dispositivo a una VLAN aislada en vez de bloquearlo ([`flows/03`](../../../flows/03_flujo_autenticacion_autorizacion.md)) queda **analizada para la referencia** — en el prototipo la cuarentena es DROP con aprobación humana ([`G-06`](../G-Diseno_de_bajo_nivel-LLD/06_reglas.md) §3). Añadir la VLAN de cuarentena al prototipo es un cambio de alcance, no de arquitectura.
- **Canal in-band:** la variante que lleva el control por una VLAN de gestión priorizada sobre los enlaces de datos sigue siendo el objetivo aspiracional analizado en [`01`](01_infraestructura_fisica.md) §4; el prototipo es out-of-band (RP-02).

## 4. La referencia: la misma correspondencia a escala

En el campus real cada segmento existe como VLAN institucional con su subred administrada por la institución, y la correspondencia se multiplica (usuarios por edificio, servidores por servicio). Lo que no cambia es la regla: la segmentación es el mecanismo; la política es de las reglas. El permiso P20 (gestionar segmentación) queda en manos de la administración de la red — nunca de los servicios.

## 5. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Dispositivo en VLAN 10 sin alcanzar 10.0.0.0/24 salvo el portal | La frontera de reglas sobre la VLAN | R1.6, RA-09 |
| Elevación abre VLAN 20 para el operador y expira al TTL | La escalera sobre el tránsito | R1.8, P10 |
| Tráfico entre VLANs enruta por caminos del controlador | Sin router: el plano de datos resuelve | flows/05 |
| Etiquetado de trunks correcto (10/20/30 según enlace) | Correspondencia con [`05`](05_puertos.md) | R2.6 |
