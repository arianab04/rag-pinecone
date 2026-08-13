# Fixtures en pytest

## Qué es una fixture

Una fixture es una función que prepara el estado necesario para que un test
pueda ejecutarse. Se declara con el decorador `@pytest.fixture` y se consume
declarando su nombre como parámetro del test. pytest resuelve la dependencia
por nombre: no hay que importarla ni instanciarla manualmente.

```python
import pytest

@pytest.fixture
def usuario():
    return {"nombre": "Ariana", "activo": True}

def test_usuario_activo(usuario):
    assert usuario["activo"] is True
```

## Setup y teardown con yield

Cuando una fixture necesita limpiar recursos después del test, se reemplaza
el `return` por un `yield`. Todo lo que está antes del `yield` es el setup;
todo lo que está después es el teardown, y pytest lo ejecuta aunque el test
haya fallado.

```python
@pytest.fixture
def conexion_db():
    conexion = abrir_conexion()
    yield conexion
    conexion.close()
```

Este patrón es el equivalente moderno de los viejos métodos `setUp` y
`tearDown` de unittest, pero con una ventaja importante: la fixture es
componible y se puede reutilizar en cualquier test del proyecto sin herencia
de clases.

## Scope: cuántas veces se ejecuta

El parámetro `scope` controla el ciclo de vida de la fixture. Los valores
posibles son `function` (el default, se recrea en cada test), `class`,
`module`, `package` y `session` (se crea una sola vez para toda la corrida).

```python
@pytest.fixture(scope="session")
def motor_db():
    return crear_motor()
```

Elegir bien el scope es la principal palanca de performance en una suite
lenta. Levantar un contenedor de base de datos por cada test es carísimo;
con `scope="session"` se levanta una sola vez. La contrapartida es el
aislamiento: si un test muta el estado compartido, contamina a los que
siguen. La regla práctica es usar `session` para recursos caros e inmutables
y `function` para todo lo que se modifica.

## conftest.py

Las fixtures definidas en un archivo `conftest.py` quedan disponibles para
todos los tests del directorio y sus subdirectorios, sin necesidad de
importarlas. Es el lugar canónico para las fixtures compartidas y para los
hooks de configuración de la suite. Puede haber varios `conftest.py`
anidados: pytest los combina de la raíz hacia adentro.

## Parametrización

`@pytest.mark.parametrize` ejecuta el mismo test con distintos juegos de
datos, generando un caso independiente por cada tupla. Un fallo en una
combinación no impide que se ejecuten las demás.

```python
@pytest.mark.parametrize("entrada,esperado", [
    ("2+2", 4),
    ("3*3", 9),
])
def test_calculadora(entrada, esperado):
    assert evaluar(entrada) == esperado
```

También se puede parametrizar la fixture misma con el argumento `params`,
lo que multiplica automáticamente todos los tests que la consumen. Es útil
para correr la misma suite contra varios motores de base de datos.

## Fixtures incorporadas

pytest trae fixtures listas para usar. `tmp_path` entrega un directorio
temporal único por test, `monkeypatch` permite modificar variables de entorno
y atributos de forma reversible, `capsys` captura la salida estándar y
`caplog` los registros de logging. Usarlas evita escribir código de limpieza
propenso a errores.
