# Método y mapa del despliegue

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** H — Despliegue
**Estado:** Borrador formal para revisión

---

**Desplegar es asignar cada elemento lógico a una máquina, una red y un orden reales.** La fase G escribió qué corre **dentro** de cada componente; esta fase define **las máquinas, la red y la secuencia** sobre las que corre. Materializa el entorno que [`F-08`](../F-Decisiones_tecnologicas/08_entorno_del_prototipo.md) decidió: contenedores para los servicios, máquinas virtuales para quien necesita identidad de red propia, el switch físico como plano de datos.

El despliegue tiene **dos vistas**, y la distinción es la de [`C-04`](../C-Contexto/04_alcance_de_la_infraestructura.md):

- **El prototipo** — lo que el proyecto **despliega** en el laboratorio y sobre lo que valida. Toda la serie lo describe al detalle de puerto y parámetro.
- **La referencia** — el campus que la solución describe. Se **analiza por diseño, no se despliega** ([`C-04`](../C-Contexto/04_alcance_de_la_infraestructura.md) §4): redundancia de nodos y enlaces, clúster del controlador en operación, canal in-band, feeds externos de inteligencia, cifrado en reposo y política de respaldo — exactamente lo que [`F-09`](../F-Decisiones_tecnologicas/09_sintesis_y_trazabilidad.md) §5 dejó para esta fase. Cada documento la recoge en su sección final, con sus condiciones de habilitación.

**La regla de lectura** es la misma que en G ([`G-00`](../G-Diseno_de_bajo_nivel-LLD/00_metodo_y_mapa.md) §1): primero lo general —el plano, la jerarquía, el criterio— y luego lo particular —la máquina, el puerto, el valor.

## 2. El mapa de la serie

| Documento | Lo general | Lo particular |
|---|---|---|
| [`01`](01_infraestructura_fisica.md) | Asignar lo lógico a hardware real; separación física de planos | Inventario del laboratorio; la referencia analizada |
| [`02`](02_vms_y_contenedores.md) | Dos formas de ejecución: quien necesita identidad de red propia es VM | Inventario completo con versiones y recursos |
| [`03`](03_red.md) | Cuatro segmentos lógicos + canal de control fuera de banda | Direccionamiento IPv4 estático, tabla a tabla |
| [`04`](04_vlans_y_subredes.md) | El segmento lógico materializado; la política sigue en las reglas | Correspondencia VLAN ↔ segmento, tagged/untagged |
| [`05`](05_puertos.md) | El plano de puertos materializa los enlaces | Asignación puerto a puerto por switch |
| [`06`](06_dependencias.md) | El orden de arranque como grafo: tiempo → identidad → estado → política → observación | Secuencia, versiones fijadas, arranque degradado |

## 3. Invariantes del despliegue

- **Topología:** ocho switches — dos núcleo, dos distribución, cuatro acceso — dual-homed, 13 enlaces ([`01`](01_infraestructura_fisica.md) §3): la redundancia del plano de datos **se despliega y se mide**; la del plano de control (clúster del controlador) se documenta, no se despliega (C-04 §4).
- **Canal de control fuera de banda** (RP-02): las interfaces de gestión de los switches nunca atraviesan el plano de datos; la variante in-band es un objetivo aspiracional analizado, no desplegado.
- **Todo tráfico de ataque es interno al entorno del proyecto** (RP-06, RP-08): nada malicioso hacia redes del campus ni de terceros.
- **IPv4** (RP-12): direccionamiento privado, estático donde la reproducibilidad lo exige.
- **Reproducibilidad** (RNF-11): el despliegue completo se levanta desde una definición versionada; recrear el entorno no es un procedimiento manual.
- **Alcance** (RP-04): el prototipo representa los escenarios, no reproduce el campus — las cifras de capacidad valen para el prototipo y así se reportan ([`F-08`](../F-Decisiones_tecnologicas/08_entorno_del_prototipo.md) §6).

## 4. Fronteras

- **La medición** (prototipo): este despliegue es el instrumento de las verificaciones de F y G; los números finales salen de correr sobre él, no de este documento.
- **El campus real**: fuera del alcance del curso; la referencia de esta serie es el análisis que lo anticipa.
