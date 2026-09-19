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
| Segmento de usuarios finales | Alumnos y docentes conectados | Origen de R1 y del tráfico observado en R3 y R4 |
| Segmento de servidores | Servicios académicos y administrativos | Objeto de R2 |
| Segmento de administración | Consola, controlador y planos de gestión | Protegido según RA-09 |
| Segmento perimetral | Borde con redes externas | Punto de aplicación de R5 |
| Servicios institucionales | Académicos, notas, administrativos y base de datos | Activos protegidos (ver [`03_sistemas_externos.md`](03_sistemas_externos.md)) |
| Dispositivos de usuario final | Equipos de alumnos, docentes y administradores | Origen del tráfico; candidatos a aislamiento |

La segmentación anterior es una propuesta de referencia. Su definición definitiva pertenece a la arquitectura lógica (fases D y E) y a la topología (Fase H).

---

## 3. Infraestructura del prototipo

| Elemento | Se despliega o se simula | Nota |
|---|---|---|
| Controlador SDN | Se despliega | Decisión tecnológica pendiente (Fase G) |
| Switches SDN | Se despliegan (virtuales o físicos) | Deben soportar la instalación dinámica de reglas |
| Hosts de usuario | Se simulan | Representan alumnos y docentes; generan tráfico legítimo |
| Servidores de servicio | Se simulan | Representan los activos protegidos |
| Segmentación | Se configura | Necesaria para R2 y para separar poblaciones |
| Tráfico de ataque | Se genera de forma controlada | Solo dentro del entorno del proyecto (RP-06, RP-08) |
| Sistema de identidad | Se simula o se integra | Depende de SE-02 |
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
- alta disponibilidad real y redundancia física: se analizan por diseño, no se despliegan;
- servicios institucionales reales: se representan mediante equivalentes controlados.

---

## 5. Supuestos

- El entorno disponible admite virtualización de hosts, switches y controlador.
- Los dispositivos SDN del prototipo soportan la instalación dinámica de reglas.
- Existe conectividad de laboratorio suficiente para generar tráfico de carga y de ataque sin salir del entorno.

---

## 6. Cuestiones abiertas

- Número de switches y de hosts del prototipo: depende de la capacidad disponible y de los escenarios que se quieran reproducir.
- Capacidad de las tablas de flujo del dispositivo elegido: condiciona cuántas reglas simultáneas admite la solución (riesgo de exceso de reglas SDN).
- Representación del perímetro: firewall simulado, componente del propio entorno o solo reglas en el borde.
- Si habrá acceso a hardware físico o el prototipo será íntegramente virtual.
