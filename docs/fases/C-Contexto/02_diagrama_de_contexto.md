# Diagrama de contexto

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** C — Contexto
**Estado:** Borrador formal para revisión

---

## 1. Propósito y nivel

El diagrama representa el sistema como una caja negra y muestra **quién y qué intercambia información con él**. No describe componentes internos: la descomposición funcional y la arquitectura lógica corresponden a la Fase D.

Responde una sola pregunta: ¿dónde empieza y termina la solución? La respuesta está en [`01_limite_del_sistema.md`](01_limite_del_sistema.md).

---

## 2. Diagrama

```text
        ┌───────────────────────────┐        ┌────────────────────────────┐
        │  USUARIOS                 │        │  SISTEMAS EXTERNOS         │
        │  Usuario académico        │        │  Internet / red externa    │
        │  (BASE → ACADÉMICO)       │        │  Identidad (IdP/LDAP)      │
        ├───────────────────────────┤        │  Inteligencia de amenazas  │
        │  OPERADORES               │        └──────────────┬─────────────┘
        │  Especialista de TI       │                       │
        │  Administrador de Red     │                       │
        │  Superadministrador       │                       │
        └─────────────┬─────────────┘                       │
                      │                                     │
       acceso y uso de servicios          tráfico externo, verificación
       administración y supervisión       de identidad, indicadores
                      │                                     │
                      ▼                                     ▼
        ┌─────────────────────────────────────────────────────────────┐
        │                                                             │
        │              PLATAFORMA SDN DE SEGURIDAD                    │
        │                                                             │
        │  perfiles de acceso · portal cautivo · AAA · detección      │
        │  mitigación · administración de políticas · auditoría       │
        │                                                             │
        └───────────────────────────────┬─────────────────────────────┘
                                        │
                        controla el acceso y protege
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │  ACTIVOS PROTEGIDOS           │
                        │  servidores y servicios       │
                        │  académicos y administrativos │
                        └───────────────────────────────┘

  ── FUENTES DE AMENAZA ────────────────────────────────────────────────
     Atacante externo   → actúa desde Internet
     Atacante interno   → opera con acceso legítimo a la red
     Nodo comprometido  → dispositivo legítimo bajo control ajeno
```

---

## 3. Interacciones

| Origen | Destino | Qué fluye | Propósito |
|---|---|---|---|
| Usuario académico | Plataforma | Solicitud de configuración (DHCP) y de uso de servicios | Conectividad base y autorización por defecto (R1, R2) |
| Usuario académico | Plataforma | Login en el portal (contra el IdP institucional) | Obtener el perfil ACADÉMICO: servicios académicos e Internet (R1) |
| Plataforma | Usuario académico | Perfil BASE y conectividad al servicio autorizado | Aplicar la política vigente |
| Usuario académico | Plataforma | Solicitud de elevación temporal | Elevación aprobada por el Administrador de Red, con TTL |
| Especialista de TI | Plataforma | Login (portal cautivo); consultas de tráfico y de eventos; acciones de mitigación autorizadas | Supervisión y respuesta ante incidentes (R3, R4) |
| Administrador de Red | Plataforma | Login (portal cautivo); cambios de políticas, de reglas y de segmentación; aprobación de elevaciones; altas en el registro de dispositivos | Administración operativa de la red |
| Superadministrador | Plataforma | Login (portal cautivo o acceso remoto); gestión de operadores, de roles y de configuración global | Control de la plataforma |
| Plataforma | Operadores | Alertas, eventos, estado de red y registros | Operación y auditoría |
| Internet | Plataforma | Tráfico entrante | Servicio legítimo e inspección perimetral (R5) |
| Plataforma | Internet | Tráfico saliente autorizado | Conectividad externa |
| Identidad institucional (IdP/LDAP) | Plataforma (AAA) | Verificación de credenciales y atributos de la comunidad universitaria | Autenticación de la comunidad (R1) |
| Inteligencia de amenazas | Plataforma | Indicadores de IP, URL u otros | Determinar qué es malicioso (R5.6) |
| Plataforma | Activos protegidos | Tráfico permitido; bloqueo del no autorizado | Protección de recursos (R2) |
| Activos protegidos | Plataforma | Registros y eventos de servicio | Detección y trazabilidad |
| Atacante externo | Plataforma | Tráfico malicioso desde redes externas | Objeto de R5 y, si atraviesa el perímetro, de R3 y R4 |
| Atacante interno, nodo comprometido | Plataforma | Tráfico anómalo originado dentro de la red | Objeto de R3 y R4 |

---

## 4. Qué no muestra el diagrama

- Los componentes internos de la plataforma y sus interfaces (Fase D).
- La topología física y la segmentación (Fase H; ver [`04_alcance_de_la_infraestructura.md`](04_alcance_de_la_infraestructura.md)).
- Las decisiones tecnológicas: controlador, IDS/IPS, broker o persistencia (Fase F).

---

## 5. Cuestiones abiertas

- Si la inteligencia de amenazas proviene de un servicio externo, de listas propias o de ambos (R5.6).
