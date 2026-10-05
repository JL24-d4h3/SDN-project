# Método de validación

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** E — Validación del HLD
**Estado:** Borrador formal para revisión

---

Esta fase no introduce arquitectura nueva: **comprueba que el HLD (Fase D) responde a los drivers (Fase B)** y deja registrado lo que todavía no tiene dueño. Cada comprobación termina en un veredicto con evidencia; los huecos quedan listados con la acción que los cierra.

## 1. Qué se comprueba

| Documento | Comprueba | Contra |
|---|---|---|
| `01_casos_de_uso_a_componentes.md` | Que cada caso de uso tiene componentes que lo realizan | [B-00](../B-Drivers_de_arquitectura/00_Proyecto_ConOps_y_CU.md) §5 (CU-01–CU-10) |
| `02_requisitos_a_componentes.md` | Que cada requisito tiene dueño arquitectónico | [B-01.1](../B-Drivers_de_arquitectura/01.1_RF_funcionales.md) (R1–R5) y [B-01.2](../B-Drivers_de_arquitectura/01.2_RQ_transversales-de_calidad-arquitectonicos.md) (RT, RNF, RA) |
| `03_atributos_de_calidad_a_decisiones.md` | Que cada atributo de calidad se resuelve en una decisión concreta | B-01.2 y los principios (D-03) |
| `04_escenarios_de_fallo.md` | Qué ocurre ante la caída de cada pieza y qué tolerancia a fallos existe por diseño | D-04, D-05 y las restricciones (C-04) |
| `05_escenarios_de_ataque.md` | Que cada amenaza del catálogo tiene detección y respuesta asignadas | D-11.1 y la serie de flujo |

## 2. Veredictos

- **Cubierto** — hay componente, mecanismo descrito y evidencia documental.
- **Parcial** — existe el mecanismo, pero falta una pieza o una precisión; se indica cuál y dónde se cierra.
- **Hueco** — no hay dueño; se registra con la acción y la fase que lo cierra.

Un hueco registrado no invalida el HLD: la validación existe para que nada quede sin dueño visible. La lista de huecos queda al final de cada documento.

## 3. Entradas

- Casos de uso y criterios de éxito: B-00 §5 y §8.
- Requisitos: B-01.1 (R1–R5) y B-01.2 (RT-01–RT-10, RNF-01–RNF-12, RA-01–RA-09).
- Arquitectura: D-01–D-12; catálogo de amenazas: D-11.1.
- Mecanismos paso a paso: la serie de flujo, partes 0–5 (`flows/`).

## 4. Salida

Los documentos de esta fase. Los huecos que resulten alimentan la fase de decisiones tecnológicas y el prototipo.
