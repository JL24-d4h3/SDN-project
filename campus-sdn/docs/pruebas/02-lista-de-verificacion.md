# Lista de verificación — permisos y capacidades

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** Implementación — Pruebas sobre el slice del laboratorio
**Estado:** Vivo — se marca conforme se verifica

---

La etapa 0 definió 37 permisos (P01–P36, con P22 partido en operar y configurar) sobre la política [`policy/permissions.yaml`](../../policy/permissions.yaml). Esta lista los recorre uno por uno y marca el estado **verificado**, no el prometido:

- ✅ **Verificado en el slice**: se ejecutó sobre el slice real y se observó el resultado esperado.
- 🟡 **Implementado**: el código existe y pasa sus pruebas locales; falta la demostración en el slice.
- ⬜ **Pendiente o parcial**: falta código, o el flujo completo no está.

| ID | Permiso | Estado | Evidencia / qué falta |
|---|---|---|---|
| P01 | Authenticate | ✅ | **Reino real en el slice**: comunidad por RADIUS→LDAP (USR-0006 aceptado, contraseña mala rechazada), operadores en dos pasos (credenciales → TOTP), invitados con autoregistro TTL |
| P02 | Access the network | ✅ | Regla de sesión en sw2 (ida con alcance + vuelta), escalera observada, una sola sesión por dispositivo |
| P03 | Access service | 🟡 | APIs de servicios existen; SSO por servicio solo en Consola y Políticas |
| P04 | Read resource | 🟡 | Pruebas locales de los endpoints de lectura |
| P05 | Execute operation | 🟡 | Pruebas locales de los endpoints de operación |
| P06 | Read network status | 🟡 | I2 `/topology`, `/counters`; sin demo en el slice |
| P07 | Read traffic | 🟡 | Monitor y `/counters`; sin demo en el slice |
| P08 | Read events and logs | 🟡 | Auditoría `/events`; sin demo en el slice |
| P09 | Read alerts | 🟡 | La decisión está probada (403/200); falta la demo en vivo de la Consola |
| P10 | Analyze incident | 🟡 | Incidentes implementado; sin demo en el slice |
| P11 | Manage alert | 🟡 | Incidentes implementado; sin demo en el slice |
| P12 | Execute mitigation | 🟡 | Adaptador + Políticas (escalera 1000); sin demo en el slice |
| P13 | Isolate node | 🟡 | Ídem (ISOLATE_DEVICE); sin demo en el slice |
| P14 | Manage local accounts | 🟡 | IAM `/operators` real (bcrypt + TOTP, URI una vez) y listado privilegiado verificado en el slice; el alta por consola con rol aún no |
| P15 | Assign role | 🟡 | La asignación vive en la política; el motor en `bd_politicas` falta |
| P16 | Manage permissions | 🟡 | YAML + validador + generadores; el motor en `bd_politicas` falta |
| P17 | Manage access policies | 🟡 | Políticas `/profiles`; sin demo en el slice |
| P18 | Manage security policies | 🟡 | Políticas (mitigaciones); sin demo en el slice |
| P19 | Manage network rules | 🟡 | I2 `/orders` ejecuta; el permiso administrativo aún sin SSO en esa ruta |
| P20 | Manage segmentation | ⬜ | VLANs solo en Ansible; sin API |
| P21 | Manage network devices | 🟡 | Adaptador `/services` (inventario); sin demo en el slice |
| P22-OP | Operate the SDN controller | 🟡 | El adaptador opera ONOS por I2; sin demo en el slice |
| P22-CFG | Configure the SDN controller | ⬜ | Sin implementación |
| P23 | Manage security mechanisms | 🟡 | Políticas; sin demo en el slice |
| P24 | Manage administrators | 🟡 | Mismo camino que P14; sin demo en el slice |
| P25 | Audit operations | 🟡 | Auditoría; sin demo en el slice |
| P26 | Manage global configuration | ⬜ | Sin implementación |
| P27 | Manage recovery | ⬜ | Sin implementación |
| P28 | Request elevation | 🟡 | El Portal publica `ElevationRequested`; la decisión completa falta |
| P29 | Approve elevation | 🟡 | Políticas `/elevations`; sin demo en el slice |
| P30 | Register privileged device | 🟡 | IAM `/devices/{mac}/reprovision-totp`; el flujo completo falta |
| P31 | Manage sessions | 🟡 | IAM consulta y revoca sesiones; listado privilegiado verificado en el slice (sin SSO aún en esas rutas) |
| P32 | Approve high-impact action | 🟡 | Incidentes (aprobación); sin demo en el slice |
| P33 | Adjust detection thresholds | 🟡 | Políticas `/thresholds`; sin demo en el slice |
| P34 | Manage keys and certificates | ⬜ | Sin implementación |
| P35 | Request device registration | 🟡 | Registry; sin demo en el slice |
| P36 | Manage audit retention and export | ⬜ | Sin implementación |

## Brechas detectadas en la prueba (para cerrar antes de marcar ✅)

1. ~~**Una sola sesión por dispositivo.**~~ **Cerrada (2026-11-03):** un login nuevo con el mismo dispositivo cierra la sesión previa (`reason: replaced`, sus reglas se retiran) antes de emitir la nueva. Verificado en el slice: la primera sesión responde 404 y solo quedan las reglas de la segunda.
2. **Estado en memoria.** Sesiones, operadores e invitados del IAM y el registro de órdenes del adaptador se pierden al recrear el contenedor; los flujos instalados quedan huérfanos. La persistencia llega con `bd_politicas` (paso 5); mientras, cada prueba empieza con la limpieza del manual del perfil base.
3. **Los flujos hablan, pero no dicen quién.** Las reglas en el switch no llevan la identidad a la vista (la cookie la reemplaza ONOS). La trazabilidad (qué regla corresponde a qué sesión) vive en el registro de órdenes del adaptador y en el IAM; los manuales de prueba la consultan desde ahí, no desde `dump-flows`.
4. **El esqueleto por dispositivo falta.** El perfil base instalado es por **destino** (cubre a cualquier dispositivo que aparezca, verificado con el 10.0.0.9 aprendido). Las entradas por dispositivo del LLD — par MAC/IP aprendido (120) y anti-spoofing (110) — aún no se instalan: llegan con el motor de política. Hasta entonces, un dispositivo nuevo queda bajo el esqueleto por destino, que ya lo protege, pero sin el par MAC/IP individual.
5. **DHCP y DNS sin servidores en este slice.** Las entradas 10 actúan (el contador de DNS sube con una consulta real), pero no hay servidores en el plano de datos que respondan: llegan con el despliegue completo. La verificación de asignación real de DHCP (dirección entregada al host) espera a ese slice.
6. **La VNRT filtra MAC nuevas.** El descubrimiento de un dispositivo con MAC nueva no se puede demostrar en este slice (la red virtual no deja entrar tramas de MACs desconocidas): la demostración de adaptividad quedó con una IP nueva sobre una MAC conocida. Con el slice real, el `arping` de un equipo nuevo debe aparecer en `/hosts` igual.
