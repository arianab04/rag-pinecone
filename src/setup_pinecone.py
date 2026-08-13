import os

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec


# 1. Cargar las variables del archivo .env
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("INDEX_NAME")


# 2. Verificar que las variables necesarias existan
if not PINECONE_API_KEY:
    raise ValueError("No se encontró PINECONE_API_KEY en el archivo .env")

if not INDEX_NAME:
    raise ValueError("No se encontró INDEX_NAME en el archivo .env")


# 3. Conectarnos a Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)


# 4. Verificar si el índice ya existe
if not pc.has_index(INDEX_NAME):

    print(f"El índice '{INDEX_NAME}' no existe. Creándolo...")

    pc.create_index(
        name=INDEX_NAME,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        ),
        deletion_protection="disabled"
    )

    print(f"Índice '{INDEX_NAME}' creado.")

else:

    print(f"El índice '{INDEX_NAME}' ya existe.")


# 5. Mostrar información del índice
index_info = pc.describe_index(INDEX_NAME)

print("\nInformación del índice:")
print(index_info)