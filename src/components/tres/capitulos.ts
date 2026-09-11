// Guion de la prueba de 30 segundos: cada capítulo tiene su posición de cámara y su rótulo.

export type Capitulo = {
  t: number;
  titulo: string;
  bajada: string;
  camara: [number, number, number];
  mira: [number, number, number];
};

export const DURACION = 30;

export const CAPITULOS: Capitulo[] = [
  {
    t: 0,
    titulo: "11 DE SEPTIEMBRE",
    bajada: "Amanece sobre Nueva York",
    camara: [0, 6, 46],
    mira: [0, 10, 0],
  },
  {
    t: 6,
    titulo: "UNA MAÑANA CUALQUIERA",
    bajada: "Martes, 6:00 a.m. · la ciudad se enciende",
    camara: [24, 9, 26],
    mira: [0, 12, 0],
  },
  {
    t: 12,
    titulo: "CUATRO VUELOS DE RUTINA",
    bajada: "Boston · Newark · Washington",
    camara: [-26, 22, 24],
    mira: [0, 16, 0],
  },
  {
    t: 18,
    titulo: "8:14 A.M. · FUERA DE RUTA",
    bajada: "El radar pierde al vuelo 11",
    camara: [-6, 30, 20],
    mira: [-2, 18, -6],
  },
  {
    t: 23,
    titulo: "110 PISOS SOBRE MANHATTAN",
    bajada: "50.000 personas empiezan su día",
    camara: [5, 12, 13],
    mira: [0, 20, 0],
  },
  {
    t: 27,
    titulo: "EN MEMORIA",
    bajada: "La historia completa, minuto a minuto",
    camara: [0, 14, 34],
    mira: [0, 24, 0],
  },
];

export function capituloEn(t: number) {
  let i = 0;
  for (let k = 0; k < CAPITULOS.length; k++) {
    const c = CAPITULOS[k];
    if (c && t >= c.t) i = k;
  }
  return i;
}
