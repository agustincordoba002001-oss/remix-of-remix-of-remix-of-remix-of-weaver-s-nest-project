import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";

const BUCKET = "project-videos";

const transcriptSchema = z.array(
  z.object({
    t0: z.number().min(0),
    t1: z.number().min(0),
    txt: z.string().max(2000),
  }),
);

export const prepararSubidaVideo = createServerFn({ method: "POST" })
  .inputValidator((input: unknown) =>
    z
      .object({
        name: z.string().min(1).max(240),
        type: z.string().startsWith("video/").max(100),
        size: z.number().int().positive().max(500 * 1024 * 1024),
      })
      .parse(input),
  )
  .handler(async ({ data }) => {
    const { supabaseAdmin } = await import("@/integrations/supabase/client.server");
    const extension = data.name.split(".").pop()?.toLowerCase().replace(/[^a-z0-9]/g, "") || "mp4";
    const id = crypto.randomUUID();
    const path = `${id}/original.${extension}`;
    const { data: signed, error } = await supabaseAdmin.storage.from(BUCKET).createSignedUploadUrl(path);
    if (error || !signed) throw new Error(error?.message || "No pude preparar la subida");

    const { error: insertError } = await supabaseAdmin.from("video_projects").insert({
      id,
      name: data.name,
      storage_path: path,
      mime_type: data.type,
      size_bytes: data.size,
      status: "uploading",
    });
    if (insertError) throw new Error(insertError.message);
    return { id, path, token: signed.token };
  });

export const confirmarSubidaVideo = createServerFn({ method: "POST" })
  .inputValidator((input: unknown) =>
    z.object({ id: z.string().uuid(), duration: z.number().min(0).max(100_000).nullish() }).parse(input),
  )
  .handler(async ({ data }) => {
    const { supabaseAdmin } = await import("@/integrations/supabase/client.server");
    const { error } = await supabaseAdmin
      .from("video_projects")
      .update({ status: "uploaded", duration_seconds: data.duration ?? null })
      .eq("id", data.id);
    if (error) throw new Error(error.message);
    return { ok: true };
  });

export const guardarGuionVideo = createServerFn({ method: "POST" })
  .inputValidator((input: unknown) =>
    z.object({ id: z.string().uuid(), transcript: transcriptSchema }).parse(input),
  )
  .handler(async ({ data }) => {
    const { supabaseAdmin } = await import("@/integrations/supabase/client.server");
    const { error } = await supabaseAdmin
      .from("video_projects")
      .update({ transcript: data.transcript, status: "ready" })
      .eq("id", data.id);
    if (error) throw new Error(error.message);
    return { ok: true };
  });

export const cargarUltimoVideo = createServerFn({ method: "GET" }).handler(async () => {
  const { supabaseAdmin } = await import("@/integrations/supabase/client.server");
  const { data, error } = await supabaseAdmin
    .from("video_projects")
    .select("id,name,storage_path,mime_type,size_bytes,duration_seconds,transcript,status")
    .in("status", ["uploaded", "processing", "ready"])
    .order("created_at", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (error) throw new Error(error.message);
  if (!data) return null;
  const { data: signed, error: signedError } = await supabaseAdmin.storage
    .from(BUCKET)
    .createSignedUrl(data.storage_path, 60 * 60 * 12);
  if (signedError || !signed) throw new Error(signedError?.message || "No pude abrir el video guardado");
  return { ...data, url: signed.signedUrl, transcript: transcriptSchema.parse(data.transcript) };
});