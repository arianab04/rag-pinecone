# Manipulación de datos con pandas

## Series y DataFrame

`Series` es un arreglo unidimensional con índice; `DataFrame` es una tabla
bidimensional donde cada columna es una `Series`. El índice no es un simple
número de fila: es una estructura que pandas usa para alinear operaciones
entre objetos. Sumar dos Series con índices distintos no concatena valores,
los alinea por etiqueta y produce `NaN` donde no hay correspondencia.

## Selección: loc frente a iloc

`loc` selecciona por etiqueta y `iloc` por posición entera. La confusión
entre ambos es la fuente número uno de errores en código con pandas.

```python
df.loc[3, "precio"]     # fila con etiqueta 3
df.iloc[3, 2]           # cuarta fila, tercera columna
```

Con `loc` los rangos son inclusivos en ambos extremos, a diferencia del
slicing normal de Python. `df.loc[2:5]` devuelve cuatro filas, no tres.

## El SettingWithCopyWarning

Encadenar indexaciones para asignar produce el temido
`SettingWithCopyWarning`, porque pandas no puede garantizar si está operando
sobre una vista o sobre una copia.

```python
df[df["edad"] > 30]["categoria"] = "senior"   # no confiable
df.loc[df["edad"] > 30, "categoria"] = "senior"  # correcto
```

La regla es asignar siempre en una sola operación con `loc`.

## groupby y agregación

`groupby` implementa el patrón split-apply-combine: parte el DataFrame según
una clave, aplica una función a cada grupo y recombina los resultados.

```python
df.groupby("sucursal")["monto"].agg(["sum", "mean", "count"])
```

`agg` acepta un diccionario para aplicar funciones distintas a columnas
distintas. `transform` devuelve un resultado del mismo tamaño que el original,
útil para calcular porcentajes sobre el total del grupo sin perder filas.

## merge y join

`merge` implementa los joins de SQL. El parámetro `how` acepta `inner`
(default), `left`, `right` y `outer`. Un error frecuente es no verificar la
cardinalidad: si la clave está duplicada en la tabla derecha, el resultado
tiene más filas que el original. El argumento `validate="one_to_one"` hace
que pandas falle explícitamente en ese caso en lugar de multiplicar filas en
silencio.

## Valores faltantes

`NaN` es el marcador de dato ausente. `isna()` los detecta, `fillna()` los
reemplaza y `dropna()` elimina las filas o columnas que los contienen.
Conviene distinguir entre un dato ausente y un cero: rellenar con `0` una
columna de precios cambia el promedio y sesga cualquier análisis posterior.

## Tipos y memoria

Las columnas de texto se guardan por defecto como `object`, que es una lista
de punteros a strings de Python y consume mucha memoria. Convertir una
columna de baja cardinalidad a `category` con `astype("category")` puede
reducir el uso de memoria en un orden de magnitud y acelerar los `groupby`.
Los enteros con faltantes requieren el tipo nullable `Int64` con I mayúscula,
porque el `int64` clásico de NumPy no admite `NaN`.
