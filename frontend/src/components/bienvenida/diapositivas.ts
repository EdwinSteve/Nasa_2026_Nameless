// Contenido del carrusel: la misma imagen con distinto encuadre por diapositiva.
export const IMAGEN_BIENVENIDA = '/img/bienvenida-terrazas.jpg';
export const ALT_IMAGEN_BIENVENIDA =
  'Ilustración de terrazas de cultivo en las montañas del Huila al amanecer, con un campesino mirando su finca.';

export interface Diapositiva {
  titulo: string;
  subtitulo: string;
  encuadre: string; // object-position
}

export const DIAPOSITIVAS: Diapositiva[] = [
  { titulo: 'Tu finca, vista desde el espacio', subtitulo: 'Te ayudamos a decidir qué sembrar, cuándo y con cuánta agua.', encuadre: '50% 50%' },
  { titulo: 'Riega solo lo que tu cultivo necesita', subtitulo: 'Medimos la humedad de tu tierra con satélites de la NASA.', encuadre: '20% 50%' },
  { titulo: 'Siembra en la fecha con menos riesgo', subtitulo: 'Usamos 45 años de clima para recomendarte cuándo sembrar.', encuadre: '85% 50%' },
];
