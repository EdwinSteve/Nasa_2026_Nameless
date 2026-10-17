import os

# Valores seguros por defecto para que la configuración cargue en las pruebas.
# No pisan variables que el desarrollador ya tenga definidas.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://surco:surco@localhost:5432/surco")
os.environ.setdefault("JWT_SECRETO", "prueba-" + "x" * 64)
