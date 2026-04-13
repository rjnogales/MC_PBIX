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
