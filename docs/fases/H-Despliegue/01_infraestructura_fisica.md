# Infraestructura física

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** H — Despliegue
**Estado:** Borrador formal para revisión

---

La **infraestructura física es el soporte real del despliegue**: las máquinas, los cables y los puertos sobre los que todo lo demás se asigna. Su criterio rector es la **separación de planos**: el canal de control, el espejo del perímetro y el plano de datos son físicamente distintos — lo que no comparte cable no comparte fallo ni interfiere (RP-02, RA-09).

## 2. El prototipo: inventario del laboratorio

| Elemento | Cantidad | Papel | Dónde |
|---|---|---|---|
| Switches del plano de datos (Pica8/PicOS) | 8 (NC1, NC2, D1, D2, A1–A4) | Plano de datos SDN: esqueleto, sesiones, mitigaciones | Laboratorio (RP-11) |
| Servidor de laboratorio | 1 | Hipervisor: todas las VMs y los contenedores | Laboratorio |
| Interfaces de gestión (`ma1`) | 8 | Canal de control OpenFlow, fuera de banda | Red de gestión del laboratorio o puertos dedicados del servidor |
| Cableado de datos | 13 enlaces entre switches + accesos + espejo | La malla dual-homed ([`05`](05_puertos.md)) | Etiquetado por puerto |
| Cable del espejo | 1 | A4 p47 → NIC dedicada del sensor | Directo, sin pasar por ningún otro equipo |

**Sobre el hardware disponible.** Los ocho switches son Pica8 del laboratorio —el único lugar donde las primitivas OpenFlow se verifican de verdad ([`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §4)—. El servidor es una máquina del laboratorio con ≥ 32 GB de RAM y ≥ 8 núcleos; con 16 GB se recorta el escenario a 10 hosts de usuario y 2 servidores de servicio ([`02`](02_vms_y_contenedores.md) §4). Si el slice no reuniera los ocho Pica8, el recorte evaluado es **seis** — dos núcleo y cuatro acceso, sin nivel de distribución—: se pierde la jerarquía completa, no la demostración de failover. Las **ventanas de uso del laboratorio condicionan cuándo corre la verificación física**; fuera de ellas rige el apoyo virtual declarado en [`F-08`](../F-Decisiones_tecnologicas/08_entorno_del_prototipo.md) §1 ([`06`](06_dependencias.md) §5).

## 3. La topología del prototipo

```text
   A1      A2      A3      A4        ← acceso: usuarios, usuarios, servidores, borde + espejo
    │╲     ╱│       │╲     ╱│
    │ ╲   ╱ │       │ ╲   ╱ │         ← cada acceso conecta con D1 Y con D2 (dual-homed)
    │  ╲ ╱  │       │  ╲ ╱  │
    │  ╱ ╲  │       │  ╱ ╲  │
    │╱     ╲│       │╱     ╲│
   D1        D2                      ← distribución
    │╲       ╱│
    │ ╲     ╱ │                       ← cada distribución conecta con NC1 Y con NC2
    │  ╲   ╱  │
    │   ╲ ╱   │
    │    ╳    │
    │   ╱ ╲   │
    │  ╱   ╲  │
    │ ╱     ╲ │
    │╱       ╲│
   NC1 ────── NC2                     ← núcleo, enlazados entre sí

   13 enlaces entre switches; todo acceso, toda distribución y todo destino
   quedan a un fallo de enlace o de switch del resto de la red.
```

**Dos núcleo, dos distribución y cuatro acceso**, con doble enlace desde cada acceso y enlace directo entre núcleos: la jerarquía de tres niveles de [`D-10`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/10_topología_lógica.md) materializada. Cada corte cuenta una historia, y todas se miden:

| Falla | Qué ocurre | Qué se mide |
|---|---|---|
| Corte de un enlace de acceso (A1–D1) | `PORT_STATUS`; el tráfico sigue por D2 — con grupo *fast-failover* la conmutación es local del switch, sin controlador (P2); sin él, el controlador reinstala el camino alternativo ([`G-06`](../G-Diseno_de_bajo_nivel-LLD/06_reglas.md) §4) | Tiempo de conmutación |
| Caída de un núcleo (NC1) | La red sigue completa por NC2; los caminos se recalculan | Tiempo de re-enrutamiento global |
| Caída de un acceso (A1) | Su segmento se aísla; el resto no se entera (E-04) | Aislamiento del fallo |
| Caída del controlador | Lo instalado sigue operando y expira por timeout (P2); el clúster documentado en [`F-01`](../F-Decisiones_tecnologicas/01_controlador_y_api_northbound.md) §6 es la vía de HA | — |

**La redundancia no cuesta un protocolo de árbol.** No hay STP esperando a que converja un anillo: el controlador ya tiene el grafo, y el camino alternativo es un recálculo o una conmutación local del propio plano de datos — la demostración de P2 en vivo, con números (RA-07).

**El reparto de papeles.** A4 es el **borde**: concentra lo externo (segmento EXTERNA) y el espejo hacia el sensor ([`G-04`](../G-Diseno_de_bajo_nivel-LLD/04_interfaces.md) §5). A1 y A2 cargan la política de ingreso de usuarios; A3 sirve a los servidores y recibe la gestión (VLAN 20). Con orígenes de ataque en A1, A2 y A4, un ataque distribuido se mitiga **simultáneamente en tres switches de ingreso** (P9) — la demostración de concurrencia. La escala —ocho switches, ~23 dispositivos, ~350–450 reglas ([`G-06`](../G-Diseno_de_bajo_nivel-LLD/06_reglas.md) §4)— hace creíbles los experimentos de capacidad, y el sondeo I8 deja de ser simbólico: barre los ocho dispositivos.

## 4. La referencia: lo que se analiza, no se despliega

El campus que la solución describe, con sus condiciones de habilitación ([`F-09`](../F-Decisiones_tecnologicas/09_sintesis_y_trazabilidad.md) §5, [`C-04`](../C-Contexto/04_alcance_de_la_infraestructura.md) §4):

| Elemento de la referencia | Análisis | Condición de habilitación |
|---|---|---|
| Jerarquía núcleo / distribución / acceso | El prototipo ya la materializa (§3); la referencia la lleva a la escala del campus: cantidades y enlaces según la red real | Topología definitiva del campus (D-10) |
| Redundancia de nodos y enlaces | El prototipo ya la **despliega y mide**; la referencia la extiende a doble enlace en todos los accesos y doble núcleo físico | Decisión de la administración de la red (E-04: es despliegue) |
| Clúster del controlador en operación | Tres instancias ONOS en servidores de gestión separados; switches con los tres endpoints y failover por rol | Migración del prototipo de instancia única (F-01 §6) |
| Canal in-band | VLAN de gestión priorizada sobre los enlaces de datos; los flujos del canal se instalan antes que nada | Aprobación de la administración; supervivencia verificada ante ataque volumétrico (C-04 §6) |
| Feeds externos de inteligencia | Listas de reputación para R5.6, con la regla de promoción del prototipo como filtro | Acuerdo con el proveedor del feed; fuera del entorno controlado (F-07 §4) |
| Cifrado en reposo y política de respaldo | Volúmenes de las bases cifrados; respaldo con retención y drill periódico | Procedimientos de la administración de la red |
| 802.1X en puertos sensibles | Accesos administrativos y zonas restringidas con autenticación de puerto | Reservado por diseño desde D-07 §3; fuera del prototipo |

La referencia **no** es una lista de tareas del proyecto: es la forma del diseño cuando el prototipo haya firmado sus decisiones con mediciones (P12).

## 5. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Inventario completo presente y conectado (8 switches, 13 enlaces, espejo, gestión) | Correspondencia con [`05`](05_puertos.md), puerto a puerto | C-04 §5 |
| Corte de un enlace de acceso (A1–D1) | Tiempo de conmutación al camino por D2 — grupo fast-failover o recálculo | RA-07, P2, E-04 |
| Caída de NC1 | La red sigue completa por NC2; tiempo de re-enrutamiento global | RA-07 |
| Ataque distribuido desde A1, A2 y A4 | Mitigación simultánea en los tres switches de ingreso (P9) | R3.5 |
| Canal de control activo por `ma1` con el plano de datos operando | Separación física de planos | RP-02, RA-09 |
| Ataque de carga contra el segmento de gestión durante un escenario | El canal out-of-band sostiene el control | RA-09, P2 |
| Ventanas de laboratorio planificadas | La verificación física corre en el hardware real | RP-11 |
