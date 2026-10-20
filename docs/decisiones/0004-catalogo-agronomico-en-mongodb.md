# 0004: Catálogo agronómico en MongoDB

- Estado: propuesta (en uso desde 2026-10-17)
- Fecha: 2026-10-20

## Contexto
El catálogo de requerimientos por cultivo (`surco_agro`) es información de referencia, de solo lectura y con estructura variable: perennes, musáceas y granos tienen fases distintas, de 3 a 6 por cultivo. Hasta ahora la arquitectura solo tenía PostgreSQL.

## Decisión
- Guardar el catálogo en MongoDB, base `surco_agro`, con las fases embebidas en cada cultivo y validadores `$jsonSchema` en modo estricto.
- Solo el módulo `motor_agronomico` lee `surco_agro`. Usuarios, lotes y planes siguen en PostgreSQL.
- El catálogo se versiona con el campo `version` de cada documento, y los JSON de [data/catalogo_cultivos_mongodb/datos/](../../data/catalogo_cultivos_mongodb/datos/) son la fuente de verdad.
- El entrenamiento del modelo lee los JSON directamente y no necesita Mongo.

**Alternativa descartada:** guardar el catálogo como `jsonb` en PostgreSQL. Evita un componente más, pero hace más difícil validar y consultar las fases.

## Consecuencias
- Un cultivo completo se trae en una sola lectura.
- Hay un servicio más que desplegar y mantener.
- Cada máquina con una base local tiene que recargarla cuando cambian los JSON (`scripts/01_crear_base.js` y `scripts/02_cargar_datos.js`, que se pueden repetir sin duplicar).
