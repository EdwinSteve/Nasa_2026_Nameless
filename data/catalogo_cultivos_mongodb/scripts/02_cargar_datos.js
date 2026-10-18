// Carga o actualiza los datos (idempotente: se puede ejecutar varias veces).
// Uso: mongosh "mongodb://localhost:27017" scripts/02_cargar_datos.js
const fs = require('fs');
const RAIZ = process.env.SURCO_AGRO_DIR || '.';
const agro = db.getSiblingDB('surco_agro');

for (const nombre of ['fuentes', 'metricas', 'cultivos', 'variedades']) {
  const documentos = JSON.parse(fs.readFileSync(`${RAIZ}/datos/${nombre}.json`, 'utf8'));
  const operaciones = documentos.map((doc) => ({
    replaceOne: { filter: { _id: doc._id }, replacement: doc, upsert: true },
  }));
  const r = agro[nombre].bulkWrite(operaciones, { ordered: false });
  print(`${nombre}: ${r.upsertedCount} nuevos, ${r.modifiedCount} actualizados`);
}
