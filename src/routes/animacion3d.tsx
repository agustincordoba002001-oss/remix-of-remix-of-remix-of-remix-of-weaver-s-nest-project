import { Canvas } from "@react-three/fiber";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";

import { CAPITULOS } from "@/components/tres/capitulos";
import { Escena11S } from "@/components/tres/Escena11S";

export const Route = createFileRoute("/animacion3d")({
  ssr: false,
  head: () => ({
    meta: [
      { title: "11 de septiembre en 3D | Animación de la historia completa" },
      {
        name: "description",
        content:
          "Prueba de animación 3D a pantalla completa: el amanecer sobre Nueva York, los cuatro vuelos y el memorial, narrado con rótulos.",
      },
      { property: "og:title", content: "11 de septiembre en 3D" },
      {
        property: "og:description",
        content: "Animación 3D a pantalla completa que cuenta la historia con coherencia.",
      },
      { property: "og:type", content: "video.other" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Animacion3D,
});

function Animacion3D() {
  const [indice, setIndice] = useState(0);
  const capitulo = CAPITULOS[indice] ?? CAPITULOS[0];

  return (
    <main className="fixed inset-0 overflow-hidden bg-[#0d1626]">
      <h1 className="sr-only">11 de septiembre: animación 3D de la historia completa</h1>

      <Canvas
        shadows
        dpr={[1, 2]}
        camera={{ position: [0, 6, 46], fov: 52, near: 0.1, far: 400 }}
        gl={{ antialias: true }}
      >
        <Escena11S onCapitulo={setIndice} />
      </Canvas>

      <div className="pointer-events-none absolute inset-0 flex flex-col justify-between p-6 sm:p-12">
        <div key={indice} className="animate-fade-in max-w-3xl">
          <p className="text-[11px] uppercase tracking-[0.4em] text-amber-200/70">
            Animación 3D · prueba de 30 segundos
          </p>
          <h2 className="mt-3 text-4xl font-black uppercase leading-[0.95] tracking-tight text-white drop-shadow-[0_4px_18px_rgba(0,0,0,0.7)] sm:text-6xl">
            {capitulo?.titulo}
          </h2>
          <p className="mt-3 text-base font-medium uppercase tracking-wide text-amber-300 sm:text-xl">
            {capitulo?.bajada}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {CAPITULOS.map((c, i) => (
            <span
              key={c.t}
              className={`h-1 flex-1 rounded-full transition-[background-color] ${
                i <= indice ? "bg-amber-300" : "bg-white/20"
              }`}
            />
          ))}
        </div>
      </div>
    </main>
  );
}
