# Escenarios de fallo

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** E — Validación del HLD
**Estado:** Borrador formal para revisión

---

Qué ocurre cuando cada pieza deja de responder. La pregunta no es «¿se cae?» —toda pieza se cae— sino «¿qué sostiene la red mientras tanto, con qué se recupera y qué queda fuera del alcance del prototipo?». Cierra el requisito RA-07 (puntos de fallo y sus efectos). Dos mecanismos estructurales responden primero: **el plano de datos conserva lo instalado** (P2 — el controlador no es camino del tráfico) y **todo privilegio y toda mitigación expira por sí solo** (P10 — ningún estado pegado sobrevive a su timeout).

## 1. Plano de control y plano de datos

| Pieza que falla | Efecto inmediato | Qué sostiene el diseño | Veredicto |
|---|---|---|---|
| **Controlador SDN** | No hay decisiones nuevas: dispositivos nuevos se quedan en BASE sin portal resuelto; elevaciones y mitigaciones pendientes sin resolver | El tráfico ya instalado sigue fluyendo (P2); los switches conservan sus reglas y sus timeouts; al reconectar, el switch se re-registra y las reglas se reinstalan | Cubierto por diseño; la **redundancia del plano de control** se decide en la Fase F (clúster del controlador / switches con más de un controlador) |
| **Canal de control (red de gestión)** | Se pierde el control y la observación de los switches | El plano de datos queda intacto: es un canal separado (out-of-band) y no transporta tráfico de usuarios | Cubierto por diseño |
| **Un switch** | Se pierde su segmento; el resto de la red no se ve afectado | Decisión centralizada, ejecución distribuida (P2): el fallo queda aislado a su dominio; la caída se detecta por eventos de puerto | Cubierto (aislamiento del fallo); la **redundancia de nodos y enlaces** pertenece al despliegue (Fase H) |

## 2. Cadena de detección y respuesta

| Pieza que falla | Efecto inmediato | Qué sostiene el diseño | Veredicto |
|---|---|---|---|
| **Monitor** | No hay observación nueva: la línea base deja de actualizarse; la detección queda ciega a partir de ahí | Las mitigaciones ya activas siguen vigentes y expiran por timeout (P10); al volver, la observación se reanuda sin estado que reparar | Cubierto por diseño (degradación, no pérdida) |
| **Detection Engine** | No hay detección nueva de anomalías | Las mitigaciones activas expiran solas; los eventos en tránsito quedan en las colas del intermediario (P13) | Cubierto por diseño; la garantía de entrega depende del producto de mensajería (Fase F) |
| **Incident Manager** | Incidentes sin registrar ni cerrar | Las mitigaciones no dependen de él para expirar: el timeout y FLOW_REMOVED cierran igual; al volver, reconcilia el estado | Cubierto por diseño; reconciliación a especificar con el producto (Fase F) |
| **Policy Engine** | No hay decisiones nuevas: ni elevaciones ni mitigaciones nuevas; el resto de la cadena observa sin poder actuar | Las reglas vigentes y sus TTL son el estado seguro (P10); la red ya decidida sigue operando | Cubierto por diseño; es el componente crítico junto con el controlador — su redundancia se decide en la Fase F |
| **Intermediario de eventos** | Los componentes de seguridad dejan de intercambiar eventos | Los publicadores absorben ráfagas en colas locales (P13) mientras el intermediario se recupera | Parcial: el comportamiento exacto (persistencia, reintentos) se fija con el producto elegido en la Fase F |

## 3. Identidad, administración y registros

| Pieza que falla | Efecto inmediato | Qué sostiene el diseño | Veredicto |
|---|---|---|---|
| **IAM/AAA** | No hay nuevos logins ni elevaciones nuevas | Las sesiones vigentes continúan hasta su TTL (P10); el fallo del IdP institucional no impide el login de operadores (repositorio propio) ni al revés — las dos fuentes son independientes | Cubierto por diseño (degradación acotada) |
| **IdP institucional** (externo) | La comunidad no puede autenticarse: nadie nuevo obtiene perfil ACADÉMICO | Lo ya autenticado sigue hasta su TTL; los operadores entran por el repositorio propio; la mitigación activa no depende del IdP | Cubierto (el diseño no depende del IdP para operar) |
| **Registro de dispositivos privilegiados** | No se habilitan nuevos dispositivos de operador | Los ya registrados siguen operando; sin match, el perfil es BASE (P5): el fallo degrada hacia el lado seguro | Cubierto por diseño |
| **Consola** | No hay administración interactiva | Las políticas vigentes siguen; la consola no es camino de datos ni de decisión | Cubierto por diseño (degradación operativa) |
| **Auditoría y almacenamiento** | Los eventos de seguridad dejan de persistirse | Nada operativo depende de ella en el momento; sí la trazabilidad (RNF-09) | Parcial: retención y recuperación de registros a definir (Fase F) |

## 4. Redundancia y recuperación: qué es diseño y qué es despliegue

- **Garantizado por diseño (ya validado en esta fase):** el plano de datos no depende del controlador en régimen; toda mitigación y privilegio expira por timeout; el aislamiento de fallos es por segmento y por switch; el estado de retorno es siempre BASE.
- **Decisión de la Fase F:** la redundancia del plano de control —clúster del controlador elegido y/o switches conectados a más de un controlador— con su mecanismo de failover. El insumo está dicho: el diseño no la exige para operar, la exige para no degradar durante la caída.
- **Despliegue (Fase H):** redundancia física de nodos y enlaces. El alcance de la infraestructura (C-04) ya declara que estos escenarios **se analizan por diseño y no se despliegan** en el prototipo.
- **Cuantificación (prototipo):** tiempo de recuperación y de reinstalación de reglas tras la vuelta del controlador (R4.10, RA-07).

## 5. Cierre del requisito

RA-07 quedaba como el requisito «deberán identificarse puntos de fallo y sus efectos»: queda cerrado con §1–§3. Lo que no cierra aquí no es un hueco de arquitectura sino una frontera de alcance: redundancia del controlador (Fase F), redundancia física (Fase H) y sus tiempos (prototipo).
