# Reglas del repositorio campus-sdn

Reglas de implementación y documentación. Todo agente y todo autor debe leerlas antes de crear o modificar algo dentro de este directorio; un cambio que las viole se corrige, no se discute.

## Idioma

- **Carpetas, archivos e identificadores de código: inglés.** Archivos de configuración en kebab-case (`s3-response.yml`, `i2-controller.openapi.yaml`); scripts y paquetes Python en snake_case (`validate.py`, `generate_matrix.py`, `sensor_adapter/`).
- **Los campos, rutas y valores de los contratos también van en inglés** (`event_id`, `sender`, `/orders`, `APPLY_PROFILE`); la correspondencia con los nombres en español del LLD se documenta en el README de cada carpeta de `contracts/`.
- **Documentación, comentarios y mensajes de salida: español.**
- **Los documentos de `docs/` se nombran en español, con prefijo numérico según el orden de lectura** (`01-mapa.md`, `02-estado.md`, `03-formatos.md`); un documento nuevo toma el siguiente número.
- **Los valores y las etiquetas `name` de `policy/permissions.yaml` van en inglés y sin tildes** (roles `academic`, `network_admin`; plano `pre_session`; `ACADEMIC`, `ELEVATION`). El corpus conserva el modelo en español; la correspondencia completa está en [`policy/README.md`](policy/README.md) y los cambios se reflejan en ambas copias, versionados.
- Fuera de `docs/`, no se crean archivos ni carpetas con nombres en español.

## Documentación

- Un asunto por archivo; de lo general a lo particular; sin secciones de «qué cambió» en documentos limpios; sin listar tecnologías descartadas.
- El corpus (fuera de `campus-sdn/`) es la fuente del diseño: aquí se enlaza, no se copia.
- Al cerrar un paso de construcción, actualizar `docs/02-estado.md`: avance con fecha en §1 y el pendiente resuelto fuera de §2.

## Operación

- Toda tarea se ejecuta por `make`; no hay pasos manuales fuera del Makefile y de Ansible.
- Sin secretos en el repositorio: `.env`, el inventario `slice.yml` y el vault están ignorados por git; las credenciales viajan por Ansible Vault o variables de entorno.
- `deploy/images/bundles/` no se versiona: git guarda el lock, no los binarios.
- `policy/permissions.yaml` es la copia operativa de la etapa 0; su gemelo histórico está en `../implementation/policy/`. Se cambian juntos y versionados.
- Los contratos se congelan antes de escribir servicios: contrato → prueba de contrato → servicio.

## Referencias

- Plan de construcción: [`../implementation/09_plan_de_construccion.md`](../implementation/09_plan_de_construccion.md)
- Mapa, estado y formatos: [`docs/01-mapa.md`](docs/01-mapa.md), [`docs/02-estado.md`](docs/02-estado.md), [`docs/03-formatos.md`](docs/03-formatos.md)
