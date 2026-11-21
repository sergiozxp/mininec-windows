# MININEC for Windows — guía de uso

Distribución no oficial para Windows de [PyMININEC](https://github.com/schlatterbeck/pymininec), implementación de MININEC3 en Python de **Dr. Ralf Schlatterbeck**. Esta distribución añade un ejecutable de consola para simplificar su uso; **no** es MMANA-GAL ni modifica las ecuaciones del motor original.

## 1. Descargar y ejecutar

1. Abre [Actions](https://github.com/sergiozxp/mininec-windows/actions) y selecciona una ejecución exitosa de **Build MININEC for Windows**.
2. En **Artifacts**, descarga `mininec-windows-win64`, descomprímelo y extrae `mininec.exe`.
3. Coloca `mininec.exe` en una carpeta, por ejemplo `C:\MININEC`. No hace falta instalar Python en el equipo que ejecutará el programa.
4. Abre **PowerShell** en esa carpeta y ejecuta:

```powershell
.\mininec.exe --help
```

El EXE es un **programa de consola**: normalmente recibe los datos como **opciones en la misma llamada**, muestra resultados en la consola y puede redirigirlos a un archivo de texto.

> Este procedimiento queda sujeto al éxito de la compilación automática. Que el repositorio exista no significa que el EXE esté ya validado.

## 2. Estructura básica de entrada

```text
mininec.exe -f FRECUENCIA -w DEFINICION_DE_HILO --excitation-pulse=PULSO [OTRAS_OPCIONES]
```

Parámetros básicos documentados por el proyecto original:

| Parámetro | Significado | Unidades / observaciones |
|---|---|---|
| `-f 14.2` | Frecuencia de trabajo | MHz |
| `-w ...` o `--wire ...` | Conductor recto, repetible para cada hilo | Coordenadas y radio en **metros** |
| `--excitation-pulse=10` | Posición de la alimentación | **Pulso MININEC**, no segmento NEC2 |
| `--excitation-voltage=1` | Tensión de alimentación (opcional) | Voltios; 1 V por defecto |
| `--theta=0,5,37` | Barrido angular polar del patrón | Ángulo inicial, paso y número de puntos, en grados |
| `--phi=0,5,73` | Barrido azimutal del patrón | Ángulo inicial, paso y número de puntos, en grados |
| `--frequency-increment=0.1` | Incremento de frecuencia en un barrido | MHz |
| `--frequency-steps=11` | Número de pasos/frecuencias del barrido | Revisar salida y límites del motor |
| `--help` | Mostrar opciones disponibles | Sin modelo de antena |

La sintaxis de cada hilo es:

```text
-w [tag,]nseg,x1,y1,z1,x2,y2,z2,radio
```

- **tag**: identificador numérico opcional del hilo; recomendable cuando existen varios.
- **nseg**: número de segmentos rectos de ese hilo.
- **x1,y1,z1** y **x2,y2,z2**: puntos inicial y final en metros.
- **radio**: **radio físico** del conductor en metros (no diámetro).
- Para varios hilos se repite `-w`; los extremos unidos deben coincidir geométricamente.

Usa punto decimal (`0.001`), no coma decimal: las comas separan valores.

## 3. Ejemplo completo: dipolo horizontal de 10 m

Modelo didáctico: un hilo recto de 10 m de longitud, sobre el eje X, con coordenada Z=6 m y radio de 1 mm, discretizado en 21 segmentos. Se alimenta aproximadamente en el centro.

```powershell
.\mininec.exe -f 14.2 -w 1,21,-5,0,6,5,0,6,0.001 --excitation-pulse=10 > dipolo_14MHz.txt
```

Desglose:

| Componente | Valor | Interpretación |
|---|---|---|
| `-f` | `14.2` | 14,2 MHz |
| `-w` | `1` | Tag 1 |
| `-w` | `21` | 21 segmentos |
| `(x1,y1,z1)` | `(-5,0,6)` | Extremo izquierdo con z=6 m; solo es altura sobre suelo si se activa el suelo |
| `(x2,y2,z2)` | `(5,0,6)` | Extremo derecho con z=6 m |
| radio | `0.001` | 1 mm |
| `--excitation-pulse` | `10` | Alimentación en el pulso 10 |

**Importante:** para un hilo aislado de N segmentos, MININEC normalmente genera N−1 pulsos internos. Por eso **pulso y segmento no son intercambiables**. La ubicación del pulso debe verificarse en el listado de geometría/salida, especialmente con varios hilos. Este ejemplo es de sintaxis y **no** un caso de referencia electromagnética validado.

Para leer el resultado:

```powershell
Get-Content .\dipolo_14MHz.txt
```

La salida textual de PyMININEC contiene información como corrientes, impedancia de alimentación y, cuando se solicitan, patrones de radiación.

## 4. Espacio libre frente a suelo real

**Corrección importante:** si no se especifica suelo, PyMININEC usa **espacio libre** (la salida puede decir `ENVIRONMENT: +1 FOR FREE SPACE`). En ese entorno, trasladar toda la antena en Z de 0 m a 6 m **no altera** sus resultados. Las coordenadas de la sección 3 describen una geometría en el espacio, **no una simulación de antena a 6 metros sobre el terreno**.

La implementación original acepta `--medium=permitividad,conductividad,altura`. La conductividad se especifica en S/m y la altura del primer medio debe ser 0:

| Caso | Opciones de suelo | Uso |
|---|---|---|
| Espacio libre | Ninguna | Comparación sin tierra |
| Suelo perfecto | `--medium=0,0,0` | Plano conductor ideal |
| Suelo real hipotético | `--medium=13,0.005,0` | Ejemplo con εr=13 y σ=0,005 S/m |

Ejemplo del dipolo a 6 m sobre un suelo real homogéneo:

```powershell
.\mininec.exe -f 14.2 -w 1,21,-5,0,6,5,0,6,0.001 --excitation-pulse=10 --medium=13,0.005,0 > dipolo_suelo.txt
```

Para radiales de suelo, PyMININEC proporciona `--radial-count` y `--radial-radius`. El radio aquí es el radio físico del conductor; la **longitud de los radiales** depende de la extensión de la primera región de suelo definida por dos `--medium`, por lo que se debe estudiar el ejemplo original antes de modelar una vertical. Los radiales del modelo de suelo no son intercambiables sin validación con conductores `GW` explícitos de NEC2.

La comparación entre motores debe fijar por escrito las condiciones de suelo, altura, pérdidas y alimentación. **No se debe comparar un resultado MININEC en espacio libre con NEC2 configurado sobre suelo.**

## 5. Extracción de resultados para automatización

La salida nativa es texto, no CSV. Para medir diferencias cuantitativas se necesita un **parser versionado** que extraiga, como mínimo: frecuencia (MHz), resistencia de alimentación R (Ω), reactancia X (Ω), tipo de suelo y configuración del modelo. La salida puede contener etiquetas `FREQUENCY` e `IMPEDANCE = (...)`; el parser debe probarse con archivos de salida reales antes de utilizar regex como protocolo estable. Conservar siempre la salida original para auditoría.

La referencia cruzada con NEC2 aún **no está realizada**. Una futura prueba reproducible debe usar geometría y frecuencia comunes, configuraciones equivalentes de suelo, convergencia de segmentación y tolerancias predefinidas.

## 6. Ejemplo de patrón de radiación

```powershell
.\mininec.exe -f 14.2 -w 1,21,-5,0,6,5,0,6,0.001 --excitation-pulse=10 --theta=0,5,37 --phi=0,5,73 > patron_dipolo.txt
```

Aquí `theta` recorre 0° a 180° en incrementos de 5° (37 puntos), y `phi` de 0° a 360° (73 puntos). El último azimut coincide geométricamente con el primero; ambos pueden aparecer en la tabla.

## 7. Barrido de frecuencias

Se puede pedir un barrido directamente al motor:

```powershell
.\mininec.exe -f 7 -w 1,21,-5,0,6,5,0,6,0.001 --excitation-pulse=10 --frequency-increment=0.1 --frequency-steps=11 > barrido.txt
```

La opción `-f` fija el comienzo; `--frequency-increment` y `--frequency-steps` gobiernan el barrido. Comprueba las frecuencias efectivamente enumeradas en la salida antes de utilizar los resultados en un estudio.

También puedes automatizarlo externamente desde PowerShell, guardando **un archivo por frecuencia**:

```powershell
foreach ($f in @(7.0, 7.1, 7.2)) {
    & .\mininec.exe -f $f -w "1,21,-5,0,6,5,0,6,0.001" --excitation-pulse=10 > ("resultado_{0}.txt" -f $f)
}
```

No se ha incluido aún un exportador CSV estructurado ni un adaptador de archivos NEC2.

## 8. Uso desde un archivo BAT

Guarda este texto como `ejecutar_dipolo.bat` junto a `mininec.exe`:

```bat
@echo off
cd /d "%~dp0"
mininec.exe -f 14.2 -w 1,21,-5,0,6,5,0,6,0.001 --excitation-pulse=10 --theta=0,5,37 --phi=0,5,73 > resultado_dipolo.txt
if errorlevel 1 (
  echo ERROR: no se completo la simulacion.
  pause
  exit /b 1
)
echo Resultado guardado en resultado_dipolo.txt
pause
```

Así se ejecuta el modelo con doble clic. **No** abras simplemente `mininec.exe` esperando una interfaz de ventanas.

## 9. Archivos de entrada y compatibilidad con NEC2

- **Entrada nativa actual**: argumentos de consola (`-f`, `-w`, `--excitation-pulse`, etc.). No se acepta directamente `modelo.nec`.
- **Salida nativa**: texto estándar, capturable con `> archivo.txt`.
- **Archivo `.pym` del proyecto original**: contiene argumentos de consola; para procesarlo en Windows se requiere un pequeño lanzador que lea el archivo, ignore comentarios y pase los argumentos al programa. **Esta distribución aún no implementa el uso directo `mininec.exe modelo.pym`**.
- **Conversión desde NEC2**: requiere traducir tarjetas `GW`, `EX`, `FR`, parámetros de suelo y demás ajustes. No basta con cambiar la extensión.
- **Referencia de 50 ohmios**: la impedancia calculada corresponde al punto de alimentación; si necesitas ROE o pérdidas por desadaptación respecto de 50 Ω, debes calcularlas a partir de esa impedancia o agregar un postprocesador. No confundir referencia de 50 Ω con una impedancia de entrada impuesta.

## 10. Advertencias físicas

La selección del suelo importa y **no debe suponerse que los resultados con suelo predeterminado equivalen al suelo real de NEC2**. Consulta `--help` y la documentación original para escoger explícitamente el modelo de tierra antes de hacer comparaciones. Comprueba que las longitudes de segmento sean suficientemente pequeñas para la frecuencia de interés y que el radio físico sea coherente. Geometrías muy pequeñas, lazos con grandes pérdidas, puntos de alimentación en uniones y conductores próximos al terreno merecen especial cuidado.

**MININEC/PyMININEC no es idéntico a NEC2 y tampoco equivale automáticamente al motor modificado de MMANA-GAL.**

## 11. Compilar desde el código

Windows + Python 3.12 + Git:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m PyInstaller --clean --onefile --console --name mininec src/mininec_cli.py
.\.venv\Scripts\python.exe tests/smoke.py dist/mininec.exe
```

El workflow usa una revisión fijada del proyecto original: `3b0b3b836f0c785c30a6d78bf30028b8eff88c5b` (2025-07-28). El smoke test solo comprueba que arranque y que presente la ayuda. **No certifica la exactitud electromagnética**.

## 12. Autoría, licencia y referencias

- **Motor original:** [PyMININEC, Ralf Schlatterbeck](https://github.com/schlatterbeck/pymininec), licencia MIT.
- **Documentación completa de las opciones:** [README original](https://github.com/schlatterbeck/pymininec/blob/master/README.rst).
- **Esta distribución Windows:** proyecto comunitario de empaquetado, sin atribuirse autoría del motor.
- Licencias y avisos: [LICENSE](LICENSE), [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
