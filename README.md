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

## Scripts y responsabilidad
Los scripts en zCODE estan centralizados y reutilizables para todas las areas.

- 01_leer_tablas.py: Lee tablas desde Model/tables y excluye tablas tecnicas.
- 02_leer_columnas.py: Lee columnas y tipos de datos desde archivos .tmdl.
- 03_leer_medidas.py: Lee medidas DAX y limpia ruido de metadatos.
- 04_leer_relaciones.py: Lee relaciones desde Model/relationships.tmdl.
- 05_exportar_excel.py: Clasifica tablas/relaciones y exporta el Excel final.
- 06_procesar_pbixs.py: Orquesta la ejecucion completa por area.

## Lo que acabamos de implementar

1. Reorganizacion por area
- Se movieron las carpetas globales a OFICINA_EVALUACION.
- Se creo la estructura base para PRESIDENCIA.

2. Configuracion por area
- Se agrego OFICINA_EVALUACION/config/pipeline.json.
- Se agrego PRESIDENCIA/config/pipeline.json.
- El script 06 ahora carga rutas desde ese archivo (con defaults seguros).

3. Seleccion de area activa en el script 06
- Se implemento un esquema de prioridad para elegir area:
  1) AREA_ID_MANUAL
  2) Variable de entorno PBIX_AREA
  3) AREA_ID_DEFAULT

Bloque actual en zCODE/06_procesar_pbixs.py:

AREA_ID_MANUAL = ""  # Ej: "PRESIDENCIA" para forzar el area.
AREA_ID_DEFAULT = "OFICINA_EVALUACION"
AREA_ID = (
    AREA_ID_MANUAL.strip()
    or os.getenv("PBIX_AREA", AREA_ID_DEFAULT).strip()
    or AREA_ID_DEFAULT
)

4. Logs por area
- El log ahora se escribe dentro de cada area segun pipeline.json.

## Config por area (pipeline.json)
Ejemplo de campos usados:

- area_id
- paths.pbix_in
- paths.pbix_descompuestos
- paths.output
- paths.log_file
- procesamiento.incluir_patrones
- procesamiento.excluir_patrones
- exportacion.formato_salida

## Requisitos

- Python con dependencias del proyecto
- pbi-tools instalado y disponible en PATH

Compatibilidad validada en este workspace:

- pbi-tools Desktop 1.2.0 no acepta -o en extract.
- Comando compatible: pbi-tools extract <pbixPath>
- Si falla mover la salida por locks/rutas largas en Windows, el proceso usa fallback.

## Como ejecutar

### Opcion A: Seleccion por variable de entorno (recomendada)
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

1. Buscar PBIX en <AREA>/PBIXs.
2. Descomponer con pbi-tools si hace falta (control por metadata).
3. Leer tablas, columnas, medidas y relaciones.
4. Generar Excel en <AREA>/PBIXs_output.
5. Escribir log en <AREA>/proceso_pbix.log.

## Siguientes pasos sugeridos

- Agregar mas areas creando su carpeta y config/pipeline.json.
- Opcional: usar procesamiento.incluir_patrones para correr subconjuntos.
- Opcional: versionar plantillas de config para nuevas areas.
