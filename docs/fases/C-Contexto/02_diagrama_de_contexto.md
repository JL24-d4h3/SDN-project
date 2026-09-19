# Diagrama de contexto

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** C — Contexto
**Estado:** Borrador formal para revisión

---

## 1. Propósito y nivel

El diagrama representa el sistema como una caja negra y muestra **quién y qué intercambia información con él**. No describe componentes internos: la descomposición funcional y la arquitectura lógica corresponden a las fases D y E.

Responde una sola pregunta: ¿dónde empieza y termina la solución? La respuesta está en [`01_limite_del_sistema.md`](01_limite_del_sistema.md).

---

## 2. Diagrama

```text
        ┌───────────────────────────┐        ┌────────────────────────────┐
        │  USUARIOS                 │        │  SISTEMAS EXTERNOS         │
        │  Alumno · Docente         │        │  Internet / red externa    │
        ├───────────────────────────┤        │  Identidad institucional   │
        │  ADMINISTRADORES          │        │  Inteligencia de amenazas  │
        │  Especialista de TI       │        └──────────────┬─────────────┘
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
        │  control de acceso · autorización · detección · mitigación  │
        │  administración de políticas · registro y auditoría         │
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
| Alumno, Docente | Plataforma | Solicitud de acceso y de uso de servicios | Autenticación, autorización y registro (R1, R2) |
| Plataforma | Alumno, Docente | Decisión de acceso y conectividad al servicio autorizado | Aplicar la política vigente |
| Especialista de TI | Plataforma | Consultas de tráfico y de eventos; acciones de mitigación autorizadas | Supervisión y respuesta ante incidentes (R3, R4) |
| Administrador de Red | Plataforma | Cambios de políticas, de reglas y de segmentación | Administración operativa de la red |
| Superadministrador | Plataforma | Gestión de administradores, de roles y de configuración global | Control de la plataforma |
| Plataforma | Administradores | Alertas, eventos, estado de red y registros | Operación y auditoría |
| Internet | Plataforma | Tráfico entrante | Servicio legítimo e inspección perimetral (R5) |
| Plataforma | Internet | Tráfico saliente autorizado | Conectividad externa |
| Identidad institucional | Plataforma | Verificación de credenciales y atributos | Autenticación (R1) |
| Inteligencia de amenazas | Plataforma | Indicadores de IP, URL u otros | Determinar qué es malicioso (R5.6) |
| Plataforma | Activos protegidos | Tráfico permitido; bloqueo del no autorizado | Protección de recursos (R2) |
| Activos protegidos | Plataforma | Registros y eventos de servicio | Detección y trazabilidad |
| Atacante externo | Plataforma | Tráfico malicioso desde redes externas | Objeto de R5 y, si atraviesa el perímetro, de R3 y R4 |
| Atacante interno, nodo comprometido | Plataforma | Tráfico anómalo originado dentro de la red | Objeto de R3 y R4 |

---

## 4. Qué no muestra el diagrama

- Los componentes internos de la plataforma y sus interfaces (fases D y E).
- La topología física y la segmentación (Fase H; ver [`04_alcance_de_la_infraestructura.md`](04_alcance_de_la_infraestructura.md)).
- Las decisiones tecnológicas: controlador, IDS/IPS, broker o persistencia (Fase G).

---

## 5. Cuestiones abiertas

- Si la inteligencia de amenazas proviene de un servicio externo, de listas propias o de ambos (R5.6).
- Si la verificación de identidad es síncrona con cada acceso o se apoya en sesiones ya establecidas.
