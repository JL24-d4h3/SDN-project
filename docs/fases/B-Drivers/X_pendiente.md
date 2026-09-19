# 11. Decisiones arquitectónicas pendientes

En esta primera versión no se consideran definitivas las siguientes decisiones:

- mecanismo de autenticación;
- RBAC, ABAC o combinación;
- gestión de identidad;
- controlador SDN;
- protocolo southbound;
- diseño de northbound API;
- mecanismo de monitoreo;
- IDS, IPS o ambos;
- algoritmo/método de detección;
- umbrales estáticos o dinámicos;
- rate limiting;
- bloqueo;
- segmentación;
- ubicación de componentes de seguridad;
- almacenamiento de logs;
- visualización;
- virtualización/simulación;
- estrategia de recuperación.

Cada decisión deberá justificarse por requisitos, restricciones, complejidad y resultados cuantitativos.

---
#
# 12. Principios arquitectónicos

La solución deberá procurar:

1. mínimo privilegio;
2. separación de responsabilidades;
3. políticas centralizadas;
4. aplicación programable;
5. monitoreo continuo;
6. respuesta automatizada cuando corresponda;
7. trazabilidad;
8. modularidad;
9. escalabilidad;
10. reversibilidad;
11. verificabilidad;
12. integración de R1–R5.

---
#
# 13. Criterios de aceptación de la arquitectura

La arquitectura se considerará adecuada cuando:

- represente los cinco requerimientos;
- identifique actores y componentes;
- defina responsabilidades;
- muestre flujos de información y decisión;
- explique cómo las políticas llegan a la infraestructura SDN;
- contemple operación normal y escenarios de ataque;
- defina mecanismos de mitigación;
- considere restricciones;
- establezca criterios de éxito;
- permita derivar HLD y LLSD;
- sea viable dentro del alcance del curso.