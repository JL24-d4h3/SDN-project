# Marco del proyecto SDN

**Curso:** TEL354 — Redes Definidas por Software
**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** A — Modelo de dominio
**Fecha:** 17 de septiembre de 2026

---

Este documento establece el marco del proyecto: qué se propone, por qué y con qué límites.

Continúa en documentos separados:

- **Requisitos** — funcionales, transversales, no funcionales, arquitectónicos y de pruebas: [`../B-Drivers/01_Requisitos_y_Restricciones_SDN_v0.1.md`](../B-Drivers/01_Requisitos_y_Restricciones_SDN_v0.1.md)
- **Restricciones** — condiciones impuestas al proyecto: [`../B-Drivers/02_restricciones.md`](../B-Drivers/02_restricciones.md)
- **Actores, roles y agentes**: [`01_actores-roles_y_agentes.md`](01_actores-roles_y_agentes.md)
- **Recursos y servicios**: [`02_recursos_y_servicios.md`](02_recursos_y_servicios.md)

---

## 1. Propósito

Diseñar una solución de seguridad basada en SDN para una red de campus académico, a partir de los cinco requerimientos del proyecto:

- **R1:** Controlar el acceso a la red: perfil mínimo por defecto para todo dispositivo conectado, y privilegios superiores solo mediante autenticación y autorización (acorde con el rol y el contexto).
- **R2:** Restringir el acceso a recursos privilegiados solo a usuarios autorizados.
- **R3:** Detectar y mitigar ataques encubiertos en la intranet.
- **R4:** Detectar y mitigar ataques DDoS brute-force en la intranet.
- **R5:** Proteger a la red de ataques externos mediante seguridad perimetral.

> **Criterio de alcance:** la arquitectura deberá considerar integralmente los cinco requerimientos. La implementación detallada se concentrará en los tres requerimientos asignados al grupo. Las decisiones marcadas como propuestas deberán validarse durante HLD, LLSD y pruebas.

---

## 2. Contexto y problema

Una red de campus académico integra numerosos usuarios, dispositivos y servicios que requieren conectividad permanente. Los usuarios tienen distintas responsabilidades y, por tanto, diferentes necesidades de acceso. Asimismo, existen recursos que requieren protección diferenciada y amenazas que pueden originarse tanto dentro como fuera de la red.

La solución deberá proporcionar mecanismos para:

1. controlar el acceso según dispositivo, perfil y contexto, con identidad solo para elevar privilegios;
2. proteger recursos privilegiados;
3. detectar comportamientos maliciosos dentro de la intranet;
4. preservar la disponibilidad ante ataques de saturación;
5. controlar amenazas provenientes del exterior.

El problema se formula como la necesidad de **gestionar y proteger una red de campus mediante mecanismos programables y coherentes con una arquitectura SDN**.

---

## 3. Objetivo general

Diseñar una solución de seguridad basada en SDN que permita controlar el acceso de usuarios, proteger recursos privilegiados, detectar y mitigar amenazas internas y externas y preservar la disponibilidad de los servicios de red.

La arquitectura deberá permitir que las decisiones de seguridad puedan traducirse en políticas y acciones aplicables sobre la infraestructura SDN.

---

## 4. Alcance

### 4.1 Alcance funcional

La solución deberá contemplar:

- control de acceso;
- autorización sobre recursos;
- monitoreo de tráfico;
- detección de amenazas;
- mitigación;
- seguridad perimetral;
- gestión de políticas;
- registro y auditoría;
- recuperación;
- evaluación cuantitativa.

### 4.2 Alcance de implementación

El grupo deberá implementar los tres requerimientos asignados por el proyecto del curso.

La arquitectura global deberá mostrar cómo los cinco requerimientos podrían coexistir e interactuar dentro de una solución única.

### 4.3 Entorno de referencia

El prototipo estará orientado a una red de campus académico representativa. No será necesario reproducir físicamente la escala real de la universidad; el entorno deberá ser suficiente para validar los escenarios y métricas definidos.
