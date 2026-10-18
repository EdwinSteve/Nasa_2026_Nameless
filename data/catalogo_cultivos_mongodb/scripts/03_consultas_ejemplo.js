// Consultas de ejemplo para el modelo predictivo.
// Uso: mongosh "mongodb://localhost:27017/surco_agro" scripts/03_consultas_ejemplo.js
const agro = db.getSiblingDB('surco_agro');

// 1. Requerimientos de la floración del maíz
printjson(agro.cultivos.aggregate([
  { $match: { _id: 'maiz' } },
  { $unwind: '$fases' },
  { $match: { 'fases.codigo': 'floracion' } },
  { $project: { _id: 0, cultivo: '$nombre', fase: '$fases' } },
]).toArray());

// 2. Cultivos posibles para un lote del valle de Neiva (450 msnm, pH 6,2, T media 27,5 °C)
const lote = { altitud: 450, ph: 6.2, tMedia: 27.5 };
printjson(agro.cultivos.find(
  {
    'zona_produccion.altitud_msnm.min': { $lte: lote.altitud },
    'zona_produccion.altitud_msnm.max': { $gte: lote.altitud },
    'requerimientos_cultivo.suelo.ph.min_absoluto': { $lte: lote.ph },
    'requerimientos_cultivo.suelo.ph.max_absoluto': { $gte: lote.ph },
    'requerimientos_cultivo.temperatura_aire_C.min_absoluto': { $lte: lote.tMedia },
    'requerimientos_cultivo.temperatura_aire_C.max_absoluto': { $gte: lote.tMedia },
  },
  { nombre: 1, grupo: 1, 'requerimientos_cultivo.temperatura_aire_C': 1 }
).toArray());

// 3. Leguminosas o abonos verdes que aportan nitrógeno a esa altitud (para la rotación)
printjson(agro.cultivos.find(
  {
    'rotacion.aporta_nitrogeno': true,
    'zona_produccion.altitud_msnm.min': { $lte: lote.altitud },
    'zona_produccion.altitud_msnm.max': { $gte: lote.altitud },
  },
  { nombre: 1, 'nitrogeno.fijacion_biologica_kg_ha': 1 }
).toArray());

// 4. Fases que toleran un pronóstico de 2 mm/día de lluvia sin riego
printjson(agro.cultivos.aggregate([
  { $unwind: '$fases' },
  { $match: { 'fases.precipitacion_mm_dia.optimo_min': { $lte: 2 } } },
  { $project: { _id: 0, cultivo: '$nombre', fase: '$fases.nombre', mm_dia: '$fases.precipitacion_mm_dia' } },
  { $limit: 20 },
]).toArray());

// 5. Cultivo con sus variedades
printjson(agro.cultivos.aggregate([
  { $match: { _id: 'cafe' } },
  { $lookup: { from: 'variedades', localField: '_id', foreignField: 'cultivo_id', as: 'variedades' } },
  { $project: { nombre: 1, 'variedades.nombre': 1, 'variedades.obtentor': 1 } },
]).toArray());
