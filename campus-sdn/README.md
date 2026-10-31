# campus-sdn

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** Implementación
**Estado:** Esqueleto del repositorio

---

Repositorio de construcción de la solución: contratos, servicios, política ejecutable, despliegue automatizado y pruebas. La arquitectura y los planes viven en el corpus ([`../docs/`](../docs/), [`../implementation/`](../implementation/)); este repositorio los convierte en código reproducible.

## 1. Entrada

| Objetivo | Acción |
|---|---|
| `make help` | Objetivos disponibles |
| `make images-pull` | Descarga las imágenes y fija sus digests |
| `make images-verify` | Compara los digests locales con el lock |
| `make images-save` | Empaqueta los bundles para el slice |
| `make images-load IMAGES=onos` | Carga bundles en la VM local |
| `make ping` | Conectividad con todas las VMs |
| `make deploy TAGS=platform` | Despliega `site.yml`, completo o por etiqueta |
| `make up` / `make down` | Levanta o detiene los servicios |
| `make status` | Salud de contenedores y servicios |
| `make test` | Pruebas de contrato e integración |
| `make verify` | Verificación completa |

## 2. Estructura

```text
campus-sdn/
├── CLAUDE.md            # reglas de implementación y documentación
├── contracts/          # esquemas de eventos, OpenAPI y política
├── services/           # los diez servicios + common/
├── policy/             # permissions.yaml (etapa 0), profiles.yaml, tools/
├── deploy/
│   ├── compose/        # un Compose por VM de plataforma y ONOS
│   ├── images/         # images.lock y scripts pull/verify/save/load
│   ├── ansible/        # inventario, site.yml y roles por frente
│   └── env/            # plantilla de entorno
├── tests/              # contract/, integration/, e2e/
└── docs/               # 01-mapa.md, 02-estado.md, 03-formatos.md, adr/, runbooks/
```

## 3. Reglas

- Sin secretos en el repositorio: el `.env` real, el inventario `slice.yml` y el vault están ignorados por git; las credenciales viajan por Ansible Vault o variables de entorno.
- Los bundles de imágenes (`deploy/images/bundles/`) no se versionan: git guarda el lock, no los binarios.
- `policy/permissions.yaml` es la copia operativa de la etapa 0; la fuente histórica sigue en [`../implementation/policy/`](../implementation/policy/). Los cambios se versionan en el YAML.
- Toda tarea se ejecuta por `make`; no hay pasos manuales fuera del Makefile y de Ansible.

## 4. Documentos

| Documento | Uso |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Reglas de implementación y documentación |
| [`docs/01-mapa.md`](docs/01-mapa.md) | Estructura del repositorio y los hilos que conectan sus piezas |
| [`docs/02-estado.md`](docs/02-estado.md) | Avances y pendientes del proyecto |
| [`docs/03-formatos.md`](docs/03-formatos.md) | Tutorial: leer YAML, JSON, OpenAPI y Compose |
| [`../implementation/09_plan_de_construccion.md`](../implementation/09_plan_de_construccion.md) | Plan de construcción del repositorio |
| [`../implementation/05_plan_de_implementacion.md`](../implementation/05_plan_de_implementacion.md) | Diseño del despliegue |
| [`../implementation/06_plan_de_trabajo_etapa_2.md`](../implementation/06_plan_de_trabajo_etapa_2.md) | Paquetes de trabajo de despliegue |
| [`../implementation/07_plan_de_trabajo_etapa_3.md`](../implementation/07_plan_de_trabajo_etapa_3.md) | Paquetes de trabajo de ejecución y medición |
