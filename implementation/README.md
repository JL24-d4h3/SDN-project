# Mapa de las etapas de implementación

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** Implementación
**Estado:** Borrador formal para revisión

---

La implementación se organiza en cuatro etapas secuenciales. Cada una tiene un criterio de salida verificable; no se abre la siguiente sin cerrar el anterior.

| Etapa | Objetivo | Documentos | Estado | Criterio de salida |
|---|---|---|---|---|
| **0 — Permisos** | Modelo de autorización ejecutable: catálogo, matriz, política y pruebas | [00](00_cierre_etapa_0_permisos.md), [01](01_modelo_de_contexto_y_estado.md), [02](02_matriz_rol_permiso.md), [03](03_plan_de_pruebas_permisos.md), [policy](policy/) | **Cerrada** (2026-10-28) | Matriz 37 × 4, YAML validado y generador en verde |
| **1 — Verificación del slice** | Confirmar capacidades del switch, dimensionamiento y presupuesto de recursos | [04](04_capacidades_del_switch.md), [08](08_inventario_del_slice.md) | **Documentada**; pendiente de ejecución en el slice | Checklist de capacidades ejecutado y tabla del slice completa |
| **2 — Despliegue** | Llevar el diseño al slice: switches, clúster ONOS, servidores y servicios base | [05](05_plan_de_implementacion.md), [06](06_plan_de_trabajo_etapa_2.md), [09](09_plan_de_construccion.md) | **Planificada** | Entorno reproducible, clúster sano y flujos F1–F3 operativos |
| **3 — Ejecución y medición** | Integrar F1–F7, ejecutar R4, probar permisos y medir los requisitos | [07](07_plan_de_trabajo_etapa_3.md) | **Planificada** | Evidencia completa, métricas registradas y cierre documentado |

## 1. Relación entre etapas

```text
Etapa 0 ──► Etapa 1 ──► Etapa 2 ──► Etapa 3
permisos     slice        despliegue   ejecución
ejecutable   verificado   reproducible y medición
```

- La **etapa 0** entrega la política que los servicios y el switch aplican; su fuente de verdad es [`policy/permisos.yaml`](policy/permisos.yaml).
- La **etapa 1** confirma que el slice puede sostener el diseño; si una capacidad falta, se activa el respaldo declarado en [`04`](04_capacidades_del_switch.md) antes de desplegar.
- La **etapa 2** construye el entorno y demuestra los flujos base; no mide todavía la campaña completa.
- La **etapa 3** produce la evidencia: flujos extremo a extremo, R4, suite de permisos, resiliencia, capacidad y seguridad.

## 2. Qué no cambia entre etapas

Los estilos, patrones, roles, perfiles, contratos y prioridades de la arquitectura de referencia se mantienen. La reducción de switches y servidores es una adaptación de despliegue, no un cambio de arquitectura. Las decisiones cerradas en la etapa 0 solo se revisan si una medición de la etapa 3 obliga a un cambio explícito, versionado en el YAML.

## 3. Documentos de referencia

| Documento | Uso |
|---|---|
| [`../docs/fases/H-Despliegue/`](../docs/fases/H-Despliegue/) | Infraestructura, VMs, red y puertos de referencia |
| [`../docs/fases/F-Decisiones_tecnologicas/`](../docs/fases/F-Decisiones_tecnologicas/) | Decisiones de controlador, plano de datos, identidad y mensajería |
| [`../docs/fases/G-Diseno_de_bajo_nivel-LLD/`](../docs/fases/G-Diseno_de_bajo_nivel-LLD/) | Contratos, reglas, configuraciones y detalles de implementación |
| [`../flows/`](../flows/) | Flujos explicados paso a paso, con mensajes OpenFlow |
