// Contenido del carrusel: una ilustración por diapositiva (1376 × 768, WebP).
// El encuadre (object-position) mantiene a la vista al campesino y al satélite
// cuando la tarjeta de móvil recorta los lados de la imagen.

export interface Diapositiva {
  titulo: string;
  subtitulo: string;
  imagen: string;
  alt: string;
  encuadre: string;
}

export const DIAPOSITIVAS: Diapositiva[] = [
  {
    titulo: 'Tu finca, vista desde el espacio',
    subtitulo: 'Te ayudamos a decidir qué sembrar, cuándo y con cuánta agua.',
    imagen: '/img/bienvenida-1-finca-desde-el-espacio.webp',
    alt: 'Un satélite escanea las terrazas de cultivo de las montañas del Huila al amanecer mientras un campesino mira su finca.',
    encuadre: '80% 50%',
  },
  {
    titulo: 'Riega solo lo que tu cultivo necesita',
    subtitulo: 'Medimos la humedad de tu tierra con satélites de la NASA.',
    imagen: '/img/bienvenida-2-riego.webp',
    alt: 'Un campesino abre la válvula del riego por goteo de su maizal mientras un satélite mide la humedad del suelo.',
    encuadre: '80% 50%',
  },
  {
    titulo: 'Siembra en la fecha con menos riesgo',
    subtitulo: 'Usamos 45 años de clima para recomendarte cuándo sembrar.',
    imagen: '/img/bienvenida-3-siembra.webp',
    alt: 'Un campesino sonriente sostiene una canasta con mazorcas y verduras recién cosechadas entre su maizal.',
    encuadre: '80% 50%',
  },
];
