# Autenticación y autorización — manual de verificación

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** Implementación — Pruebas sobre el slice del laboratorio
**Estado:** Borrador formal para revisión

---

Autenticación **real**: las credenciales se verifican contra los registros de cada reino — la comunidad contra el IdP (FreeRADIUS → OpenLDAP, protocolo RADIUS real, F-03 §2), los operadores contra el repositorio propio con TOTP obligatorio (F-03 §3) y los invitados contra el registro efímero con TTL. Nada de stub. Este manual dice qué está desplegado, con qué credenciales se prueba, qué respuesta se espera en cada paso y cómo se revisa quién está registrado.

## 1. Los tres reinos desplegados

| Reino | Dónde viven las cuentas | Cómo entran | Ejemplo |
|---|---|---|---|
| Comunidad universitaria | OpenLDAP (IdP simulado), verificado por FreeRADIUS | **Nunca se registran**: solo inician sesión; las cuentas las crea el directorio | USR-0006 / user_0006 |
| Operadores (TI, Admin, SA) | Repositorio del IAM (bcrypt + TOTP) | **No se autoregistran**: los crea la cadena SA→Admin→TI (P14/P24) | OPRT-0001 / operator_0001 + TOTP |
| Invitados | Registro efímero del IAM | **Sí se autoregistran**: cuenta con TTL de 24 h que se borra sola | INV-0003 / inv_0003 |

Infraestructura (todo en el controller, red de gestión):

- `mini-openldap`: directorio `dc=campus,dc=local`; la semilla [`deploy/ldap/seed-users.ldif`](../../deploy/ldap/seed-users.ldif) crea USR-0001…USR-0006 con `user_000X`. Se siembra **una vez** con `ldapadd` (la imagen rompe con bind-mounts de bootstrap):

  ```bash
  sudo docker cp /tmp/campus/ldap/seed-users.ldif mini-openldap:/tmp/seed.ldif
  sudo docker exec mini-openldap ldapadd -x -H ldap://127.0.0.1 \
    -D "cn=admin,dc=campus,dc=local" -w "$(grep LDAP_ADMIN_PASSWORD /tmp/campus/.env | cut -d= -f2)" \
    -f /tmp/seed.ldif
  ```

  Los `<PLACEHOLDER>` de este manual se reemplazan por los valores del `.env` del controller (`/tmp/campus/.env`): `LDAP_ADMIN_PASSWORD`, `LDAP_READONLY_PASSWORD`, `RADIUS_SECRET` — los secretos no van en documentos ni en el repo.

- `mini-freeradius`: IdP por protocolo real. Sus archivos (`clients.conf` y `mods-ldap`) se generan desde las plantillas de [`deploy/radius/`](../../deploy/radius/) con los secretos del `.env` (los generados están ignorados por git). Dos hallazgos del slice quedaron resueltos ahí: la imagen **no genera clientes por entorno** (sin `clients.conf`, el IAM no es cliente y FreeRADIUS descarta en silencio) y FreeRADIUS 3.2.10 **exige `Message-Authenticator`** (el cliente pyrad lo añade).
- El IAM: `STUB_VERIFY=0`, `RADIUS_HOST=freeradius`, `RADIUS_SECRET` del `.env`.

Verificación local del IdP (dentro del contenedor):

```bash
sudo docker exec mini-freeradius sh -c \
  'echo "User-Name=USR-0006,User-Password=user_0006" | radclient 127.0.0.1 auth testing123'
# Received Access-Accept
```

## 2. Comunidad: solo inicia sesión

```bash
# credenciales reales → sesión
curl -s -X POST http://192.168.0.10:8001/verify -H 'Content-Type: application/json' \
  -d '{"population":"university","username":"USR-0006","password":"user_0006"}'
# → {"session":"…","profile_or_role":"academic","device":null,"network":{"status":"skipped",…}}

# contraseña mala → rechazo (401), igual que un usuario inexistente
```

`device: null` aquí es la limitación del slice actual: el login por la red de gestión no trae asociación del plano de datos (el portal la resuelve cuando la conexión llega en banda; §6 lo prueba con el dispositivo explícito). Desde cada host (h1–h4) el mismo comando apuntando a `192.168.0.10` da el mismo resultado real.

## 3. Operadores: credenciales primero, TOTP después

El TOTP **solo se muestra a quien ya pasó las credenciales** — jamás antes (corrección pedida en la revisión):

1. **Aprovisionar** (una vez; la URI TOTP se muestra una sola vez, F-03 §3.1):

   ```bash
   curl -s -X POST http://192.168.0.10:8001/operators -H 'Content-Type: application/json' \
     -d '{"username":"OPRT-0001","password":"operator_0001","role":"network_admin"}'
   # → {"status":"registered","provisioning_uri":"otpauth://totp/…secret=…"}
   ```

   El secreto de la URI se carga en la app autenticadora. Para pruebas por API, el código se genera con el secreto:

   ```bash
   sudo docker exec mini-iam python3 -c \
     'import pyotp; print(pyotp.TOTP("<secreto>").now())'
   ```

2. **Paso 1 — solo credenciales**: la respuesta pide el segundo factor; una contraseña mala recibe 401 sin ninguna pista:

   ```bash
   curl -s -X POST …/verify -d '{"population":"operations","username":"OPRT-0001","password":"operator_0001"}'
   # → {"totp_required":true,"username":"OPRT-0001","profile_or_role":"network_admin"}
   ```

3. **Paso 2 — credenciales + TOTP** → sesión de operador.

En el formulario del portal, el campo TOTP aparece recién cuando la respuesta declara `totp_required` (el JS lo revela con el mensaje «Credenciales reconocidas»); un académico jamás lo ve.

## 4. Invitados: se autoregistran

```bash
curl -s -X POST http://192.168.0.10:8001/guest-register -H 'Content-Type: application/json' \
  -d '{"username":"INV-0003","password":"inv_0003"}'
# → {"status":"registered","expires_at":…}   (TTL 24 h; la cuenta se borra sola)
# login normal con population=guest → sesión con perfil guest
```

## 5. Revisar quién está registrado (sesión de operador)

Con el token de la sesión del operador (`X-Session` o `?session=`):

| Qué | Ruta | Qué devuelve |
|---|---|---|
| Operadores | `GET /operators` | username + rol (sin hashes ni secretos) |
| Invitados | `GET /guests` | username + vencimiento |
| Sesiones vigentes | `GET /sessions` | identidad, perfil, dispositivo, vigencia |
| Comunidad | `ldapsearch` contra mini-openldap | las cuentas del directorio (no viven en la plataforma) |
| Dispositivos asociados | `GET http://192.168.0.10:8002/devices` | MAC, dueño, rol (Registry) |

Sin sesión de operador, estas rutas responden 401/403 — la revisión es privilegiada (P14/P31), no pública.

### 5.1 Consultar el directorio (comunidad)

```bash
# quién existe (las contraseñas se ven hasheadas, nunca en claro)
sudo docker exec mini-openldap ldapsearch -x -H ldap://127.0.0.1 \
  -b "ou=people,dc=campus,dc=local" \
  -D "cn=admin,dc=campus,dc=local" -w "$(grep LDAP_ADMIN_PASSWORD /tmp/campus/.env | cut -d= -f2)" \
  "(objectClass=inetOrgPerson)" uid cn userPassword

# un solo usuario
sudo docker exec mini-openldap ldapsearch -x -H ldap://127.0.0.1 \
  -b "ou=people,dc=campus,dc=local" -D "cn=admin,dc=campus,dc=local" \
  -w "$(grep LDAP_ADMIN_PASSWORD /tmp/campus/.env | cut -d= -f2)" "(uid=USR-0006)"
```

### 5.2 Ver al IdP en acción (RADIUS)

Cada intento de la comunidad queda en el `linelog` de FreeRADIUS — aceptados y rechazados:

```bash
# tras un login correcto y uno con contraseña mala:
sudo docker exec mini-freeradius tail -4 /var/log/freeradius/linelog
# Accepted user: USR-0006
# Rejected user: USR-0006
```

El accounting de la sesión queda en `radacct/` dentro del contenedor (los `Start` del IAM). Y sin pasar por la plataforma, el IdP se prueba solo:

```bash
sudo docker exec mini-freeradius sh -c \
  'echo "User-Name=USR-0006,User-Password=user_0006" | radclient 127.0.0.1 auth testing123'
# Received Access-Accept   (con la contraseña mala: Access-Reject)
```

## 6. La sesión, el dispositivo y los flujos

La sesión nace **ligada al dispositivo** (F-03 §4): el login con `device` instala la escalera en el switch del anfitrión y registra la asociación en el Registry:

```bash
curl -s -X POST …/verify -d '{"population":"university","username":"USR-0001",
  "password":"user_0001","device":"FA:16:3E:88:05:79"}'
# → {"session":"…","profile_or_role":"academic","device":"FA:16:3E:88:05:79",
#    "network":{"status":"applied","rules":["of:00001a749039894a:200:…","…"]}}
```

- **Reglas en sw2** (el switch de h1): `dump-flows sw2 | grep priority=200` — ida con el alcance del académico (`nw_dst=10.0.0.0/24`) y vuelta.
- **Una sola sesión por dispositivo**: un segundo login con la misma MAC cierra la sesión anterior (`reason: replaced`, sus reglas se retiran) antes de emitir la nueva — la red admite al usuario, no duplica su presencia. Verificado: la primera sesión responde 404.
- **El Registry** queda con la asociación (`owner`, `role`) — es la observabilidad de «quién entró desde qué dispositivo», no concede confianza por sí misma.
- **Cierre y expiración**: `POST /logout` retira las reglas por la orden que las instaló (selectores exactos; ONOS reemplaza las cookies, verificado en el slice). Si la sesión expira (tope o idle), las reglas mueren solas en el switch (`hard_timeout`/`idle_timeout`) y el barrido del IAM cierra la sesión con `SessionClosed` (`reason: hard-timeout`).
- En este slice el login por gestión llega sin dispositivo (limitación documentada en el [inventario](00-inventario-del-slice-actual.md) §7); con el slice real, el portal resuelve la MAC en banda y el `device` aparece solo.

## 7. Criterios

| Observación | Veredicto |
|---|---|
| USR-0006 aceptado; contraseña mala y usuario inexistente rechazados | comunidad real ✓ |
| `totp_required` solo tras credenciales correctas; TOTP malo rechazado | operadores en dos pasos ✓ |
| INV-0003 se registra solo y entra con TTL | invitados ✓ |
| Los listados exigen sesión de operador y ocultan secretos | revisión privilegiada ✓ |
| Dos logins con la misma MAC dejan una sola sesión viva | una sesión por dispositivo ✓ |
| Login con dispositivo instala 2 reglas en el switch correcto; logout las retira | escalera + retiro ✓ |
