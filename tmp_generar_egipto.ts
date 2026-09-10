/**
 * Generador one-off del guion del documental "EL IMPERIO EGIPCIO".
 * Usa hechos gratis de la enciclopedia libre + el narrador propio del proyecto.
 */
import { writeFile } from "node:fs/promises";
import { wikipedia } from "./src/lib/hechos.ts";
import { escribirGuion, type Guion } from "./src/lib/narrador.ts";
import { AJUSTES_BASE } from "./src/lib/ajustes.ts";

const TEMAS = [
  "Antiguo Egipto",
  "Pirámides de Egipto",
  "Faraón",
  "Reino Nuevo de Egipto",
  "Cleopatra",
  "Ramsés II",
  "Tutankamón",
];

const TITULOS_EGIPTO = [
  /\begipto/i,
  /\begipcio/i,
  /\begipcia/i,
  /\bfara[óo]n/i,
  /\bpir[aá]mide/i,
  /\bnilo/i,
  /\bkarnak/i,
  /\bluxor/i,
  /\bmemphis/i,
  /\btebas/i,
  /\bgiza/i,
  /\bguiza/i,
  /\bsaqqara/i,
  /\bsakkara/i,
  /\bmomia/i,
  /\bjerogl[ií]fico/i,
  /\bsarc[óo]fago/i,
  /\bimhotep/i,
  /\bkeops/i,
  /\bkefren/i,
  /\bmicerino/i,
  /\btutankam[óo]n/i,
  /\brams[eé]s/i,
  /\bhatshepsut/i,
  /\bcleopatra/i,
  /\bptolomeo/i,
  /\banubis/i,
  /\bosiris/i,
  /\bhorus/i,
  /\bisis\b/i,
  /\bam[óo]n/i,
  /\baten/i,
  /\bakh?enat[óo]n/i,
  /\bnefertiti/i,
];

function esEgipto(titulo: string): boolean {
  return TITULOS_EGIPTO.some((r) => r.test(titulo));
}

async function main() {
  const todo: { titulo: string; relato: string[] }[] = [];
  for (const tema of TEMAS) {
    console.log("Buscando:", tema);
    const arts = await wikipedia(tema);
    for (const a of arts) {
      if (!esEgipto(a.titulo)) {
        console.log("  descartado:", a.titulo);
        continue;
      }
      if (!todo.some((x) => x.titulo === a.titulo)) {
        todo.push(a);
      }
    }
  }

  const hechos = todo.flatMap((c, i) => (i === 0 ? c.relato : c.relato.slice(0, 35)));
  console.log("Artículos:", todo.length, "Hechos:", hechos.length);

  const ajustes = {
    ...AJUSTES_BASE,
    drama: 2,
    datos: 2,
    preguntas: 2,
    frasesCortas: 1,
    minutosExtra: 3,
    priorizar: [
      "pirámide",
      "faraón",
      "momia",
      "jeroglífico",
      "construcción",
      "dios",
      "tumba",
      "reino",
      "Nilo",
      "imperio",
      "batalla",
      "curiosidad",
    ],
    evitar: [
      "cine",
      "película",
      "videojuego",
      "novela",
      "recaudación",
      "taquilla",
      "egiptólogo",
      "egiptología",
    ],
  };

  const guion = escribirGuion("EL IMPERIO EGIPCIO", hechos, 22, ajustes);
  console.log("Escenas:", guion.escenas.length, "Palabras:", guion.palabras, "Min:", guion.minutos);

  const payload = {
    titulo: guion.titulo,
    palabras: guion.palabras,
    minutos: guion.minutos,
    escenas: guion.escenas,
    fuentes: todo.map((t) => t.titulo),
  };

  await writeFile("animacion-luna/guion_egipto.json", JSON.stringify(payload, null, 2));
  console.log("Guardado en animacion-luna/guion_egipto.json");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
