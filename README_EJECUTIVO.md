# PBIX Analytics - Resumen Ejecutivo

## Que es este aplicativo
Este aplicativo toma archivos PBIX de cada area institucional y genera un catalogo tecnico en Excel con:

- Tablas
- Columnas
- Medidas
- Relaciones

El objetivo es estandarizar y acelerar la documentacion tecnica de modelos Power BI.

## Que cambio en esta fase
Se paso de una estructura global a una estructura por area.

Antes:
- PBIXs/
- PBIXs_descompuestos/
- PBIXs_output/

Ahora, por cada area:
- <AREA>/PBIXs/
- <AREA>/PBIXs_descompuestos/
- <AREA>/PBIXs_output/
- <AREA>/config/pipeline.json
- <AREA>/proceso_pbix.log

Regla operativa:
- Cada oficina/area de datos debe tener su propio config/pipeline.json.
- La relacion es 1 oficina (area) = 1 configuracion.

Areas creadas en esta implementacion:
- OFICINA_EVALUACION
- PRESIDENCIA

## Beneficio institucional
- Separacion clara de informacion por area
- Menor riesgo de mezclar insumos y salidas
- Escalabilidad simple para nuevas areas
- Trazabilidad de ejecucion con log por area

## Control de calidad incorporado

Se implemento una capa de pruebas automaticas para fortalecer la confiabilidad del proceso tecnico.

- Suite unitaria en zCODE/tests/unit
- Cobertura objetivo del MVP: 90%
- Validacion de extraccion de tablas, columnas, medidas y relaciones
- Validacion de exportacion de catalogo tecnico a Excel

Clasificacion oficial de control:

- Punto 2: pruebas funcionales (reglas de negocio).
- Punto 4: pruebas de regresion contra dataset de referencia.

Estado de implementacion actual:

- Punto 2 implementado en zCODE/tests/regression/reglas_negocio.
- Punto 4 implementado en zCODE/tests/regression/regresion_referencia.

Impacto de negocio:

- Reduce el riesgo de regresiones por cambios en parser o reglas.
- Mejora la estabilidad operativa antes de procesamientos masivos.

## Indicadores verificables (corte 2026-04-20)

| Indicador | Resultado | Criterio | Estado |
|---|---:|---:|---|
| Pruebas ejecutadas | 26 | N/A | Cumple |
| Pruebas aprobadas | 26 | 100% de las ejecutadas | Cumple |
| Pruebas fallidas | 0 | 0 | Cumple |
| Cobertura objetivo MVP | 90% | >= 90% | Cumple |
| Cobertura alcanzada | 98.12% | >= 90% | Cumple |
| Cobertura 01_leer_tablas.py | 100% | >= 90% | Cumple |
| Cobertura 02_leer_columnas.py | 96% | >= 90% | Cumple |
| Cobertura 03_leer_medidas.py | 98% | >= 90% | Cumple |
| Cobertura 04_leer_relaciones.py | 100% | >= 90% | Cumple |
| Cobertura 05_exportar_excel.py | 98% | >= 90% | Cumple |

Fuentes de evidencia:

- Resumen de ejecucion: zCODE/tests/reports/pytest-summary.txt
- Reporte XML (formato JUnit): zCODE/tests/reports/junit.xml
- Reporte HTML de cobertura: zCODE/htmlcov/index.html

Comando de reproduccion (local Windows):

- python -m pytest -c zCODE/pytest.ini zCODE/tests/unit -q

Alcance de cobertura del MVP:

- Incluye: 01_leer_tablas.py, 02_leer_columnas.py, 03_leer_medidas.py, 04_leer_relaciones.py, 05_exportar_excel.py
- Excluye por definicion de fase: 06_procesar_pbixs.py, 07_definir_area.py

## Como se selecciona el area al ejecutar
Forma recomendada (linea de comando):

- python zCODE/07_definir_area.py OFICINA_EVALUACION
- python zCODE/07_definir_area.py PRESIDENCIA

El lanzador valida la carpeta del area y su config/pipeline.json, define PBIX_AREA para esa ejecucion y llama el proceso principal.

Alternativas disponibles:
El sistema usa esta prioridad:

1. Valor manual en el script (si se define)
2. Variable de entorno PBIX_AREA
3. Valor por defecto OFICINA_EVALUACION

## Resultado esperado por ejecucion
Por cada PBIX procesado se genera un archivo Excel en:

- <AREA>/PBIXs_output/

El proceso deja registro en:

- <AREA>/proceso_pbix.log

## Gobierno de la solucion
- La logica de procesamiento es unica y centralizada en zCODE.
- Cada area solo define sus rutas y parametros en config/pipeline.json.
- El script zCODE/07_definir_area.py estandariza la ejecucion por area.
- No se duplican scripts por area.

## Proximo paso recomendado
Cuando cada area entregue sus PBIX:

1. Cargar PBIX en <AREA>/PBIXs/
2. Ejecutar pipeline para esa area
3. Validar Excel y log generado
4. Repetir para las demas areas

## Ejemplo final de ejecucion

Comando:

python zCODE/07_definir_area.py OFICINA_EVALUACION

Salida esperada (resumen):

- Ejecutando area: OFICINA_EVALUACION
- Comando: <python> zCODE/06_procesar_pbixs.py
- INICIO PROCESO MASIVO PBIX
- Área activa: OFICINA_EVALUACION
- PROCESO FINALIZADO
