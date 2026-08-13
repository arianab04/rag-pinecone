# Inyección de dependencias en FastAPI

## El sistema Depends

FastAPI resuelve dependencias declarativamente con `Depends`. Una dependencia
es cualquier callable que FastAPI ejecuta antes del endpoint, inyectando su
resultado como parámetro.

```python
from fastapi import Depends, FastAPI

def parametros_paginacion(skip: int = 0, limit: int = 20):
    return {"skip": skip, "limit": limit}

@app.get("/items")
def listar(paginacion: dict = Depends(parametros_paginacion)):
    return consultar(**paginacion)
```

La ventaja frente a llamar la función a mano es que FastAPI conoce la firma
de la dependencia y la incorpora al esquema OpenAPI: los parámetros `skip` y
`limit` aparecen documentados automáticamente en `/docs`.

## Dependencias con yield

Igual que las fixtures de pytest, una dependencia puede usar `yield` para
ejecutar código de limpieza después de que la respuesta fue enviada. Es el
patrón estándar para manejar sesiones de base de datos.

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

El bloque `finally` garantiza que la sesión se cierre incluso si el endpoint
lanza una excepción.

## Sub-dependencias

Una dependencia puede depender de otra, formando un grafo. FastAPI lo resuelve
en orden y cachea el resultado dentro de una misma request: si tres
dependencias distintas requieren `get_current_user`, se ejecuta una sola vez.
Ese caché se puede desactivar con `Depends(funcion, use_cache=False)` cuando
se necesita reevaluar.

## Seguridad y autenticación

Los esquemas de seguridad se implementan como dependencias. `OAuth2PasswordBearer`
extrae el token del encabezado `Authorization`, y una dependencia propia lo
decodifica y busca el usuario.

```python
async def usuario_actual(token: str = Depends(oauth2_scheme)):
    payload = decodificar(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido")
    return buscar_usuario(payload["sub"])
```

Aplicar esa dependencia a un router completo mediante
`APIRouter(dependencies=[Depends(usuario_actual)])` protege todos sus
endpoints sin repetir el parámetro en cada firma.

## Modelos de request y response

FastAPI usa Pydantic para validar el cuerpo de la petición. Declarar un
parámetro con tipo `BaseModel` hace que el JSON entrante se valide antes de
entrar al endpoint; si falla, el cliente recibe un 422 con el detalle exacto.
El argumento `response_model` filtra la salida: aunque la función devuelva un
objeto con más campos, solo se serializan los declarados en el modelo. Es la
forma correcta de evitar que un hash de contraseña se filtre en una respuesta.

## Endpoints async y sincrónicos

Un endpoint declarado con `async def` corre en el event loop; uno declarado
con `def` común corre en un threadpool para no bloquearlo. El error clásico
es declarar `async def` y adentro llamar una librería bloqueante como
`requests` o un driver de base de datos sincrónico: eso congela el loop
entero y tira la concurrencia del servidor al piso. Si la librería es
bloqueante, conviene el `def` normal.
