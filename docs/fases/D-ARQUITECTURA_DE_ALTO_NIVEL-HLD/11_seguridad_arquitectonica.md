# Seguridad arquitectónica

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** D — Arquitectura de alto nivel (HLD)
**Estado:** Borrador formal para revisión

---

Cómo la arquitectura realiza la seguridad: la jerarquía de confianza, los puntos de enforcement, la protección del plano de control y la cobertura de amenazas. No repite los mecanismos (están en la serie de flujo); fija **dónde** actúa cada control y por qué.

## 1. La jerarquía de confianza

```text
Sin presencia en campus            →  sin acceso
Presencia física en campus         →  perfil BASE (confianza inicial, RP-13)
Login en el portal                 →  perfil ACADÉMICO (comunidad)
                                      o identidad + rol (operadores)
Autorización contextual            →  privilegios adicionales (TTL / sesión)
```

Cada peldaño habilita el siguiente y ninguno puede saltarse (P6): la presencia física jamás justifica privilegios; el registro de dispositivos jamás concede por sí solo; el login sin contexto vigente no produce reglas permanentes.

## 2. Puntos de enforcement

| Punto | Qué aplica | Mecanismo |
|---|---|---|
| **Switch de ingreso** | El perfil BASE: denegación por defecto hacia infraestructura y mínimo de conectividad (DHCP, DNS y portal) | Entradas de flujo con prioridades (DROP a red de gestión, prioridad 100) |
| **Portal cautivo / IAM** | La identidad de la población: perfil ACADÉMICO (comunidad) o sesión de rol (operadores) | Autenticación contra el IdP o contra el repositorio propio con MFA; sesión con vigencia |
| **Policy Engine** | La autorización contextual: qué perfil corresponde a cada sesión o elevación | Condiciones ABAC-like (identidad + dispositivo + contexto + recurso + acción + vigencia) |
| **Controlador** | La traducción de cada decisión a reglas concretas y reversibles | FLOW_MOD con cookie, prioridad y timeouts |
| **Plano de datos (meter/drop)** | La mitigación en el punto de ingreso | Meters para limitar; DROP para bloquear; ambos temporales (P10) |
| **Registro de dispositivos** | La pertenencia al catálogo privilegiado | Match explícito; no match → BASE (P7) |

La misma decisión atraviesa todos los puntos en orden: perfil por defecto → identidad (si eleva) → política contextual → regla → ejecución → verificación.

## 3. Protección del plano de control (RA-09)

El controlador y sus interfaces administrativas son el objetivo de mayor valor de la solución. La arquitectura los protege en tres niveles:

1. **Aislamiento de red.** El controlador vive en la red de gestión, separada del plano de datos (out-of-band). Desde el perfil BASE existe una entrada DROP explícita hacia esa red: ningún usuario académico la alcanza, ni siquiera para escanearla.
2. **Identidad exigida.** Solo los operadores autenticados (portal/AAA) obtienen entradas que permiten alcanzar la gestión, con prioridad mayor y con idle_timeout ligado a la sesión (P6, P10).
3. **Canal de control sano.** El canal OpenFlow usa TCP 6653 en la red de gestión; los switches solo aceptan a su controlador configurado. La variante in-band exige además priorización del tráfico de control (serie de flujo, parte 2 §14).

## 4. Cobertura de amenazas

El listado consolidado de ataques y amenazas, con su origen y descripción, está en [`11.1_catalogo_de_ataques_y_amenazas.md`](11.1_catalogo_de_ataques_y_amenazas.md). Aquí se fija el control que la arquitectura aplica a cada uno:

| Amenaza | Control arquitectónico | Referencia |
|---|---|---|
| Atacante externo (R5) | Segmento perimetral con inspección y bloqueo por indicadores; integración SDN de los eventos de borde | R5.x; perímetro por definir (fase C) |
| Atacante interno (R3) | Perfil BASE restrictivo + detección de scanning/spoofing + respuesta escalonada | R3.x, P8 |
| Nodo comprometido (R3/R4) | Detección por anomalía + aislamiento del dispositivo (ISOLATE_DEVICE / cuarentena) | R3.7, R4.5 |
| DDoS volumétrico (R4) | Línea base + detección de tasas + mitigación en el switch de ingreso (meter/drop) | R4.x, P9 |
| Brute-force de solicitudes (R4) | Detección de intentos/conexiones por segundo + RATE_LIMIT/BLOCK por origen | R4.x |
| Suplantación de MAC | MAC como atributo (P7) + eventos MAC_MOVE + port security/802.1X en puertos sensibles | R3.3, flujo parte 3 |
| Compromiso del IdP | Es externo: el IAM consume su veredicto y la auditoría registra toda sesión; la mitigación no depende del IdP una vez establecida la sesión | SE-02, fase C |

## 5. Controles administrativos

La seguridad no termina en la red: las acciones de los operadores están controladas y registradas:

- **Separación de funciones.** Ningún rol define, aplica y evalúa una política sin control (fase A §2.6, doc 06 §4).
- **Registro con aprobación.** Las altas de operadores y de dispositivos privilegiados exigen decisión de autorización, vigencia explícita y responsable identificado (P30).
- **Accounting.** Toda mitigación y cambio queda asociado a su autor, motivo e incidente (P11).
- **Reversión obligatoria.** Toda medida temporal expira o se retira; el estado BASE es el punto de retorno (P10).

## 6. Datos sensibles

| Dato | Dónde vive | Protección |
|---|---|---|
| Credenciales de la comunidad | IdP institucional (externo) | El IAM no las almacena: consulta y descarta |
| Credenciales de operadores | Repositorio propio del IAM | Almacenadas con hash; MFA obligatorio (TOTP) |
| Registro de dispositivos privilegiados | `DeviceRepository` | Acceso solo por el servicio y por operadores autorizados; cada cambio auditado |
| Incidentes y eventos | `IncidentRepository`, `AuditRepository` | Consulta según rol (P08, P25); retención por definir |
| Reglas instaladas | Pipeline de los switches | Solo el controlador las modifica (P1) |

## 7. Lo que la arquitectura no cubre

- **Seguridad física del campus.** Asumida como condición de confianza (RP-13); su compromiso degrada el modelo a perfil BASE generalizado, y por eso se documenta como restricción, no se ignora.
- **Cifrado extremo a extremo del tráfico de usuario.** No es objetivo de la solución: se controla *quién puede* alcanzar qué, no el contenido de lo permitido.
- **Red inalámbrica y red de invitados.** Fuera del alcance hasta que se confirme lo contrario (fase A).

## 8. Cuestiones abiertas

- **Integración con el firewall perimetral.** Si existe uno institucional con el que integrarse (R5, fase C).
- **Retención e integridad de logs.** Cuánto tiempo se conservan y si se protegen contra manipulación (ligado a la retención de eventos del doc 08).
