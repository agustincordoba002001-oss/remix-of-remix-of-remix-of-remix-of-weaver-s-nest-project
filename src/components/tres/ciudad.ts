// Datos de la ciudad generados de forma determinista (misma ciudad en cada visita).

export type Edificio = {
  x: number;
  z: number;
  ancho: number;
  fondo: number;
  alto: number;
  tono: number;
};

function aleatorio(semilla: number) {
  let s = semilla;
  return () => {
    s = (s * 1664525 + 1013904223) % 4294967296;
    return s / 4294967296;
  };
}

export const TORRE_A: [number, number] = [-1.15, 0];
export const TORRE_B: [number, number] = [1.15, 0];
export const ALTO_TORRE = 26;

export function generarCiudad(): Edificio[] {
  const rnd = aleatorio(20010911);
  const lista: Edificio[] = [];
  for (let i = 0; i < 190; i++) {
    const x = (rnd() - 0.5) * 62;
    const z = (rnd() - 0.5) * 46;
    const distancia = Math.hypot(x, z);
    if (distancia < 3.2) continue;
    const cerca = Math.max(0, 1 - distancia / 26);
    const alto = 1.5 + rnd() * 7 + cerca * 11;
    lista.push({
      x,
      z,
      ancho: 1 + rnd() * 2.2,
      fondo: 1 + rnd() * 2.2,
      alto,
      tono: 0.55 + rnd() * 0.45,
    });
  }
  return lista;
}
