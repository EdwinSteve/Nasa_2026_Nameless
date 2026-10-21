// src/lib/fechas.ts
// Saludo, fechas y números en español de Colombia. Nada fijo: todo sale de la fecha que se pase.

const fechaLarga = new Intl.DateTimeFormat('es-CO', { weekday: 'long', day: 'numeric', month: 'long' });
const fechaCorta = new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'short', timeZone: 'UTC' });
const fechaDiaMes = new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'long', timeZone: 'UTC' });
const mesCorto = new Intl.DateTimeFormat('es-CO', { month: 'short', timeZone: 'UTC' });
const mesLargo = new Intl.DateTimeFormat('es-CO', { month: 'long', timeZone: 'UTC' });
const mesLargoAnio = new Intl.DateTimeFormat('es-CO', { month: 'long', year: 'numeric', timeZone: 'UTC' });
const entero = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 });
const unDecimal = new Intl.NumberFormat('es-CO', { minimumFractionDigits: 1, maximumFractionDigits: 1 });

/** "Buenos días" de 5:00 a 11:59, "Buenas tardes" hasta las 18:59, "Buenas noches" el resto. */
export function saludo(fecha: Date): string {
  const hora = fecha.getHours();
  if (hora >= 5 && hora < 12) return 'Buenos días';
  if (hora >= 12 && hora < 19) return 'Buenas tardes';
  return 'Buenas noches';
}

/** "miércoles, 14 de octubre" */
export function formatearFechaLarga(fecha: Date): string {
  return fechaLarga.format(fecha);
}

/** Una fecha ISO (AAAA-MM-DD) del backend como día UTC, sin que la zona horaria la corra un día. */
function deIso(iso: string): Date {
  return new Date(`${iso.slice(0, 10)}T00:00:00Z`);
}

/** "12 oct". Se arma con las partes: según el entorno, Intl da "12 oct" o "12 de oct". */
export function formatearFechaCorta(iso: string): string {
  const partes = fechaCorta.formatToParts(deIso(iso));
  const dia = partes.find((p) => p.type === 'day')?.value ?? '';
  const mes = (partes.find((p) => p.type === 'month')?.value ?? '').replace('.', '');
  return `${dia} ${mes}`.trim();
}

/** "20 de enero" */
export function formatearDiaMes(iso: string): string {
  return fechaDiaMes.format(deIso(iso));
}

/** "2026-05" → "May" */
export function formatearMesCorto(mes: string): string {
  const texto = mesCorto.format(deIso(`${mes}-01`)).replace('.', '');
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

/** "2026-05" → "Mayo" */
export function formatearMesLargo(mes: string): string {
  const texto = mesLargo.format(deIso(`${mes}-01`));
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

/** "2026-05" → "mayo de 2026" */
export function formatearMesAnio(mes: string): string {
  return mesLargoAnio.format(deIso(`${mes}-01`));
}

/** 1840 → "1.840" */
export function formatearEntero(valor: number): string {
  return entero.format(valor);
}

/** 6.4 → "6,4" */
export function formatearUnDecimal(valor: number): string {
  return unDecimal.format(valor);
}
