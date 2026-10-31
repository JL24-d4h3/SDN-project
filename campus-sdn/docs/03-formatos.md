# Cómo leer los archivos del repositorio

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** Implementación
**Estado:** Vivo — se amplía cuando un formato nuevo entra al repositorio

---

## 1. Propósito

Explicar, para quien nunca los vio, los formatos que usa el repositorio: YAML, JSON, OpenAPI y Compose. Todos los ejemplos salen de nuestros propios archivos, no de manuales. No sustituye la lectura del código: da lo mínimo para que esa lectura sea posible. La estructura general está en [`mapa.md`](mapa.md).

## 2. Por qué dos formatos parecidos

- **YAML** es para lo que editan personas: la política, el inventario, los Compose y los playbooks. Permite comentarios y se lee casi como una lista.
- **JSON** es para lo que validan máquinas: los esquemas y el lock de imágenes. Sin comentarios ni atajos: toda herramienta lo entiende igual.

La regla del repositorio: lo que una persona corrige a mano es YAML; lo que una máquina valida byte a byte es JSON.

## 3. YAML en un minuto

Un YAML es pares `clave: valor` anidados por indentación (espacios, nunca tabuladores):

```yaml
roles:
  academico:
    name: Académico
    level: 0
    mfa_required: false
```

- `roles` contiene a `academico`, que contiene `name`, `level` y `mfa_required`.
- Una lista se escribe con guion:

```yaml
scope: [portal, dhcp, dns]        # lista en una línea
conditions:                       # o en varias
  - C1
  - C9
```

- `#` inicia un comentario; YAML lo ignora.
- Dos trampas que este proyecto ya pisó, para no repetirlas:

| Trampa | Qué pasó | Cómo se evita |
|---|---|---|
| `valid_from: 2026-10-28` sin comillas | YAML lo convirtió en un objeto fecha, y el esquema esperaba texto | `valid_from: "2026-10-28"` |
| `description: para QUARANTINE: aprobación` | el segundo `:` rompió el parseo | citar todo: `description: "para QUARANTINE: aprobación"` |

Regla práctica: si un valor lleva dos puntos, comillas, o parece fecha, se escribe entre comillas.

## 4. JSON en un minuto

Mismo esqueleto, otra sintaxis: llaves, comillas dobles obligatorias en nombres y textos, comas entre elementos, sin comentarios:

```json
{
  "name": "onos",
  "ref": "onosproject/onos:2.7.0",
  "digest": "sha256:bc84…",
  "used_by": ["onos-1", "onos-2", "onos-3"]
}
```

Se usa en el lock y en los esquemas porque cualquier validador lo procesa sin ambigüedad.

## 5. Cómo leer un esquema JSON

Un esquema describe la **forma** que debe tener un dato. Dos claves hacen casi todo el trabajo:

- `required`: qué campos son obligatorios.
- `additionalProperties: false`: nada fuera de lo declarado.

```json
{
  "type": "object",
  "required": ["mac", "ip", "switch", "puerto", "timestamp"],
  "additionalProperties": false,
  "properties": {
    "mac":  {"type": "string"},
    "timestamp": {"type": "string", "format": "date-time"}
  }
}
```

Leído en voz alta: «un `DeviceConnected` es un objeto que debe traer mac, ip, switch, puerto y timestamp; mac es texto y timestamp es fecha-hora; cualquier otro campo se rechaza». El validador ([`policy/tools/validate.py`](../policy/tools/validate.py) para la política; las pruebas de contrato para los eventos) aplica esta pregunta a cada dato.

## 6. Cómo leer la política, bloque a bloque

[`policy/permissions.yaml`](../policy/permissions.yaml) se lee en este orden, de lo general a lo particular:

| Bloque | Pregunta que responde |
|---|---|
| `defaults` | Si nada dice otra cosa, ¿qué se hace? (denegar, auditar, exigir sesión) |
| `roles` | ¿Quiénes existen? (académico, TI, admin de red, superadmin) |
| `profiles` | ¿Qué perfiles de red existen? (BASE, ACADÉMICO, OPERADOR_*, ELEVACIÓN) |
| `resources` | ¿Sobre qué tipos de recurso se actúa? |
| `conditions` | ¿Qué condiciones C1–C11 matizan una decisión? |
| `permissions` | ¿Qué acciones P01–P36 existen? |
| `assignments` | ¿Qué rol tiene qué permiso, sobre qué recursos, con qué condiciones y obligaciones? |
| `rules` | ¿Qué prohibiciones valen para todos, pase lo que pase? (separación de funciones, break-glass…) |
| `delegations` | ¿Qué delegó el superadmin y hasta cuándo? |
| `obligations` | ¿Qué debe ocurrir además al ejecutar? (auditar, notificar, justificar…) |
| `priorities` | ¿En qué orden se resuelven las reglas del switch? |

Una asignación, desglosada:

```yaml
- {id: A001, role: academico, permission: P03, effect: permit,
   resources: [servicio_academico, servicio_publico],
   conditions: [C9], obligations: [auditar]}
```

Leída en voz alta: «A001 permite al académico el permiso P03 (acceder a servicio) sobre servicios académicos y públicos, siempre que se cumpla C9 (recurso autorizado), y queda auditado». La matriz rol × permiso que se muestra en los documentos es exactamente este bloque, generado por [`generate_matrix.py`](../policy/tools/generate_matrix.py).

## 7. Cómo leer un Compose

Un Compose describe los contenedores de una VM y lo que necesitan:

```yaml
services:
  postgres:
    image: postgres:16
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "127.0.0.1:5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER:-postgres} -d bd_politicas"]
volumes:
  postgres_data:
```

- `services`: los contenedores; aquí, uno.
- `image`: qué imagen se usa (el digest ya quedó garantizado por el lock).
- `volumes`: qué datos sobreviven si el contenedor se recrea.
- `ports`: `puerto_del_host:puerto_del_contenedor`; el `127.0.0.1` limita el acceso a la propia VM.
- `healthcheck`: cómo Compose decide si el contenedor está sano; sin él, `up --wait` no esperaría nada.

`${POSTGRES_PASSWORD:?definir…}` significa: el valor viene del archivo `.env` y, si falta, Compose se niega a arrancar con ese mensaje — así un secreto jamás entra al repositorio.

## 8. Cómo leer un playbook y un rol

Un playbook dice **qué** se hace y **dónde**; un rol dice **cómo**:

```yaml
- name: Plataforma por VM
  hosts: platform
  roles:
    - platform
```

- `hosts: platform` selecciona las VMs del grupo `platform` del inventario (S1–S4).
- El rol `platform` vive en [`deploy/ansible/roles/platform/tasks/main.yml`](../deploy/ansible/roles/platform/tasks/main.yml): una lista de tareas, cada una con `tags` para ejecutarla sola.
- `when:` salta una tarea si la condición no se cumple (por ejemplo, si la VM no declara `compose_file`).
- La repetición es segura: cada tarea es idempotente, y repetir el playbook no rompe nada.

## 9. Cómo leer un OpenAPI

Un archivo OpenAPI describe una API completa: qué rutas existen, qué parámetros aceptan, qué responden y qué errores devuelven. [`i2-controller.openapi.yaml`](../contracts/api/i2-controller.openapi.yaml) dice, por ejemplo, que `POST /ordenes` acepta tres órdenes (`APLICAR_PERFIL`, `APLICAR_MITIGACION`, `RETIRAR`) y responde `201` al aplicarse o `403` si el solicitante no es competente. Sirve para dos cosas: documentar lo que un servicio debe cumplir y generar clientes de prueba.

## 10. Después de esto

El siguiente paso es [`01-mapa.md`](01-mapa.md) §6 (los hilos) y luego [`02-estado.md`](02-estado.md) (qué está hecho y qué falta). Con eso, cualquier carpeta del árbol se entiende en su contexto.
