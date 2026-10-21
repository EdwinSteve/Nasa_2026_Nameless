# 0005: Completar el catálogo con análogos solo si son de la misma familia

- Estado: aceptada
- Fecha: 2026-10-20

## Contexto
Doce cultivos del catálogo no tenían Kc, profundidad de raíz (Zr) ni agotamiento permitido (p), y sin ellos el oráculo no puede calcular su balance hídrico. FAO-56 no trae valores para la mayoría de los frutales tropicales y andinos.

## Decisión
- Un valor faltante se completa **solo** si hay en FAO-56 un cultivo de la **misma familia o género** con un hábito parecido.
- Los valores por fase se derivan con la misma regla que ya usa el catálogo.
- Cada valor queda registrado con su método, confianza y fuentes: `calidad_dato.parametros_agua` para Kc, Zr y p por análogo, y `calidad_dato.profundidad_raiz` para la Zr. El `version` del cultivo sube.
- Un valor medido en la literatura (aunque no esté en FAO-56) vale más que un análogo: se prefiere siempre.
- Si no hay un análogo defendible, el campo **se deja en `null`**: es mejor un dato faltante que un dato inventado.

Aplicado el 2026-10-20: arracacha, mora, lulo, uchuva y crotalaria tienen Kc, Zr y p por análogo. Ñame, mango, guayaba, papaya y maracuyá tienen Zr **medida** en estudios publicados; granadilla y tomate de árbol, Zr por analogía de **confianza baja**. A esos siete les faltan Kc y p. Detalle en la [sección 9 del README del catálogo](../../data/catalogo_cultivos_mongodb/README.md#9-valores-aproximados-por-análogo).

## Consecuencias
- El oráculo calcula el riego de 37 de los 44 cultivos (los 7 restantes ya tienen Zr, pero no Kc ni p). Los otros 7 se evalúan solo por clima hasta conseguir datos medidos (Embrapa, IITA, Agrosavia).
- Cualquier valor del catálogo se puede rastrear hasta su fuente, lo que sostiene el criterio de *Validity*.
