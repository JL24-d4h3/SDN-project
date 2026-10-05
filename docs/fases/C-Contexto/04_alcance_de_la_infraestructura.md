# Alcance de la infraestructura

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** C — Contexto
**Estado:** Borrador formal para revisión

---

## 1. Dos infraestructuras

- **Infraestructura de referencia** — la red de campus que la solución describe: qué poblaciones, segmentos y servicios existen.
- **Infraestructura del prototipo** — lo que el proyecto despliega y sobre lo que valida.

RP-05 exige un entorno controlado y representativo: la segunda debe representar a la primera en los aspectos que los escenarios y las métricas necesitan, sin reproducir su escala real (RP-04).

---

## 2. Infraestructura de referencia

| Elemento | Descripción | Relación con los requerimientos |
|---|---|---|
| Segmento de usuarios finales | Usuarios académicos conectados (BASE; ACADÉMICO tras el login) | Origen de R1 y del tráfico observado en R3 y R4 |
| Segmento de servidores | Servicios académicos y administrativos | Objeto de R2 |
| Segmento de administración | Consola, controlador y planos de gestión | Protegido según RA-09 |
| Segmento perimetral | Borde con redes externas | Punto de aplicación de R5 |
| Servicios institucionales | Académicos, administrativos y base de datos | Activos protegidos (ver [`03_sistemas_externos.md`](03_sistemas_externos.md)) |
| Dispositivos de usuario final | Equipos de usuarios académicos y de operadores | Origen del tráfico; candidatos a aislamiento |

La segmentación anterior es una propuesta de referencia. Su definición definitiva pertenece a la arquitectura lógica (Fase D) y a la topología (Fase H).

---

## 3. Infraestructura del prototipo

| Elemento | Se despliega o se simula | Nota |
|---|---|---|
| Controlador SDN | Se despliega | Decisión tecnológica pendiente (Fase F) |
| Switches SDN | Se despliegan (virtuales o físicos) | Hardware del laboratorio: **Pica8 con PicOS** (RP-11); deben soportar la instalación dinámica de reglas y las primitivas OpenFlow que el diseño exija (meters, groups, counters) |
| Canal de control | Se configura | Out-of-band (red de gestión); la variante in-band es un objetivo aspiracional (ver flujo §2.6) |
| Hosts de usuario | Se simulan | Representan al usuario académico; generan tráfico legítimo; no se registran en ningún catálogo |
| Servidores de servicio | Se simulan | Representan los activos protegidos |
| Portal cautivo y AAA/RADIUS | Se despliegan | Autenticación de la comunidad y de los operadores; el backend de identidad (IdP) se simula o se integra (SE-02) |
| Registro de dispositivos privilegiados | Se despliega | Base de datos propia: dispositivos de operadores y su auditoría |
| Cadena de detección (Monitor, Detection, Incident, Policy) | Se despliega | Lee counters del plano de datos y alimenta al controlador |
| Segmentación | Se configura | Necesaria para R2 y para separar poblaciones |
| Tráfico de ataque | Se genera de forma controlada | Solo dentro del entorno del proyecto (RP-06, RP-08) |
| Perímetro | Se representa | Alcance por definir (ver cuestiones abiertas) |

---

## 4. Dentro y fuera del alcance

**Dentro**

- lo necesario para implementar R1, R2 y R4, los tres requerimientos obligatorios, y para demostrar los escenarios de R3 y R5;
- la segmentación mínima que haga verificable R2;
- los escenarios de ataque controlados que las pruebas exijan.

**Fuera**

- la escala real del campus: número de usuarios, de dispositivos y de enlaces;
- hardware de red específico, cuando el entorno virtual permita validar lo mismo;
- alta disponibilidad del plano de control (clúster del controlador): se analiza por diseño, no se despliega; la redundancia del plano de datos sí se despliega y se mide — ocho switches dual-homed, fijado en la Fase H;
- servicios institucionales reales: se representan mediante equivalentes controlados.

---

## 5. Supuestos

- El entorno disponible admite virtualización de hosts, switches y controlador.
- Los switches del prototipo son Pica8/PicOS (RP-11) y soportan la instalación dinámica de reglas; las primitivas OpenFlow concretas (meters, groups, counters) se verifican contra el dispositivo antes de comprometer el diseño.
- El canal de control es out-of-band (RP-02); si el prototipo adopta la variante in-band, exige VLAN de gestión y priorización del tráfico de control.
- El prototipo opera solo con IPv4 (RP-12).
- La topología es rígida por diseño, pero el sistema tolera la aparición de dispositivos nuevos: todo dispositivo que no haga match con el registro de dispositivos privilegiados recibe perfil BASE (RP-13).
- Existe conectividad de laboratorio suficiente para generar tráfico de carga y de ataque sin salir del entorno.

---

## 6. Cuestiones abiertas

- Número de switches y de hosts del prototipo: **cerrado en la Fase H** — ocho switches (dos núcleo, dos distribución, cuatro acceso, dual-homed) y ~23 dispositivos simulados.
- Capacidad de las tablas de flujo de PicOS: condiciona cuántas reglas simultáneas admite la solución (riesgo de exceso de reglas SDN) y si meters/groups están disponibles.
- Representación del perímetro: firewall simulado, componente del propio entorno o solo reglas en el borde.
- Si habrá acceso a hardware físico o el prototipo será íntegramente virtual: **cerrado** — hardware físico (Pica8 del laboratorio, RP-11), con apoyo virtual para el desarrollo fuera de las ventanas.
- Si el canal in-band se implementa en el prototipo y en qué fase: es más complejo (VLAN de gestión, priorización, prueba de supervivencia ante un ataque volumétrico), pero valorado por el profesor.
