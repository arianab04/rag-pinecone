# Validación de datos con Pydantic

## El modelo como contrato

Pydantic convierte anotaciones de tipo de Python en validación en tiempo de
ejecución. Una clase que hereda de `BaseModel` declara qué campos espera y de
qué tipo; al instanciarla, Pydantic valida, convierte y falla con un error
descriptivo si los datos no encajan.

```python
from pydantic import BaseModel, EmailStr, Field

class Usuario(BaseModel):
    nombre: str
    email: EmailStr
    edad: int = Field(ge=0, le=120)
```

Si se pasa `edad="treinta"`, Pydantic lanza un `ValidationError` que indica
el campo exacto, el valor recibido y la regla incumplida. Ese error es
serializable a JSON, lo que lo hace ideal para devolver desde una API.

## Coerción de tipos

Por defecto Pydantic intenta convertir antes de rechazar: el string `"42"`
en un campo `int` se convierte a `42`. Este comportamiento, llamado modo lax,
es cómodo para procesar datos de formularios o variables de entorno. Cuando
se necesita rigor absoluto se activa el modo estricto con
`model_config = ConfigDict(strict=True)`, y entonces `"42"` es un error.

## Field y las restricciones

`Field` agrega metadatos y restricciones a un campo: valores por defecto,
descripciones, alias y límites. `ge` y `le` acotan números, `min_length` y
`max_length` acotan cadenas y listas, y `pattern` valida contra una expresión
regular.

El argumento `description` no es decorativo: es lo que aparece en el esquema
JSON generado por `model_json_schema()`, que a su vez alimenta la
documentación automática de FastAPI y las instrucciones de formato de un
`PydanticOutputParser` en LangChain.

## Validadores personalizados

Cuando la regla excede lo declarativo, se usan validadores. El decorador
`@field_validator` opera sobre un campo individual, después de que se validó
su tipo.

```python
from pydantic import field_validator

class Cuenta(BaseModel):
    cbu: str

    @field_validator("cbu")
    @classmethod
    def validar_cbu(cls, v: str) -> str:
        if len(v) != 22 or not v.isdigit():
            raise ValueError("El CBU debe tener 22 dígitos")
        return v
```

`@model_validator` opera sobre el modelo completo y sirve para reglas que
involucran varios campos, como verificar que una fecha de fin sea posterior
a la de inicio. Se ejecuta con `mode="after"` una vez validados los campos
individuales, o con `mode="before"` sobre los datos crudos.

## Serialización

`model_dump()` devuelve un diccionario de Python y `model_dump_json()` una
cadena JSON. Los argumentos `exclude`, `include` y `exclude_none` permiten
controlar qué se emite, algo importante cuando el modelo contiene campos
sensibles que no deben salir en una respuesta HTTP.

## Configuración desde el entorno

`pydantic-settings` extiende el modelo para que lea sus valores de variables
de entorno o de un archivo `.env`. Es la forma recomendada de manejar
credenciales: en lugar de esparcir llamadas a `os.getenv` por el código, se
declara una clase `Settings` que valida al arrancar y falla temprano si falta
una variable obligatoria.
