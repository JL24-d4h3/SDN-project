# Detalles de implementación

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** G — Diseño de bajo nivel (LLD)
**Estado:** Borrador formal para revisión

---

Cada **servicio es una responsabilidad** ([`D-04`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/04_descomposición_arquitectonica.md) §3) **con un ciclo de vida** —arranque, operación, degradación, reconciliación— **y una estructura interna en capas**: API (entrada síncrona), dominio (la lógica), persistencia (su base, solo la suya) y salida de eventos (el bus). Los productos (controlador, broker, bases, RADIUS, directorio, sensor) quedan como están: los servicios propios **no reimplementan lo que los productos ya hacen**.

**Ecosistema único** para los servicios propios: **Python 3.12**, con FastAPI para las APIs, SQLAlchemy para la persistencia, `pika` para el bus, `pyrad` para RADIUS y una implementación directa de RFC 6238 para el TOTP. Un solo lenguaje para ocho servicios es simplicidad justificada (P4): un patrón de despliegue, un patrón de pruebas y una sola forma de operar para todo el equipo. El controlador es Java (ONOS, producto) y el sensor C (Suricata, producto): cada pieza en su ecosistema natural.

**Ciclo de vida común.** Todo servicio expone `/health` en dos niveles: *liveness* (el proceso vive) y *readiness* (su base y sus colas responden). Un servicio no *ready* no recibe tráfico; la red **no** depende de él — lo instalado en los switches sigue operando (P2). La degradación sigue las garantías de [`02`](02_eventos.md) §5 (buffer local, DLQ, huecos declarados) y la reconciliación la regla de [`03`](03_datos.md) §4: **el plano de datos es la verdad**.

## 2. IAM — la identidad y sus sesiones

**Módulos:** `api` (I3 e I7) · `radclient` (I4) · `sesiones` · `totp` · `tokens` · `repositorio` (bd_iam).

```text
login(usuario, secreto, poblacion, ip_origen):
  si poblacion == "operacion":
      op = operadores[usuario]; verificar_bcrypt(secreto, op.hash)
      verificar_totp(op.totp_secreto, codigo, ventana=±1)     # sin variante sin TOTP
  si poblacion == "comunidad":
      r = radius.access_request(usuario, secreto)              # IdP decide (I4)
      perfil = r.atributos["perfil"]; radius.accounting("Start")
  asociacion = i2.asociaciones(ip=ip_origen)                   # ligadura al dispositivo
  sesion = crear_sesion(usuario, perfil, asociacion, ttl[perfil])
  publicar(SessionOpened)                                      # el Policy Engine ordena el perfil
  emitir_cookie_opaca(sesion)                                  # HttpOnly · Secure · SameSite

validar_peticion(cookie, ip_origen):
  s = sesiones[hash(cookie)]            # la validez vive en el servidor
  exigir(s.estado == activa y s.ip == ip_origen y ahora < s.hard_timeout)
  s.ultima_actividad = ahora

al_evento(MAC_Moved) si mac ∈ sesiones activas:
  cerrar_sesion(motivo="mac_moved"); radius.accounting("Stop"); publicar(SessionClosed)
```

El token para herramientas es el mismo hash de sesión con expiración propia (`tokens_derivados`): una sola fuente de verdad, dos formas de presentarla ([`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §4).

## 3. Registro — el catálogo de dispositivos privilegiados

**Módulos:** `api` · `catalogo` · `historial` · `repositorio` (bd_registro).

El alta es el acto administrativo que habilita (P7): TI registra el dispositivo (I7) → el Registro crea la entrada y su historial → el IAM emite el secreto TOTP del operador **una vez** (QR en la consola) → el operador verifica un código → recién entonces el par (dispositivo, operador) queda habilitado y el alta completa se audita ([`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §3). Cada `DeviceConnected` de una MAC registrada se anota en `historial_dispositivo` — es la fuente de la investigación de movimientos.

## 4. Monitor — la observación

**Módulos:** `sondeo` (I8 vía I2) · `ewma` · `publicador` · `repositorio` (bd_monitor).

```text
bucle_sondeo():                                  # régimen dual: 5 s caliente / 60 s completo
  por cada switch del lote:
      c = i2.contadores(switch)                  # multipart vía controlador (P1)
      si timeout(2s): registrar hueco de observacion; continuar   # no se inventa (P11)
      deltas = c - anterior; persistir(contadores)
  por cada destino protegido: actualizar_ewma(destino, deltas)
  publicar(MetricSample, por destino y ventana)  # materia prima de la Detección

actualizar_ewma(destino, x):
  b = lineas_base[destino]
  b.media   += alfa * (x - b.media)              # α = 0,2 (inicial)
  b.varianza += alfa * ((x - b.media)^2 - b.varianza)
```

El Monitor también **verifica** las mitigaciones: ante `MitigationApplied` compara los contadores del objetivo contra la línea base y publica `MitigationVerified` con `tasas_antes/despues` y `cumple_objetivo` — el segundo nivel de confirmación de I2 ([`F-01`](../F-Decisiones_tecnologicas/01_controlador_y_api_northbound.md) §4.4). Y produce `MAC_Moved`: la incoherencia entre la asociación aprendida y la ubicación observada es un **hecho determinista**, no un umbral (P7).

## 5. Detección — el juicio

**Módulos:** `clasificador` · `umbrales` (bd_politicas) · `histeresis`.

```text
al_metric_sample(m):
  b = linea_base(m.destino)
  si calentamiento_activo(m.destino): alertar_sin_actuar; return   # 30 min iniciales
  umbral = max(k_entrada * b.sigma, piso[destino])                  # relativo con piso
  si m.pps > b.media + umbral:
      s = estado[destino]
      si s == normal: s = sospecha(t0)              # 1ª ventana
      si s == sospecha y ventanas(t0) >= N:         # N = 3 sostenidas
          clase = clasificar(m)                     # flood / distribuido / brute / scanning
          publicar(AnomalyDetected, severidad_propuesta)
          s = alarma
  si m.pps < b.media + k_salida * b.sigma: s = normal   # histéresis: cuesta más salir
```

Las reglas de clasificación son las de [`F-06`](../F-Decisiones_tecnologicas/06_deteccion_y_mitigacion.md) §4 (≥ 10 fuentes/60 s → distribuido; ≥ 20 req/s por origen → brute-force; > 20 destinos/60 s → scanning). La Detección **clasifica, no ordena** (P8): su salida es `AnomalyDetected`; la respuesta es del Policy Engine.

## 6. Incidentes — el ciclo de vida

**Módulos:** `ciclo_vida` · `secuencia` · `consumidor_inc` (cola `inc.<id>`) · `reconciliacion` · `repositorio` (bd_incidentes).

```text
estados:  ABIERTO → EN_MITIGACION → MITIGADO → CERRADO
          └─► ESCALADO (brecha P12 o cuarentena pendiente) ─► CERRADO / nuevo peldaño

al_evento(e, secuencia):
  persistir eventos_incidente(e, secuencia)        # antes de procesar: reinicio sin pérdida
  si secuencia != esperada+1: hueco declarado; esperar faltante (buffer 100, 10 s)
  transicionar(incidente, e.tipo)                  # AnomalyDetected → abrir; Verified → mitigar…
  publicar por la cola del incidente y por las colas de servicio

reconciliar():                                     # al volver de una caída
  vivas = i2.reglas(cookie=inc.*)                  # la verdad del plano de datos
  por cada mitigación registrada sin regla viva: marcar expirada y cerrar (P10)
```

## 7. Políticas — la decisión y la orden

**Módulos:** `escalera` · `elevaciones` · `ordenes` (I2) · `repositorio` (bd_politicas).

```text
al_evento(IncidentOpened):
  peldaño = escalera[severidad, patrón]            # RATE_LIMIT → BLOCK → ISOLATE → QUARANTINE
  si peldaño == QUARANTINE: estado = ESPERANDO_APROBACION; publicar a Consola; return
  orden = i2.aplicar_mitigacion(peldaño, objetivo, orígenes, ttl)
  publicar(MitigationRequired)                     # el eco: informa, no ejecuta

al_evento(MitigationVerified) si no cumple_objetivo:
  publicar(IncidentEscalated)                      # P12: la brecha escala a humano (F-06 §6)
  # nunca se sube la fuerza automáticamente: P9 prima en la ejecución

aprobar_cuarentena(aprobacion_id):                 # vía I7, con humano
  i2.aplicar_mitigacion(QUARANTINE, aprobacion=aprobacion_id)
```

## 8. Auditoría — la prueba

**Módulos:** `ingesta` (cola `auditoria`, todo el catálogo) · `registro_directo` (actos I7) · `exportador` · `repositorio` (bd_auditoria).

```text
exportar(rango):                                   # retención larga, append-only
  por cada línea del rango:                        # tabla de 90 días
      hash = sha256(linea ‖ hash_anterior); escribir(linea + hash)
  registrar exports(archivo, rango, hash_final)
```

El export es **append-only con cadena de hash** ([`03`](03_datos.md) §3): cada línea encadena la anterior; el hash final se copia en `exports` y abre el archivo siguiente. La manipulación no puede pasar inadvertida (P11). El drill de restauración y el verificador de cadena son los que E-04 y F-05 exigen.

## 9. El adaptador del perímetro y la Consola

**El adaptador del sensor** — materializado con Suricata: consume `eve.json`, traduce cada alerta de firma a un evento `AnomalyDetected` con `origen = "perimetro"` y lo publica — la cadena de R5 entra por el mismo camino que el resto ([`F-07`](../F-Decisiones_tecnologicas/07_perimetro_r5.md) §3). **Consola**: cliente de I7 (sin credenciales propias: la sesión es el SSO), suscrita a su cola para las alertas en vivo, y la que muestra el QR de aprovisionamiento TOTP en el alta.

## 10. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Login de operador con código TOTP incorrecto | Rechazo del segundo factor, sin variante sin TOTP | R1.2 |
| Cookie presentada desde otra IP | Rechazo e invalidación de sesión | RNF-01 |
| Sondeo con controlador detenido 30 s | Huecos declarados; línea base intacta | P11 |
| Escenario flood completo | Detección N ventanas → orden → `APLICADA` → `Verified` | R4, D-08 §6 |
| Reconciliación tras caída del Incident Manager | Mitigaciones expiradas cerradas contra I2 | E-04, P10 |
| Verificador de cadena de hash sobre un export alterado | La alteración rompe la cadena y se detecta | P11 |
