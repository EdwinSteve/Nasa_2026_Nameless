// Crea la base surco_agro con validación de esquema e índices.
// Uso (desde la carpeta raíz del paquete):  mongosh "mongodb://localhost:27017" scripts/01_crear_base.js
const fs = require('fs');
const RAIZ = process.env.SURCO_AGRO_DIR || '.';
const leer = (ruta) => JSON.parse(fs.readFileSync(`${RAIZ}/${ruta}`, 'utf8'));
const agro = db.getSiblingDB('surco_agro');

for (const nombre of ['cultivos', 'variedades', 'metricas', 'fuentes']) {
  const validator = leer(`esquemas/${nombre}.schema.json`);
  const opciones = { validator, validationLevel: 'strict', validationAction: 'error' };
  if (agro.getCollectionNames().includes(nombre)) {
    agro.runCommand({ collMod: nombre, ...opciones });
    print(`Validador actualizado: ${nombre}`);
  } else {
    agro.createCollection(nombre, opciones);
    print(`Colección creada: ${nombre}`);
  }
}

agro.cultivos.createIndex({ grupo: 1, tipo_ciclo: 1 }, { name: 'ix_grupo_tipo' });
agro.cultivos.createIndex(
  { 'zona_produccion.altitud_msnm.min': 1, 'zona_produccion.altitud_msnm.max': 1 },
  { name: 'ix_altitud' }
);
agro.cultivos.createIndex({ 'fases.codigo': 1 }, { name: 'ix_fase_codigo' });
agro.cultivos.createIndex({ 'rotacion.aporta_nitrogeno': 1 }, { name: 'ix_aporta_n' });
agro.cultivos.createIndex(
  { nombre: 'text', nombre_cientifico: 'text' },
  { name: 'tx_nombre', default_language: 'spanish' }
);
agro.variedades.createIndex({ cultivo_id: 1 }, { name: 'ix_cultivo' });
print('Índices listos');
