# Restricciones

**Proyecto:** Solución de seguridad para una red de campus académico
**Curso:** TEL354 — Redes Definidas por Software
**Fase:** B — Drivers
**Origen:** separado de [`01_Requisitos_y_Restricciones_SDN_v0.1.md`](01_Requisitos_y_Restricciones_SDN_v0.1.md)

---

Una restricción es una condición impuesta al proyecto que la arquitectura no puede decidir: debe cumplirla. A diferencia de un requerimiento, no admite alternativa de diseño, y por eso se evalúa como criterio de descarte de alternativas.

---

## 1. Alcance y entregables

### RP-01 — Requerimientos implementados

**Restricción:** el proyecto exige implementar tres de los cinco requerimientos. La calidad de esos tres tiene prioridad sobre funcionalidad adicional.

**Implicación:** la arquitectura debe cubrir R1–R5 de forma integral, pero el diseño detallado, la implementación y la evaluación se concentran en los tres requerimientos asignados. El criterio de alcance se establece en [`../A-Modelo_de_dominio/00_Proyecto_SDN.md`](../A-Modelo_de_dominio/00_Proyecto_SDN.md).

### RP-07 — Complejidad

**Restricción:** no deberán incorporarse tecnologías cuya complejidad no pueda justificarse, implementarse y evaluarse dentro del alcance.

**Implicación:** cada componente tecnológico debe responder a un requerimiento o atributo de calidad identificado; lo que no pueda justificarse ni evaluarse queda fuera.

---

## 2. Arquitectura y hardware

### RP-02 — Paradigma SDN

**Restricción:** la solución deberá ser coherente con el paradigma SDN y con la separación entre plano de control y plano de datos.

**Implicación:** las decisiones de seguridad deben expresarse como políticas aplicables desde el plano de control, no como configuración manual dispositivo por dispositivo.

### RP-11 — Hardware del laboratorio

**Restricción:** la solución deberá ejecutarse sobre los switches disponibles en el laboratorio del curso, de hardware **Pica8** con **PicOS**, y sobre las capacidades OpenFlow que ese sistema expone.

**Implicación:** el protocolo southbound es OpenFlow, y las capacidades del plano de datos (meters, groups, tipos de acción y tamaño de las tablas) quedan condicionadas a lo que PicOS soporte. Ningún mecanismo puede darse por disponible sin verificarlo contra el dispositivo: si una primitiva no está soportada, el diseño debe degradarla explícitamente (p. ej. rate limiting sin meters, por muestreo y reglas del controlador).

### RP-12 — Alcance de protocolo IPv4

**Restricción:** el flujo de operación de la solución considera exclusivamente IPv4. IPv6, Neighbor Discovery y sus protocolos asociados quedan fuera del alcance.

**Implicación:** los escenarios de inicialización se describen con ARP y DHCPv4; no se modela tráfico de control IPv6.

### RP-13 — Confianza física como condición de acceso base

**Restricción:** el acceso físico controlado al campus se considera condición de confianza inicial suficiente para la obtención del perfil mínimo de red (perfil BASE), sin autenticación digital.

**Implicación:** la seguridad física del campus forma parte del perímetro de seguridad. La autenticación digital se reserva para la elevación de privilegios (operadores y elevaciones temporales); la presencia física jamás justifica privilegios elevados.

### RP-09 — Coherencia tecnológica

**Restricción:** cada tecnología deberá responder a una necesidad concreta y tener una responsabilidad definida.

**Implicación:** no se admiten tecnologías solapadas ni componentes sin responsable claro dentro de la arquitectura.

---

## 3. Tiempo y recursos

### RP-03 — Tiempo

**Restricción:** el diseño e implementación deberán ajustarse al cronograma del curso.

**Implicación:** la priorización es la herramienta de control del alcance; no hay holgura para exploración tecnológica abierta.

### RP-04 — Recursos

**Restricción:** la solución deberá utilizar los recursos computacionales disponibles.

**Implicación:** el diseño se acota al laboratorio disponible; la escalabilidad se demuestra por diseño y medición, no por despliegue a escala real.

---

## 4. Entorno y ejecución de pruebas

### RP-05 — Entorno

**Restricción:** las validaciones deberán ejecutarse en un entorno de laboratorio o simulación controlado y representativo.

**Implicación:** no es necesario reproducir la escala real del campus, pero sí los escenarios y las métricas definidos.

### RP-06 — Seguridad de las pruebas

**Restricción:** los ataques simulados deberán ejecutarse únicamente sobre infraestructura controlada por el proyecto.

### RP-08 — Aislamiento

**Restricción:** las pruebas y los mecanismos de mitigación no deberán afectar sistemas ajenos al entorno del proyecto.

**Implicación:** RP-06 y RP-08 delimitan el alcance legítimo de los escenarios de ataque; ninguna prueba puede salir del entorno controlado por el proyecto.

---

## 5. Verificación

### RP-10 — Verificabilidad

**Restricción:** toda funcionalidad crítica deberá contar con un mecanismo objetivo de validación.

**Implicación:** un requisito sin métrica ni prueba asociada no puede considerarse satisfecho.
