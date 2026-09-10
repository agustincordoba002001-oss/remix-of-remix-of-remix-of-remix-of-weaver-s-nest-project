import { createFileRoute } from "@tanstack/react-router";

/**
 * Entrega el audio ya terminado de una narración guardada, para poder
 * escucharlo y editarlo frase por frase en el editor. Soporta adelantar y
 * atrasar (Range) para que el reproductor no tenga que bajar todo el archivo.
 */
export const Route = createFileRoute("/api/public/narracion/$id")({
  server: {
    handlers: {
      GET: async ({ params, request }) => {
        const id = String(params.id ?? "").replace(/[^a-zA-Z0-9_-]/g, "");
        if (!id) return new Response("id inválido", { status: 400 });

        const { stat, open } = await import("node:fs/promises");
        const ruta = `/mnt/documents/${id}/full.wav`;
        let total: number;
        try {
          total = (await stat(ruta)).size;
        } catch {
          return new Response("no encontré esa narración", { status: 404 });
        }

        const rango = request.headers.get("range");
        const base = {
          "Content-Type": "audio/wav",
          "Accept-Ranges": "bytes",
          "Cache-Control": "no-store",
        };

        const fd = await open(ruta, "r");
        try {
          if (!rango) {
            const buf = Buffer.alloc(Math.min(total, 1_500_000));
            await fd.read(buf, 0, buf.length, 0);
            // Sin Range devolvemos solo el comienzo y avisamos el largo real.
            return new Response(buf, {
              status: 206,
              headers: {
                ...base,
                "Content-Range": `bytes 0-${buf.length - 1}/${total}`,
                "Content-Length": String(buf.length),
              },
            });
          }
          const m = /bytes=(\d*)-(\d*)/.exec(rango);
          const desde = m?.[1] ? Number(m[1]) : 0;
          const hasta = Math.min(
            m?.[2] ? Number(m[2]) : desde + 4_000_000 - 1,
            total - 1,
          );
          if (desde >= total || hasta < desde) {
            return new Response("rango inválido", {
              status: 416,
              headers: { "Content-Range": `bytes */${total}` },
            });
          }
          const largo = hasta - desde + 1;
          const buf = Buffer.alloc(largo);
          await fd.read(buf, 0, largo, desde);
          return new Response(buf, {
            status: 206,
            headers: {
              ...base,
              "Content-Range": `bytes ${desde}-${hasta}/${total}`,
              "Content-Length": String(largo),
            },
          });
        } finally {
          await fd.close();
        }
      },
    },
  },
});
