# Especificación de Requisitos
## Solución de seguridad para una red de campus basada en SDN

**Curso:** TEL354 — Redes Definidas por Software  
**Proyecto:** Solución de seguridad para una red de campus académico  
**Versión:** 0.2 — Segunda versión  
**Fecha:** 16 de septiembre de 2026  
**Estado:** Borrador formal para revisión

---

## Alcance de este documento

Este documento especifica los requisitos de la solución: funcionales, transversales, no funcionales, arquitectónicos, de casos de uso y de pruebas.

No forman parte de él y se mantienen en documentos separados:

- **Marco del proyecto** — propósito, contexto, objetivo general y alcance: [`../A-Modelo_de_dominio/00_Proyecto_SDN.md`](../A-Modelo_de_dominio/00_Proyecto_SDN.md)
- **Restricciones** — condiciones impuestas al proyecto: [`02_restricciones.md`](02_restricciones.md)
- **Actores, roles y agentes** — quién interactúa con el sistema y con qué privilegios: [`../A-Modelo_de_dominio/01_actores-roles_y_agentes.md`](../A-Modelo_de_dominio/01_actores-roles_y_agentes.md)
- **Recursos y servicios** — qué protege la solución y con qué criticidad: [`../A-Modelo_de_dominio/02_recursos_y_servicios.md`](../A-Modelo_de_dominio/02_recursos_y_servicios.md)

---

# 1. Requerimientos funcionales

## R1 — Control de acceso según rol

### R1.1 Identificación
El sistema deberá identificar al usuario que solicita acceso.

### R1.2 Autenticación
El sistema deberá verificar la identidad mediante el mecanismo de autenticación seleccionado.

### R1.3 Asignación de rol
El sistema deberá asociar el usuario autenticado con un rol definido.

### R1.4 Política de acceso
El sistema deberá determinar qué acceso corresponde al rol del usuario.

### R1.5 Mínimo privilegio
Los usuarios deberán recibir únicamente los permisos necesarios para sus funciones.

### R1.6 Denegación
Los accesos inválidos o no autorizados deberán ser rechazados.

### R1.7 Administración
La solución deberá permitir gestionar roles y permisos.

### R1.8 Superusuarios
Deberá contemplarse un rol administrativo con privilegios superiores cuando sea necesario, restringiendo su uso.

### R1.9 Trazabilidad
Los eventos relevantes de autenticación y autorización deberán poder registrarse.

### R1.10 Escalabilidad
La arquitectura deberá considerar crecimiento de usuarios y accesos concurrentes.

---

## R2 — Protección de recursos privilegiados

### R2.1 Inventario
Deberán identificarse los recursos que requieren protección.

### R2.2 Clasificación
Los recursos deberán poder clasificarse, como mínimo, en generales, privilegiados y críticos.

### R2.3 Asociación de políticas
Cada recurso privilegiado deberá estar asociado a una política de acceso.

### R2.4 Autorización
El sistema deberá verificar que el usuario o rol esté autorizado antes de permitir el acceso.

### R2.5 Denegación
Los accesos no autorizados deberán ser bloqueados.

### R2.6 Segmentación
La arquitectura deberá permitir segmentar recursos según su nivel de protección cuando corresponda.

### R2.7 Actualización
Las políticas deberán poder actualizarse ante cambios en usuarios, roles o infraestructura.

### R2.8 Protección crítica
Los recursos críticos deberán disponer de controles superiores a los recursos generales.

### R2.9 Auditoría
Los accesos a recursos privilegiados deberán poder registrarse.

### R2.10 Aplicación SDN
Deberá definirse cómo las decisiones de autorización se traducen en reglas o políticas sobre la infraestructura SDN.

---

## R3 — Ataques encubiertos en la intranet

El requerimiento contempla, entre otros, network scanning, port scanning, IP spoofing y ataques distribuidos mediante solicitudes maliciosas.

### R3.1 Monitoreo
La solución deberá obtener información suficiente del tráfico para detectar comportamientos sospechosos.

### R3.2 Scanning
Deberá poder identificarse comportamiento compatible con network/port scanning.

### R3.3 Spoofing
Deberán contemplarse mecanismos para identificar tráfico cuyo origen sea inconsistente con las políticas definidas.

### R3.4 Anomalías
La solución deberá identificar comportamientos que se aparten de la referencia establecida.

### R3.5 Ataques distribuidos
Deberá contemplarse la detección de múltiples orígenes contra un mismo recurso.

### R3.6 Clasificación
Los eventos deberán clasificarse por tipo y, cuando sea posible, nivel de riesgo.

### R3.7 Mitigación
Una amenaza confirmada deberá poder activar una acción de mitigación.

### R3.8 Acciones
Podrán contemplarse bloqueo, rate limiting, aislamiento, redirección y/o alerta, según el diseño.

### R3.9 Recuperación
Las medidas temporales deberán poder revertirse cuando finalice el evento.

### R3.10 Registro
Los eventos deberán quedar registrados para análisis posterior.

---

## R4 — DDoS brute-force en la intranet

### R4.1 Línea base
Deberá definirse una referencia del comportamiento esperado del servicio protegido.

### R4.2 Detección
La solución deberá identificar incrementos anómalos del tráfico hacia un servidor o nodo.

### R4.3 Indicadores
Podrán utilizarse paquetes/s, solicitudes/s, conexiones/s, ancho de banda, número de fuentes, latencia u otros indicadores pertinentes.

### R4.4 Umbrales
Deberán establecerse criterios cuantitativos para distinguir tráfico normal y potencialmente malicioso.

### R4.5 Mitigación
La solución deberá aplicar una política de mitigación ante un evento detectado.

### R4.6 Rate limiting
Deberá evaluarse la limitación de tráfico por origen, destino, flujo u otra dimensión pertinente.

### R4.7 Bloqueo
Deberá poder bloquearse tráfico identificado como malicioso cuando corresponda.

### R4.8 Disponibilidad
La mitigación deberá procurar preservar el servicio legítimo.

### R4.9 Recuperación
La política normal deberá poder restaurarse después del incidente.

### R4.10 Medición
Deberán medirse tiempo de detección, tiempo de mitigación e impacto sobre el servicio.

---

## R5 — Seguridad perimetral

### R5.1 Perímetro
La solución deberá definir mecanismos de control entre redes externas e internas.

### R5.2 IDS/IPS
Deberá evaluarse el uso de IDS, IPS o ambos.

### R5.3 Inspección
El tráfico externo relevante deberá poder analizarse para identificar actividad maliciosa.

### R5.4 Bloqueo por IP
Deberá poder bloquearse tráfico desde direcciones IP identificadas como maliciosas.

### R5.5 Bloqueo hacia destinos
Deberá contemplarse el bloqueo de conexiones hacia destinos maliciosos cuando corresponda.

### R5.6 Inteligencia
Deberá definirse cómo se determinará que una IP, URL u otro indicador es malicioso.

### R5.7 Integración SDN
Los eventos perimetrales deberán poder generar políticas o acciones sobre la red SDN.

### R5.8 Registro
Los eventos deberán poder registrarse.

---

# 2. Requerimientos transversales

### RT-01 — Gestión centralizada de políticas
Deberá existir un mecanismo coherente para definir y administrar políticas.

### RT-02 — Separación de responsabilidades
Los componentes de identidad, autorización, detección, mitigación, monitoreo y administración deberán tener responsabilidades delimitadas.

### RT-03 — Integración SDN
Deberá definirse la interacción entre aplicaciones, controlador y dispositivos SDN.

### RT-04 — Northbound
Deberá definirse la interfaz mediante la cual las aplicaciones/administración interactúan con el controlador, cuando corresponda.

### RT-05 — Southbound
Deberá definirse el mecanismo mediante el cual el controlador comunica reglas a los dispositivos.

### RT-06 — Monitoreo
La solución deberá proporcionar información suficiente sobre estado de red y eventos.

### RT-07 — Auditoría
Los eventos relevantes deberán poder almacenarse para análisis.

### RT-08 — Respuesta automatizada
Las amenazas que cumplan las condiciones establecidas deberán poder activar acciones automáticas.

### RT-09 — Administración
Los administradores deberán disponer de mecanismos para consultar y modificar políticas.

### RT-10 — Recuperación
Las medidas temporales deberán poder revertirse.

---

# 3. Requerimientos no funcionales

### RNF-01 — Seguridad
La solución deberá minimizar accesos no autorizados.

### RNF-02 — Disponibilidad
Los mecanismos de seguridad no deberán provocar indisponibilidad innecesaria.

### RNF-03 — Rendimiento
La sobrecarga introducida deberá mantenerse dentro de límites aceptables definidos experimentalmente.

### RNF-04 — Latencia
Las decisiones críticas deberán ejecutarse con latencia compatible con la operación prevista.

### RNF-05 — Escalabilidad
La arquitectura deberá admitir crecimiento de usuarios, dispositivos, sesiones y eventos.

### RNF-06 — Flexibilidad
Las políticas deberán poder modificarse sin rediseñar completamente la solución.

### RNF-07 — Modularidad
Los módulos deberán presentar responsabilidades e interfaces claras.

### RNF-08 — Observabilidad
Deberá existir información suficiente para supervisar la operación.

### RNF-09 — Trazabilidad
Las acciones relevantes deberán poder asociarse con usuarios, eventos, flujos o políticas cuando la información esté disponible.

### RNF-10 — Mantenibilidad
La estructura deberá facilitar correcciones y ampliaciones.

### RNF-11 — Reproducibilidad
Las pruebas deberán poder repetirse bajo condiciones controladas.

### RNF-12 — Verificabilidad
Los requisitos críticos deberán poder comprobarse mediante métricas objetivas.

---

# 4. Requisitos arquitectónicos

### RA-01 — Arquitectura integral
La arquitectura deberá representar la interacción de R1–R5.

### RA-02 — Plano de control
Deberá identificarse el controlador SDN y sus responsabilidades.

### RA-03 — Plano de datos
Deberán identificarse los dispositivos que ejecutan las decisiones.

### RA-04 — Aplicaciones de seguridad
Deberán identificarse los módulos de políticas, detección, mitigación, monitoreo y administración.

### RA-05 — Flujo de información
Deberá especificarse qué información intercambia cada componente relevante.

### RA-06 — Flujo de decisión
Deberá poder trazarse:

**evento → detección → evaluación → decisión → política → aplicación → resultado.**

### RA-07 — Fallos
Deberán identificarse puntos de fallo y sus efectos.

### RA-08 — Escalabilidad
Deberá evaluarse el comportamiento ante aumento de usuarios y tráfico.

### RA-09 — Protección del plano de control
El acceso al controlador y sus interfaces administrativas deberá estar restringido.

---

# 5. Casos de uso mínimos

## CU-01 — Acceso autorizado
Un usuario con credenciales válidas solicita acceso y obtiene únicamente los permisos correspondientes a su rol.

## CU-02 — Acceso no autorizado
Un usuario no autorizado intenta acceder y el sistema rechaza la solicitud y registra el evento.

## CU-03 — Acceso autorizado a recurso privilegiado
Un usuario autorizado solicita un recurso privilegiado y el acceso es permitido y registrado.

## CU-04 — Acceso no autorizado a recurso privilegiado
Un usuario sin privilegios suficientes intenta acceder y el sistema bloquea la solicitud.

## CU-05 — Port scanning
Un host genera múltiples intentos de conexión; el sistema detecta el patrón y aplica la respuesta definida.

## CU-06 — IP spoofing
Se detecta tráfico inconsistente con las condiciones de origen esperadas y se aplica la respuesta definida.

## CU-07 — DDoS interno
El tráfico hacia un servidor supera el comportamiento esperado; el sistema detecta, mitiga y posteriormente recupera la política normal.

## CU-08 — Ataque externo
El tráfico externo es inspeccionado; una amenaza identificada genera alerta, bloqueo o mitigación.

## CU-09 — Gestión de política
Un administrador se autentica, modifica una política y la aplica mediante el sistema.

## CU-10 — Recuperación
Después de un incidente, el sistema elimina o modifica las reglas temporales y retorna a la política normal.

---

# 6. Flujos operativos

## 11.1 Operación normal

**Usuario → identificación/autenticación → rol → política → recurso → monitoreo → registro.**

## 11.2 Acceso no autorizado

**Solicitud → autenticación/autorización → rechazo → registro → alerta cuando corresponda.**

## 11.3 Incidente de seguridad

**Tráfico → monitoreo → detección → clasificación → decisión → mitigación → registro → recuperación.**

## 11.4 Administración

**Administrador → autenticación → gestión de política → validación → aplicación → auditoría.**

---

# 7. Políticas de seguridad

### PS-01 — Mínimo privilegio
Cada usuario deberá disponer únicamente de los permisos necesarios.

### PS-02 — Denegación por defecto
Una solicitud sin autorización explícita deberá considerarse no autorizada, salvo justificación del diseño final.

### PS-03 — Separación por roles
Los privilegios deberán asociarse principalmente a roles.

### PS-04 — Protección diferenciada
Los recursos críticos deberán recibir controles superiores.

### PS-05 — Respuesta proporcional
La mitigación deberá corresponder al tipo y nivel de amenaza.

### PS-06 — Trazabilidad
Las decisiones relevantes deberán poder auditarse.

### PS-07 — Reversibilidad
Las acciones temporales deberán poder revertirse.

---

# 8. Criterios de éxito

La solución deberá evaluarse mediante criterios cualitativos y cuantitativos.

## Seguridad

- tasa de bloqueo de accesos inválidos;
- precisión en la restricción de recursos;
- tasa de detección;
- tasa de falsos positivos.

## Rendimiento

- latencia de autenticación;
- latencia de autorización;
- tiempo de detección;
- tiempo de mitigación;
- throughput;
- solicitudes por segundo.

## Disponibilidad y resiliencia

- disponibilidad durante ataques;
- tiempo de recuperación;
- impacto sobre tráfico legítimo.

## Escalabilidad

- usuarios concurrentes;
- sesiones concurrentes;
- eventos por segundo;
- cantidad de políticas/reglas gestionadas.

## Consumo de recursos

- CPU;
- memoria;
- ancho de banda;
- utilización de recursos de dispositivos SDN;
- TCAM, cuando corresponda.

---

# 9. Requisitos de pruebas

### PT-01 — Pruebas funcionales
Cada requerimiento implementado deberá contar con pruebas positivas.

### PT-02 — Pruebas negativas
Deberán probarse condiciones en las que el sistema debe rechazar, bloquear o mitigar.

### PT-03 — Rendimiento
Deberá medirse el comportamiento bajo diferentes cargas.

### PT-04 — Ataques
Los escenarios de seguridad deberán ejecutarse en el entorno controlado.

### PT-05 — Recuperación
Deberá comprobarse el retorno a operación normal.

### PT-06 — Escalabilidad
Cuando resulte viable, deberán incrementarse progresivamente usuarios, flujos, solicitudes o eventos.

### PT-07 — Comparación de alternativas
Cuando existan alternativas de diseño, deberán compararse mediante métricas objetivas.

---

# 10. Administración y observabilidad

### ADM-01
El administrador deberá poder consultar las políticas activas.

### ADM-02
El administrador deberá poder identificar eventos de seguridad relevantes.

### ADM-03
La solución deberá proporcionar información suficiente para investigar incidentes.

### ADM-04
Los cambios de política deberán poder registrarse.

### ADM-05
Las acciones automáticas de mitigación deberán poder identificarse posteriormente.

---

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

---

# 14. Trazabilidad inicial

| Objetivo | Requerimiento | Casos de uso | Métricas principales |
|---|---|---|---|
| Controlar acceso | R1 | CU-01, CU-02 | bloqueo, latencia |
| Proteger recursos | R2 | CU-03, CU-04 | precisión de restricción |
| Proteger intranet | R3 | CU-05, CU-06 | detección, falsos positivos |
| Preservar disponibilidad | R4 | CU-07 | detección, mitigación, disponibilidad |
| Proteger perímetro | R5 | CU-08 | detección, bloqueo |
| Gestionar seguridad | Transversal | CU-09 | aplicación de política |
| Recuperar operación | Transversal | CU-10 | tiempo de recuperación |

---

# 15. Riesgos iniciales

| Riesgo | Impacto | Respuesta propuesta |
|---|---|---|
| Complejidad excesiva | Alto | Priorizar los tres requerimientos asignados |
| Falsos positivos | Alto | Medir y ajustar criterios |
| Sobrecarga del controlador | Alto | Evaluar CPU, memoria y latencia |
| Exceso de reglas SDN | Alto | Evaluar recursos del switch |
| Punto único de fallo | Alto | Analizar dependencia del controlador |
| Bloqueo de usuarios legítimos | Alto | Diseñar recuperación y reglas temporales |
| Ataques difíciles de reproducir | Medio | Definir escenarios controlados |
| Integración deficiente | Alto | Definir interfaces desde HLD |
| Falta de métricas | Alto | Diseñar pruebas antes de implementar |
| Falta de tiempo | Alto | Priorizar P0 antes de extensiones |

---

# 16. Priorización

## P0 — Obligatorio

- arquitectura integral R1–R5;
- tres requerimientos asignados completamente diseñados;
- implementación de los tres requerimientos;
- casos de uso principales;
- plan de pruebas;
- métricas;
- integración SDN.

## P1 — Alta prioridad

- monitoreo centralizado;
- registro y auditoría;
- gestión de políticas;
- recuperación;
- interfaz de administración.

## P2 — Diferencial

- implementación parcial de requerimientos no asignados;
- automatización avanzada;
- detección adaptativa;
- comparación de estrategias;
- análisis avanzado de anomalías.

---

# 17. Evolución del documento

Esta versión constituye una **línea base inicial**. Deberá refinarse durante:

1. Concepto de Operación.
2. Casos de uso.
3. Arquitectura.
4. HLD.
5. Comparación cuantitativa de alternativas.
6. LLSD.
7. Topología e infraestructura.
8. Plan de pruebas.
9. Implementación.
10. Evaluación experimental.

Toda modificación deberá conservar trazabilidad entre requisitos, arquitectura, implementación y pruebas.

---

# 18. Resumen ejecutivo

La solución deberá responder a cuatro preguntas:

**¿Quién puede entrar?**  
R1 — Identidad, roles y control de acceso.

**¿A qué puede acceder?**  
R2 — Autorización y protección de recursos privilegiados.

**¿Qué ocurre ante una amenaza interna?**  
R3/R4 — Detección, mitigación y preservación de disponibilidad.

**¿Qué ocurre ante una amenaza externa?**  
R5 — Seguridad perimetral, detección y bloqueo.

Todos estos mecanismos deberán integrarse dentro de una arquitectura SDN coherente, modular, verificable y capaz de evolucionar.

---

## Estado de esta versión

| Elemento | Estado |
|---|---|
| Contexto | Ver `../A-Modelo_de_dominio/00_Proyecto_SDN.md` |
| Objetivo | Ver `../A-Modelo_de_dominio/00_Proyecto_SDN.md` |
| Alcance | Ver `../A-Modelo_de_dominio/00_Proyecto_SDN.md` |
| Actores | Ver `../A-Modelo_de_dominio/01_actores-roles_y_agentes.md` |
| R1–R5 | Primera versión |
| Requerimientos transversales | Primera versión |
| Requisitos no funcionales | Primera versión |
| Restricciones | Ver `02_restricciones.md` |
| Casos de uso | Primera versión |
| Métricas | Primera versión |
| Arquitectura tecnológica | Pendiente |
| HLD | Pendiente |
| LLSD | Pendiente |
| Plan de pruebas | Pendiente |
| Implementación | Pendiente |

**Versión 0.1 — Sujeta a revisión y refinamiento arquitectónico.**
