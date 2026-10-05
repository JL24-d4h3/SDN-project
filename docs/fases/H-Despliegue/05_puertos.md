# Puertos

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** H — Despliegue
**Estado:** Borrador formal para revisión

---

El **plano de puertos es la asignación física que materializa los enlaces**: cada puerto de cada switch tiene un papel, y el papel manda sobre su configuración. La convención del prototipo: puertos `p1–p44` de datos (trunks y accesos), `p45–p48` reservados para funciones especiales (el espejo vive en `p47` del borde), interfaz `ma1` de gestión. Todo enlace queda etiquetado en el plano y en este documento — un puerto sin papel es un fallo de despliegue.

## 2. La asignación, switch por switch

```text
        A1 (acceso usuarios)            A2 (acceso usuarios)           A3 (acceso servidores)
        p1 trunk ↔ D1 · p2 ↔ D2         p1 ↔ D1 · p2 ↔ D2              p1 ↔ D1 · p2 ↔ D2
        p3–p19 acceso VLAN 10           p3–p5 acceso VLAN 10            p3–p5 acceso VLAN 30
        p20 NIC-B (hosts virtuales)     p6 NIC-E (operadores,           p6 NIC-A trunk VLAN 20
        ma1 gestión                        atacante interno,               (gestión, por el servidor)
                                           puente demo MAC_Moved)          ma1 gestión
                                        ma1 gestión

        A4 (borde)                      D1 y D2 (distribución)          NC1 y NC2 (núcleo)
        p1 ↔ D1 · p2 ↔ D2               p1 ↔ NC1 · p2 ↔ NC2             p1 ↔ D1 · p2 ↔ D2
        p3 acceso VLAN 40               p3 ↔ A1 · p4 ↔ A2               p3 ↔ NC1–NC2 (enlace de núcleo)
        p4 NIC-C trunk VLAN 40             p5 ↔ A3 · p6 ↔ A4            ma1 gestión
           (atacante externo)           ma1 gestión
        p47 espejo → NIC-D (sensor)
        ma1 gestión
```

| Puerto | Papel | VLANs | Nota |
|---|---|---|---|
| A1 p1/p2 ↔ D1/D2 | Trunk de acceso | 10, 20, 30 (tagged) | El camino alternativo nace aquí: dos uplinks |
| A1 p3–p19 | Acceso de usuarios | 10 (untagged) | Equipos físicos del laboratorio |
| A1 p20 | NIC-B del servidor | 10 (untagged) | **Los hosts virtuales académicos** comparten este puerto |
| A2 p1/p2 ↔ D1/D2 | Trunk de acceso | 10, 20, 30 (tagged) | Dual-homed |
| A2 p3–p5 | Acceso de usuarios | 10 (untagged) | Equipos físicos |
| A2 p6 | NIC-E del servidor | 10 (untagged) | Operadores, atacante interno y el **puente de la demostración de `MAC_Moved`** |
| A3 p1/p2 ↔ D1/D2 | Trunk de acceso | 20, 30 (tagged) | Dual-homed |
| A3 p3–p5 | Acceso de servidores | 30 (untagged) | Los activos protegidos, uno por puerto |
| A3 p6 | NIC-A del servidor | 20 (tagged) | Por aquí conecta todo el plano de contenedores (gestión) |
| A4 p1/p2 ↔ D1/D2 | Trunk del borde | 40 (tagged) | Dual-homed |
| A4 p3 | Acceso externo | 40 (untagged) | Equipo externo real, si el laboratorio lo ofrece |
| A4 p4 | NIC-C del servidor | 40 (tagged) | La VM atacante externa, por el servidor |
| A4 p47 → NIC-D | **Espejo del perímetro** | — | Replica el ingreso del segmento externo (p3+p4) hacia el sensor; el sensor solo recibe, nunca emite por esta interfaz ([`G-04`](../G-Diseno_de_bajo_nivel-LLD/04_interfaces.md) §5) |
| D1/D2 p1/p2 ↔ NC1/NC2 | Trunks de distribución | 10, 20, 30, 40 (tagged) | Cada distribución llega a ambos núcleos |
| D1/D2 p3–p6 ↔ A1–A4 | Trunks de acceso | según el acceso | La agregación de los cuatro accesos |
| NC1 p3 ↔ NC2 p3 | Enlace de núcleo | 10, 20, 30, 40 (tagged) | El núcleo es un par enlazado, no un anillo |
| `ma1` ×8 | Canal de control | — | OpenFlow fuera de banda (RP-02); whitelist del controlador ([`G-04`](../G-Diseno_de_bajo_nivel-LLD/04_interfaces.md) §2) |

- **Los hosts virtuales comparten un puerto por población** — es la concesión práctica del laboratorio: cada grupo de VMs entra por una NIC del servidor (A1 p20 para académicos, A2 p6 para operadores y atacante interno). La red las ve como MAC distintas en el mismo puerto; las reglas del esqueleto y de sesión son por MAC, no por puerto, así que la política no se entera.
- **La demostración de `MAC_Moved` cruza switches:** mover la vNIC de una VM del puente de A1 (NIC-B) al de A2 (NIC-E) hace que la MAC aparezca en **otro switch** — el movimiento más fuerte que el prototipo puede producir, y el `MAC_Moved` determinista de [`G-06`](../G-Diseno_de_bajo_nivel-LLD/06_reglas.md) §4 lo aísla.
- **El espejo no comparte cable con nada** ([`01`](01_infraestructura_fisica.md) §2): A4 p47 → NIC dedicada del sensor, directo.
- **Reservas de la referencia:** puertos sensibles (infraestructura, zonas restringidas) con port security y 802.1X — reservados por diseño desde D-07 §3, fuera del prototipo ([`01`](01_infraestructura_fisica.md) §4).

## 3. El plano de puertos en la operación

El plano de puertos es la entrada de la topología: el controlador aprende por `PORT_STATUS` y LLDP quién está conectado dónde ([`flows/05`](../../../flows/05_enrutamiento.md) §3), y la caída de un enlace rehace el grafo — con la malla dual-homed, el grafo resultante sigue conexo salvo caída de un acceso. Un puerto movido **sin actualizar este documento** es un fallo de despliegue detectable: la topología aprendida dejará de corresponder con el plano — la verificación siguiente lo cierra comparando ambas.

## 4. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Correspondencia puerto a puerto entre el plano y la topología aprendida | Sin puertos sin papel | R2.6 |
| Espejo activo: tráfico externo generado llega íntegro al sensor | Copia fiel, sin interponerse | R5, P8 |
| `PORT_STATUS` al desconectar un enlace de acceso | El grafo se rehace y el camino alternativo toma el relevo — tiempo medido | E-04, RA-07 |
| Conexión de control rechazada desde un puerto de datos | El canal es solo `ma1` (V6) | RA-09 |
| Movimiento de MAC entre A1 y A2 | `MAC_Moved` determinista y aislamiento | R3.3, P7 |
