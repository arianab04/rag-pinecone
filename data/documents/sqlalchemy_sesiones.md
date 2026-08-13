# Sesiones y transacciones en SQLAlchemy

## Engine, Session y conexión

El `Engine` es el punto de entrada: administra el pool de conexiones y el
dialecto del motor de base de datos. Se crea una sola vez por aplicación,
porque instanciarlo repetidamente abre pools nuevos y agota las conexiones
del servidor.

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("postgresql+psycopg://user:pass@host/db", pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
```

`pool_pre_ping=True` verifica que la conexión siga viva antes de entregarla,
lo que evita el error de conexión cerrada por timeout del servidor.

## La unidad de trabajo

La `Session` implementa el patrón unit of work: acumula los cambios en
memoria y los envía a la base recién al hacer `commit()`. Mientras tanto
mantiene un mapa de identidad, de modo que consultar dos veces la misma fila
devuelve el mismo objeto Python.

```python
with SessionLocal() as session:
    usuario = Usuario(nombre="Ariana")
    session.add(usuario)
    session.commit()
```

Usar la sesión como context manager garantiza que se cierre. Si ocurre una
excepción antes del commit, la transacción queda abierta y hay que hacer
`rollback()`; el bloque `with` sumado a un `try/except` es la forma segura.

## Flush frente a commit

`flush()` emite el SQL pendiente pero no cierra la transacción: sirve para
obtener el ID autogenerado de una fila recién insertada y usarlo en la misma
unidad de trabajo. `commit()` hace un flush y además confirma. Un `commit`
por cada fila en un bucle de diez mil inserciones es el antipatrón de
performance más común: conviene un solo commit al final, o commits por lote.

## Carga perezosa y el problema N+1

Por defecto las relaciones se cargan de forma perezosa: acceder a
`pedido.items` dispara una consulta adicional. Recorrer cien pedidos y tocar
sus items genera ciento una consultas. La solución es carga anticipada con
`selectinload` o `joinedload`.

```python
from sqlalchemy.orm import selectinload

stmt = select(Pedido).options(selectinload(Pedido.items))
```

`selectinload` emite una segunda consulta con un `IN` y suele ser la mejor
opción para relaciones uno a muchos; `joinedload` resuelve todo en un JOIN
pero puede duplicar filas.

## DetachedInstanceError

Acceder a un atributo perezoso después de cerrar la sesión lanza
`DetachedInstanceError`, porque el objeto ya no tiene con qué consultar. Pasa
seguido al devolver entidades del ORM desde un endpoint. Las salidas son
cargar todo antes de cerrar, configurar
`expire_on_commit=False`, o convertir a un modelo Pydantic dentro del alcance
de la sesión, que además desacopla la capa de persistencia de la de
presentación.
