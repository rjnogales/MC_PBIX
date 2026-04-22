# PBIX Analytics - Extraccion y Catalogo Tecnico

## Objetivo

Este proyecto procesa archivos PBIX para extraer metadatos del modelo semantico y generar un Excel por cada PBIX con:

- Tablas
- Columnas
- Medidas DAX
- Relaciones
- Glosario tecnico

El pipeline usa pbi-tools para descomponer los PBIX y luego scripts Python para leer los archivos TMDL.

## Estructura actual del repositorio

- OFICINA_EVALUACION/
- PRESIDENCIA/
- zCODE/
- README.md

Cada area tiene su propia estructura de datos/artefactos:

- PBIXs (entrada de .pbix)
- PBIXs_descompuestos (salida de pbi-tools)
- PBIXs_output (Excel generados)
- config/pipeline.json (configuracion del area)
- proceso_pbix.log (log de ejecucion del area)

Regla clave de configuracion:

- Cada oficina/area de datos debe tener su propio config/pipeline.json.
- No se usa un pipeline.json dentro de PBIXs, PBIXs_descompuestos o PBIXs_output.
- La relacion es 1 oficina (area) = 1 archivo de configuracion.
- La carpeta config es obligatoria dentro de cada area.
- En pipeline.json, area_id debe ser el mismo nombre de la carpeta del area de datos (ejemplo: carpeta OFICINA_EVALUACION -> area_id: OFICINA_EVALUACION).

## Scripts y responsabilidad

Los scripts en zCODE estan centralizados y reutilizables para todas las areas.

- 01_leer_tablas.py: Lee tablas desde Model/tables y excluye tablas tecnicas.
- 02_leer_columnas.py: Lee columnas y tipos de datos desde archivos .tmdl.
- 03_leer_medidas.py: Lee medidas DAX y limpia ruido de metadatos.
- 04_leer_relaciones.py: Lee relaciones desde Model/relationships.tmdl.
- 05_exportar_excel.py: Clasifica tablas/relaciones y exporta el Excel final.
- 06_procesar_pbixs.py: Orquesta la ejecucion completa por area.
- 07_definir_area.py: Lanza la ejecucion por parametro de area en linea de comando.

## Contrato de entrada/salida por script

### 01_leer_tablas.py

Entrada:

- ruta_pbix (ruta a PBIX descompuesto con carpeta Model/tables).

Salida:

- list[str] con nombres de tablas no tecnicas.

### 02_leer_columnas.py

Entrada:

- ruta_pbix (ruta a PBIX descompuesto con archivos .tmdl en Model/tables).

Salida:

- list[dict] con llaves: tabla, columna, tipo.

### 03_leer_medidas.py

Entrada:

- ruta_pbix (ruta a PBIX descompuesto con medidas en archivos .tmdl).

Salida:

- list[dict] con llaves: tabla, medida, dax.

### 04_leer_relaciones.py

Entrada:

- ruta_pbix (ruta a PBIX descompuesto con Model/relationships.tmdl).

Salida:

- list[dict] con llaves: tabla_origen, columna_origen, tabla_destino, columna_destino.

### 05_exportar_excel.py

Entrada:

- tablas (DataFrame), columnas (DataFrame), medidas (DataFrame), relaciones (DataFrame), output_file (ruta).

Salida:

- archivo Excel por PBIX con hojas Tablas, Columnas, Medidas, Relaciones y Glosario.

### 06_procesar_pbixs.py

Entrada:

- area activa definida por AREA_ID_MANUAL, variable PBIX_AREA o AREA_ID_DEFAULT.
- configuracion de rutas desde `<AREA>`/config/pipeline.json.
- archivos .pbix en `<AREA>`/PBIXs.

Salida:

- PBIX descompuestos en `<AREA>`/PBIXs_descompuestos.
- Excel por PBIX en `<AREA>`/PBIXs_output.
- log del proceso en `<AREA>`/proceso_pbix.log (o ruta definida en paths.log_file).

### 07_definir_area.py

Entrada:

- AREA_ID por linea de comando (ejemplo: OFICINA_EVALUACION).

Salida:

- valida estructura del area y su config/pipeline.json.
- ejecuta 06_procesar_pbixs.py con PBIX_AREA definido para esa corrida.

## Config por area (pipeline.json)

Este archivo define como se procesa cada oficina/area. Sirve para:

- indicar de donde leer los PBIX de entrada;
- indicar donde guardar PBIX descompuestos y Excel de salida;
- definir el archivo de log de esa area;
- aplicar filtros de procesamiento (incluir/excluir patrones);
- configurar el formato de exportacion.

Si una oficina/area no tiene config/pipeline.json, no queda parametrizada correctamente para el flujo automatizado.

Ejemplo de campos usados:

- area_id
- paths.pbix_in
- paths.pbix_descompuestos
- paths.output
- paths.log_file
- procesamiento.incluir_patrones
- procesamiento.excluir_patrones
- exportacion.formato_salida

Regla para area_id:

- Debe coincidir con el nombre de la carpeta del area.
- Ejemplo valido: carpeta PRESIDENCIA con area_id = PRESIDENCIA.

## Requisitos

- Python con dependencias del proyecto
- pbi-tools instalado y disponible en PATH

Compatibilidad validada en este workspace:

- pbi-tools Desktop 1.2.0 no acepta -o en extract.
- Comando compatible: pbi-tools extract `<pbixPath>`
- Si falla mover la salida por locks/rutas largas en Windows, el proceso usa fallback.

## Pruebas automaticas

Se incorporo una suite de pruebas unitarias con pytest para validar el nucleo del proceso de extraccion y catalogo.

Cobertura objetivo definida:

- 90% minimo para los modulos del MVP.

Cobertura del MVP implementado:

- 01_leer_tablas.py
- 02_leer_columnas.py
- 03_leer_medidas.py
- 04_leer_relaciones.py
- 05_exportar_excel.py

Estructura de pruebas creada:

- zCODE/tests/conftest.py
- zCODE/tests/unit/test_01_leer_tablas.py
- zCODE/tests/unit/test_02_leer_columnas.py
- zCODE/tests/unit/test_03_leer_medidas.py
- zCODE/tests/unit/test_04_leer_relaciones.py
- zCODE/tests/unit/test_05_exportar_excel.py
- zCODE/tests/unit/test_06_procesar_pbixs_unit.py
- zCODE/tests/regression/reglas_negocio/test_funcional_reglas_negocio.py
- zCODE/tests/regression/regresion_referencia/test_regresion_referencia.py
- zCODE/pytest.ini
- zCODE/.coveragerc
- zCODE/requirements-test.txt


### Matriz de pruebas unitarias (26)

| # | Script de prueba | Caso | Validacion principal |
|---|---|---|---|
| 1 | zCODE/tests/unit/test_01_leer_tablas.py | test_leer_tablas_excluye_tecnicas | Excluye tablas tecnicas y no tmdl. |
| 2 | zCODE/tests/unit/test_01_leer_tablas.py | test_leer_tablas_lanza_si_no_existe_directorio | Error si no existe Model/tables. |
| 3 | zCODE/tests/unit/test_01_leer_tablas.py | test_leer_tablas_vacio | Retorna lista vacia sin tablas validas. |
| 4 | zCODE/tests/unit/test_02_leer_columnas.py | test_leer_columnas_extrae_tabla_columna_tipo | Extrae tabla, columna y dataType. |
| 5 | zCODE/tests/unit/test_02_leer_columnas.py | test_leer_columnas_excluye_tecnicas | Ignora LocalDateTable y DateTableTemplate. |
| 6 | zCODE/tests/unit/test_02_leer_columnas.py | test_leer_columnas_ignora_si_no_hay_data_type | Omite columnas sin dataType. |
| 7 | zCODE/tests/unit/test_02_leer_columnas.py | test_leer_columnas_lanza_si_no_existe_directorio | Error por ruta inexistente. |
| 8 | zCODE/tests/unit/test_03_leer_medidas.py | test_limpiar_dax_remueve_prefijos_y_metadatos | Limpia prefijos y metadatos del DAX. |
| 9 | zCODE/tests/unit/test_03_leer_medidas.py | test_leer_medidas_extrae_medida_dax | Extrae medida y DAX correctamente. |
| 10 | zCODE/tests/unit/test_03_leer_medidas.py | test_leer_medidas_devuelve_vacio_sin_cierre_parentesis | No registra medida sin cierre de expresion. |
| 11 | zCODE/tests/unit/test_03_leer_medidas.py | test_leer_medidas_lanza_si_no_existe_directorio | Error por directorio inexistente. |
| 12 | zCODE/tests/unit/test_04_leer_relaciones.py | test_leer_relaciones_parsea_referencias_con_comillas_y_brackets | Parsea comillas, brackets y formato con punto. |
| 13 | zCODE/tests/unit/test_04_leer_relaciones.py | test_leer_relaciones_sin_punto_devuelve_columna_vacia | Si no hay punto, deja columna origen vacia. |
| 14 | zCODE/tests/unit/test_04_leer_relaciones.py | test_leer_relaciones_lanza_si_no_existe_archivo | Error si falta relationships.tmdl. |
| 15 | zCODE/tests/unit/test_05_exportar_excel.py | test_clasificar_tabla_nombre | Heuristica HECHO, DIMENSION, OTRO por nombre. |
| 16 | zCODE/tests/unit/test_05_exportar_excel.py | test_clasificar_tablas_y_columnas | Clasifica tablas y propaga tipo a columnas. |
| 17 | zCODE/tests/unit/test_05_exportar_excel.py | test_clasificar_relaciones_y_glosario | Clasifica relaciones y valida estructura del glosario. |
| 18 | zCODE/tests/unit/test_05_exportar_excel.py | test_exportar_excel_genera_archivo_y_hojas | Genera Excel con 5 hojas esperadas. |
| 19 | zCODE/tests/unit/test_06_procesar_pbixs_unit.py | test_cargar_config_area_defaults | Carga configuracion por defecto. |
| 20 | zCODE/tests/unit/test_06_procesar_pbixs_unit.py | test_cargar_config_area_override | Aplica override desde pipeline.json. |
| 21 | zCODE/tests/unit/test_06_procesar_pbixs_unit.py | test_resolver_ruta_area_relativa_y_absoluta | Resuelve rutas relativas y absolutas. |
| 22 | zCODE/tests/unit/test_06_procesar_pbixs_unit.py | test_metadata_corresponde_pbix | Verifica coincidencia de firma de metadata. |
| 23 | zCODE/tests/unit/test_06_procesar_pbixs_unit.py | test_leer_y_guardar_metadata_extraccion | Guarda y lee metadata de extraccion. |
| 24 | zCODE/tests/unit/test_06_procesar_pbixs_unit.py | test_descomponer_pbix_reutiliza_metadata | Reutiliza descomposicion vigente por metadata. |
| 25 | zCODE/tests/unit/test_06_procesar_pbixs_unit.py | test_procesar_pbix_ok | Flujo completo exitoso de procesamiento. |
| 26 | zCODE/tests/unit/test_06_procesar_pbixs_unit.py | test_procesar_pbix_falla_si_no_hay_model | Falla controlada si no existe Model/tables. |



### Ejecutar pruebas (Windows)

Desde la raiz del proyecto:

1. Instalar dependencias de pruebas:

python -m pip install -r zCODE/requirements-test.txt

2. Ejecutar suite por defecto (unitarias + funcionales + regresion, sin cobertura obligatoria):

python -m pytest -c zCODE/pytest.ini -q

3. Ejecutar suite por defecto con cobertura y umbral (90%):

python -m pytest -c zCODE/pytest.ini -q --cov=. --cov-config=zCODE/.coveragerc --cov-report=term-missing --cov-report=html --cov-fail-under=90

4. Ejecutar solo pruebas unitarias:

python -m pytest -c zCODE/pytest.ini zCODE/tests/unit -q

5. Ejecutar solo pruebas funcionales (reglas de negocio):

python -m pytest -c zCODE/pytest.ini zCODE/tests/regression/reglas_negocio -q -m functional -o "addopts=-v --tb=short --strict-markers"

6. Ejecutar solo pruebas de regresion contra referencia:

python -m pytest -c zCODE/pytest.ini zCODE/tests/regression/regresion_referencia -q -m regression -o "addopts=-v --tb=short --strict-markers"

7. Generar vista HTML amigable de JUnit y actualizar enlaces en htmlcov/index.html (tambien crea htmlcov/cobertura-index.html):

python zCODE/tests/reports/postprocess_reports.py

8. Generar evidencia XML/TXT de funcional:

python -m pytest -c zCODE/pytest.ini zCODE/tests/regression/reglas_negocio -q -m functional -o "addopts=-v --tb=short --strict-markers" --junitxml=zCODE/tests/reports/junit-funcional.xml | tee zCODE/tests/reports/pytest-funcional-summary.txt

9. Generar evidencia XML/TXT de regresion de referencia:

python -m pytest -c zCODE/pytest.ini zCODE/tests/regression/regresion_referencia -q -m regression -o "addopts=-v --tb=short --strict-markers" --junitxml=zCODE/tests/reports/junit-regresion-referencia.xml | tee zCODE/tests/reports/pytest-regresion-referencia-summary.txt

Atajo en una sola linea (suite por defecto + postproceso):

python -m pytest -c zCODE/pytest.ini -q --junitxml=zCODE/tests/reports/junit.xml && python zCODE/tests/reports/postprocess_reports.py

Atajo en una sola linea (suite con cobertura + postproceso):

python -m pytest -c zCODE/pytest.ini -q --cov=. --cov-config=zCODE/.coveragerc --cov-report=term-missing --cov-report=html --cov-fail-under=90 --junitxml=zCODE/tests/reports/junit.xml && python zCODE/tests/reports/postprocess_reports.py

Atajo recomendado de control completo (unitario + funcional + regresion + postproceso):

python -m pytest -c zCODE/pytest.ini zCODE/tests/unit -q --junitxml=zCODE/tests/reports/junit.xml && python -m pytest -c zCODE/pytest.ini zCODE/tests/regression/reglas_negocio -q -m functional -o "addopts=-v --tb=short --strict-markers" --junitxml=zCODE/tests/reports/junit-funcional.xml && python -m pytest -c zCODE/pytest.ini zCODE/tests/regression/regresion_referencia -q -m regression -o "addopts=-v --tb=short --strict-markers" --junitxml=zCODE/tests/reports/junit-regresion-referencia.xml && python zCODE/tests/reports/postprocess_reports.py

Notas:

- La configuracion de cobertura del MVP excluye tests y scripts fuera de alcance del objetivo actual.
- Las pruebas se ejecutan con datos sinteticos y no requieren PBIX reales.
- El reporte JUnit amigable queda en zCODE/tests/reports/junit-report.html.
- El indice unificado de resultados queda en zCODE/tests/reports/reports-index.html.
- La portada de cobertura se puede abrir con htmlcov/cobertura-index.html (alias de htmlcov/index.html).
- En GitHub, abrir estos .html desde el repositorio muestra el codigo fuente; para verlos renderizados se recomienda GitHub Pages o descargar/artifact del pipeline y abrir localmente.
- Para GitHub Pages se recomienda usar una sola puerta de entrada: zCODE/tests/reports/reports-index.html (desde ahi se enlaza tambien a cobertura).

Clasificacion oficial de fases:

- Punto 2: pruebas funcionales (reglas de negocio).
- Punto 4: pruebas de regresion contra dataset de referencia.

Estructura de datos de referencia (punto 4):

- zCODE/tests/fixtures/regresion_referencia/caso_base
- zCODE/tests/fixtures/regresion_referencia/expected_snapshot.json

Evidencias de pruebas (carpeta unica):

- zCODE/tests/reports/pytest-summary.txt
- zCODE/tests/reports/junit.xml
- zCODE/tests/reports/pytest-funcional-summary.txt
- zCODE/tests/reports/junit-funcional.xml
- zCODE/tests/reports/pytest-regresion-referencia-summary.txt
- zCODE/tests/reports/junit-regresion-referencia.xml
- zCODE/tests/reports/junit-report.html

## Como ejecutar

### Opcion 0: Script lanzador por parametro de area (recomendada)

Permite ejecutar indicando el area directamente en la linea de comando.

Git Bash / PowerShell:

python zCODE/07_definir_area.py OFICINA_EVALUACION
python zCODE/07_definir_area.py PRESIDENCIA

Este lanzador valida que exista la carpeta del area y su config/pipeline.json, define PBIX_AREA para esa ejecucion y luego llama automaticamente a zCODE/06_procesar_pbixs.py.

### Opcion A: Seleccion por variable de entorno

Git Bash:

export PBIX_AREA=PRESIDENCIA
python zCODE/06_procesar_pbixs.py

PowerShell:

$env:PBIX_AREA = "PRESIDENCIA"
python zCODE/06_procesar_pbixs.py

### Opcion B: Seleccion manual en codigo

Editar zCODE/06_procesar_pbixs.py:

- Asignar valor en AREA_ID_MANUAL
- Dejar vacio AREA_ID_MANUAL para volver a usar variable de entorno/default

## Flujo resumido

1. Buscar PBIX en `<AREA>`/PBIXs.
2. Descomponer con pbi-tools si hace falta (control por metadata).
3. Leer tablas, columnas, medidas y relaciones.
4. Generar Excel en `<AREA>`/PBIXs_output.
5. Escribir log en `<AREA>`/proceso_pbix.log.

## Siguientes pasos sugeridos

- Agregar mas areas creando su carpeta y config/pipeline.json.
- Opcional: usar procesamiento.incluir_patrones para correr subconjuntos.
- Opcional: versionar plantillas de config para nuevas areas.

## Ejemplo final de ejecucion

Comando:

python zCODE/07_definir_area.py OFICINA_EVALUACION

Salida esperada (resumen):

- Ejecutando area: OFICINA_EVALUACION
- Comando: `<python>` zCODE/06_procesar_pbixs.py
- INICIO PROCESO MASIVO PBIX
- Área activa: OFICINA_EVALUACION
- PROCESO FINALIZADO
