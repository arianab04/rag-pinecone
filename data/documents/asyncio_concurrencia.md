# Concurrencia con asyncio

## Corrutinas y event loop

Una función declarada con `async def` es una corrutina: llamarla no ejecuta
el cuerpo, devuelve un objeto que hay que esperar. El `await` cede el control
al event loop, que aprovecha esa pausa para avanzar otras tareas.

```python
import asyncio

async def descargar(url):
    await asyncio.sleep(1)
    return url

asyncio.run(descargar("https://ejemplo.com"))
```

`asyncio.run` crea el loop, corre la corrutina y cierra todo. No debe
llamarse desde adentro de un loop ya corriendo, como un notebook de Jupyter:
ahí se usa `await` directamente.

## gather para paralelizar

`asyncio.gather` lanza varias corrutinas a la vez y espera a todas. Es la
diferencia entre tres segundos y uno.

```python
resultados = await asyncio.gather(
    descargar("a"), descargar("b"), descargar("c")
)
```

Los resultados vuelven en el orden en que se pasaron, no en el que
terminaron. Con `return_exceptions=True` los errores se devuelven como parte
de la lista en lugar de cancelar el conjunto.

## TaskGroup

Desde Python 3.11, `asyncio.TaskGroup` es la forma recomendada de lanzar
tareas concurrentes. A diferencia de `gather`, si una tarea falla el grupo
cancela las demás y propaga la excepción, lo que evita tareas huérfanas.

```python
async with asyncio.TaskGroup() as tg:
    tg.create_task(descargar("a"))
    tg.create_task(descargar("b"))
```

## Concurrencia no es paralelismo

asyncio corre en un solo hilo. Sirve para trabajo limitado por entrada y
salida: llamadas HTTP, consultas a base de datos, lectura de archivos. No
acelera cálculo intensivo, porque no hay otro núcleo trabajando. Para eso va
`ProcessPoolExecutor`. Meter un cálculo pesado dentro de una corrutina
bloquea el loop y congela todas las demás tareas.

## Código bloqueante dentro de async

Llamar una librería sincrónica desde una corrutina bloquea el loop entero. La
salida es delegarla a un hilo con `asyncio.to_thread`.

```python
datos = await asyncio.to_thread(funcion_bloqueante, argumento)
```

## Timeouts y cancelación

`asyncio.timeout` establece un límite y cancela la operación si se excede.
La cancelación se implementa lanzando `CancelledError` dentro de la corrutina;
capturarla y no relanzarla rompe el mecanismo de cancelación, así que si hay
que limpiar recursos conviene hacerlo en un `finally`.

## Semáforos para limitar la carga

Lanzar mil requests simultáneos con `gather` satura la red o hace que la API
remota devuelva 429. Un `asyncio.Semaphore` acota cuántas corren a la vez.

```python
sem = asyncio.Semaphore(10)

async def limitado(url):
    async with sem:
        return await descargar(url)
```
