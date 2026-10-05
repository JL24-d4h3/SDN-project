# Historial de dispositivo

**Proyecto:** Solución de seguridad para una red de campus académico
**Serie:** Componentes del sistema — 5 de 6
**Estado:** Borrador formal para revisión

---

El **registro de observación** de dispositivos: qué se sabe de cada dispositivo que se conecta —esté o no registrado— y cómo se investiga un incidente. Su contraparte (el registro de dispositivos privilegiados, de pre-provisión) está en [`05_componentes_principales.md`](../fases/D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/05_componentes_principales.md) §7; el modelo de identidades, en [04](04_identidades_y_poblaciones.md).

## 1. Por qué existe

- Los operadores están **pre-registrados** (se sabe qué dispositivo es de quién antes de conectarse); los académicos **no se registran** (por diseño, P7/RP-13) — pero eso no puede significar "no saber nada de ellos".
- La asimetría se resuelve con dos registros de naturaleza distinta: **pre-provisión** para operadores; **observación** para todos.
- Los casos que lo motivan: un académico autenticado comete un ataque → hay que poder recorrer MAC → persona. Un dispositivo pre-login ataca → al menos MAC → puerto → momento.

## 2. Qué se observa y de dónde sale

| Fuente | Qué aporta | Forma |
|---|---|---|
| Controlador | ubicación en vivo: MAC ↔ IP ↔ switch ↔ puerto | consulta (I2) |
| Controlador → broker | primera aparición de cada dispositivo (`DeviceConnected`), movimiento (`MAC_Moved`) | eventos → Auditoría |
| IAM/AAA | la sesión: identidad ↔ MAC/IP ↔ instante; accounting | eventos + registros |
| Incidentes | el hecho: qué origen atacó | `IncidentRepository` |

Todo dispositivo, **incluso antes de cualquier login**, deja `DeviceConnected` (MAC, IP, puerto, instante) y queda en Auditoría.

## 3. El recorrido de una investigación

```text
incidente INC-xxxx  (origen: MAC A1, IP 10.0.1.25, puerto S1:p1, hora T)
     │
     ▼
historial de la MAC A1 (Auditoría):
     DeviceConnected   S1:p1 · T−40 min
     SessionOpened     persona Y · rol académico · T−39 min
     → PERSONA: Y
     │
     ▼
ubicación actual (controlador): A1 sigue en S1:p1
     → contención: bloquear o poner en cuarentena el puerto/dispositivo
```

- **Con sesión:** la atribución llega a la persona — el puente MAC→persona es la sesión, y es uno de los motivos de autenticar al académico.
- **Pre-login (nunca se autenticó):** MAC + puerto + hora. No hay persona que encontrar — nunca dio identidad. El puerto físico es la pista; la contención es sobre ese puerto. Es un límite inherente, no un defecto.

## 4. La confiabilidad de MAC e IP

- **La MAC es autodeclarada** (falsificable) y **la IP es asignada** (cambia). Ninguna de las dos es prueba de identidad.
- En el diseño eso ya está asumido: la MAC es **atributo, no credencial** (P7); ambas son **localizadores y claves de correlación**, no identidades.
- La debilidad también es señal: `MAC_Moved` detecta la incoherencia (misma MAC en dos ubicaciones) y desencadena la respuesta.

```text
Fuerza como identidad, de mayor a menor:
  1. credenciales (sesión)            ← lo único que no se falsifica sin robar
  2. características del dispositivo  ← continuidad, también imitable
  3. MAC / IP                         ← localizadores
```

## 5. Características del dispositivo (en análisis)

Para reforzar la continuidad cuando la MAC rota, se pueden **observar características** del dispositivo:

| Característica | De dónde se obtiene | Qué aporta |
|---|---|---|
| OUI de la MAC | la propia MAC | fabricante (aproximación de "modelo") |
| Huella DHCP | opción 55 del cliente (si se captura) | sistema operativo aproximado |
| User-Agent | login en el portal | navegador/SO observados |
| Puerto y tiempos | controlador | ubicación y periodicidad |

- **Límite honesto:** también son falsificables (firmas de SO imitables); **no son identidad**. Aportan continuidad ("probablemente el mismo equipo"), no certeza.
- **Estado: en análisis.** Lo mínimo recomendado es **registrar lo que ya se observa naturalmente** (OUI, user-agent, puerto, tiempos) como parte del historial; el perfilado estilo NAC (producto dedicado) sería una extensión posterior.

## 6. Dónde vive y cuánto dura

- **Sin servicio nuevo (P4):** el historial es una **vista de investigación** construida de los eventos de Auditoría + las sesiones del IAM, consultable desde la consola; la ubicación en vivo la responde el controlador.
- **Retención:** cuestión abierta (doc [11 §8](../fases/D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/11_seguridad_arquitectonica.md)) que ahora tiene un motivo concreto — **forense**: debe cubrir una ventana de investigación razonable (p. ej., el semestre). Cifra exacta: por definir.

## 7. La simetría de los dos registros

| | Registro de dispositivos privilegiados | Historial de dispositivo |
|---|---|---|
| Naturaleza | pre-provisión (aprobación) | observación (automática) |
| Población | operadores | todos, incluidos académicos |
| Quién lo llena | Admin/SA (P30) | el sistema (eventos) |
| Para qué | habilitar elevación + auditoría de altas | investigar incidentes |

## 8. Cuestiones abiertas

- **Características a observar** (§5): decisión pendiente.
- **Retención** (§6): cifra.
- **Almacenamiento propio vs. vista sobre auditoría:** evaluar con el volumen del prototipo si basta la auditoría o conviene materializar el historial.
