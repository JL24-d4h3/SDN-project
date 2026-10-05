# Casos de uso → componentes

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** E — Validación del HLD
**Estado:** Borrador formal para revisión

---

Cada caso de uso de [B-00](../B-Drivers_de_arquitectura/00_Proyecto_ConOps_y_CU.md) §5, con los componentes del HLD que lo realizan y dónde está descrito su mecanismo. La secuencia detallada de cada flujo vive en la serie de flujo (partes 0–5); aquí se comprueba que **ningún caso queda sin dueño**.

## 1. Casos de uso y componentes

| Caso de uso | Componentes que lo realizan | Dónde está descrito | Veredicto |
|---|---|---|---|
| **CU-01 — Acceso autorizado** | Switches (perfil BASE y escalera de prioridades) · Controlador (FLOW_MOD; camino al portal y a los servicios) · IAM/AAA con portal (RADIUS: IdP para la comunidad; repositorio propio + TOTP para operadores) · Policy Engine (perfil o sesión) · Registro de dispositivos (habilitación del operador) · Auditoría | Partes 2 y 3 §5–6; D-05 §1, §6–7 | Cubierto |
| **CU-02 — Acceso no autorizado** | Switches (DROP por defecto) · Controlador (regla de denegación) · Policy Engine · Auditoría (registro) | Parte 3 §2 y §6; D-11 §2 | Cubierto |
| **CU-03 — Acceso autorizado a recurso privilegiado** | Policy Engine (elevación con TTL; P28/P29) · Controlador (regla de sesión con idle_timeout) · Switches · IAM/AAA · Auditoría | Parte 3 §7; D-05 §5 | Cubierto |
| **CU-04 — Acceso no autorizado a recurso privilegiado** | Policy Engine (denegación) · Switches (DROP) · Auditoría | Parte 3 §6–7 | Cubierto |
| **CU-05 — Port scanning** | Monitor (línea base) · Detection Engine (múltiples destinos) · Incident Manager · Policy Engine (RATE_LIMIT → BLOCK) · Controlador · Switches | D-11.1; parte 4 | Cubierto |
| **CU-06 — IP spoofing** | Controlador (asociaciones MAC↔IP↔switch↔puerto; detección de incoherencia) · Monitor y Detection Engine (evento) · Policy Engine (respuesta escalonada) · Switches (port security en puertos sensibles) | Parte 3 §9; D-11 §4 | Cubierto (la MAC no se impide — se detecta, P7) |
| **CU-07 — DDoS interno** | Monitor (línea base por destino) · Detection Engine (desviación sostenida) · Incident Manager · Policy Engine (escalera de mitigación) · Controlador (METER_MOD / FLOW_MOD) · Switches | Parte 4; D-11 §4 | Cubierto |
| **CU-08 — Ataque externo** | — (sin componente de frontera asignado) | D-11.1 (amenaza); C-04 §6 y D-10 §6 (perímetro por definir) | **Hueco** |
| **CU-09 — Gestión de política** | Consola (interfaz) · IAM/AAA (sesión de operador con MFA) · Policy Engine (PolicyRepository) · Controlador (aplicación) · Auditoría | D-06 §4; componentes/02; access/02 | Cubierto |
| **CU-10 — Recuperación** | Policy Engine (expiración de TTL; retiro) · Controlador (retirada por cookie) · Monitor (MitigationVerified / MitigationExpired) · Incident Manager (cierre) · Auditoría | Parte 4; D-04 §3 (P10) | Cubierto |

## 2. Huecos

- **CU-08 — Ataque externo.** El perímetro no tiene componente asignado: R5 no está asignado a ningún grupo y el firewall está por definir (C-04 §6, D-10 §6). Se cierra al fijar el alcance del perímetro —sistema externo con el que integrarse o componente propio— y en la fase de decisiones tecnológicas (R5.2 pide evaluar IDS/IPS). Es el único caso de uso sin dueño.
