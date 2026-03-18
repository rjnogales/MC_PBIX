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

Areas creadas en esta implementacion:
- OFICINA_EVALUACION
- PRESIDENCIA

## Beneficio institucional
- Separacion clara de informacion por area
- Menor riesgo de mezclar insumos y salidas
- Escalabilidad simple para nuevas areas
- Trazabilidad de ejecucion con log por area

## Como se selecciona el area al ejecutar
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
- No se duplican scripts por area.

## Proximo paso recomendado
Cuando cada area entregue sus PBIX:

1. Cargar PBIX en <AREA>/PBIXs/
2. Ejecutar pipeline para esa area
3. Validar Excel y log generado
4. Repetir para las demas areas
