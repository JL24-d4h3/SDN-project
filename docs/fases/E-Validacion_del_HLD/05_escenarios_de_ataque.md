# Escenarios de ataque → detección y respuesta

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** E — Validación del HLD
**Estado:** Borrador formal para revisión

---

Cada amenaza del catálogo ([`11.1_catalogo_de_ataques_y_amenazas.md`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/11.1_catalogo_de_ataques_y_amenazas.md)), con el punto donde se detecta, la respuesta que produce y el componente que la ejecuta. La cadena es siempre la misma (P8): **detector observa → Policy Engine decide → Controlador traduce → Switch ejecuta → Auditoría registra**; lo que cambia por amenaza es dónde se engancha.

## 1. Ataques

| Ataque | Detección | Respuesta | Componentes | Veredicto |
|---|---|---|---|---|
| **Network / port scanning** (R3.2 · CU-05) | Múltiples intentos de conexión a destinos distintos desde un origen | Escalera: RATE_LIMIT → BLOCK | Monitor · Detection Engine · Incident Manager · Policy Engine · Controlador · Switches | Cubierto (flujo parte 4) |
| **IP spoofing** (R3.3 · CU-06) | Incoherencia origen declarado vs. ubicación aprendida (MAC/IP/puerto) | Evento y respuesta escalonada; la incoherencia sostenida bloquea | Controlador (asociaciones) · Policy Engine | Cubierto (parte 3 §9; D-11 §4) |
| **Suplantación de MAC** (R3.3) | Evento MAC_MOVE: misma MAC en otro puerto o con otra identidad | Alerta → bloqueo → cuarentena; port security/802.1X en puertos sensibles | Controlador · Policy Engine · Switches | Cubierto (P7; D-11 §4) |
| **Ataques distribuidos** (R3.5) | Número de fuentes contra un mismo destino sobre la línea base | Mitigación por switch de ingreso de cada origen | Detection Engine · Policy Engine · Controlador | Cubierto (D-11.1) |
| **DDoS volumétrico / flood** (R4 · CU-07) | Tasas (pps, Mbps) muy por encima de la línea base del servicio | Meter en el switch de ingreso (RATE_LIMIT → DROP); verificación por contadores; recuperación por timeout | Monitor · Detection Engine · Incident Manager · Policy Engine · Controlador (METER_MOD) | Cubierto — **es el requerimiento asignado del curso; ciclo completo obligatorio** |
| **Brute-force de solicitudes** (R4) | Solicitudes/s por origen sobre el umbral | RATE_LIMIT o BLOCK del origen | Monitor · Detection Engine · Policy Engine | Cubierto (misma cadena que el flood) |
| **Ataques desde el exterior** (R5 · CU-08) | — sin punto de detección perimetral definido | — (la vía hacia la red SDN existe: R5.7) | — | **Hueco** — se cierra en la Fase F (evaluación IDS/IPS de R5.2 y definición del perímetro) |

## 2. Amenazas y fuentes

| Amenaza | Cómo la trata el diseño | Veredicto |
|---|---|---|
| **Atacante externo** | Objeto de R5 (hueco declarado); si atraviesa el perímetro, cae en la cadena R3/R4 como cualquier origen | Parcial (depende del perímetro) |
| **Atacante interno** | El perfil BASE restringe (lista cerrada) y la detección vigila R3/R4 sobre cualquier origen, autenticado o no | Cubierto |
| **Nodo comprometido** | Su tráfico es objeto de R3/R4 aunque el usuario tenga credenciales válidas; la respuesta lo aísla o bloquea sin depender de la identidad de la persona | Cubierto (D-11.1 §2) |

## 3. Estados que habilitan ataques

- **IdP institucional comprometido:** el IAM consume su veredicto, pero los operadores se verifican contra el repositorio propio y las mitigaciones activas no dependen del IdP: el compromiso degrada la autenticación de la comunidad, no la operación de la defensa (D-11.1 §3).
- **Manipulación de DNS:** tratada como caso de origen inconsistente (R3.3) y como vector de redirección.
- **Desincronización de tiempo (NTP):** no es ataque; deteriora la correlación de eventos y la auditoría (RNF-09) — su tratamiento (fuente de tiempo común) es insumo de la Fase F.

## 4. Cierre

Todos los ataques tienen detección y respuesta asignadas salvo el bloque perimetral, que es el mismo hueco ya registrado en `01_casos_de_uso_a_componentes.md` (CU-08) y `02_requisitos_a_componentes.md` (R5): la arquitectura interna está lista para recibir eventos perimetrales (R5.7), falta la fuente. Los umbrales concretos de cada detección se fijan con mediciones del prototipo.
