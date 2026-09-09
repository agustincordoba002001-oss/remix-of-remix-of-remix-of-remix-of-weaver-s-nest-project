CREATE TABLE public.video_projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  storage_path TEXT NOT NULL UNIQUE,
  mime_type TEXT NOT NULL,
  size_bytes BIGINT NOT NULL CHECK (size_bytes > 0),
  duration_seconds DOUBLE PRECISION,
  transcript JSONB NOT NULL DEFAULT '[]'::jsonb,
  status TEXT NOT NULL DEFAULT 'uploaded' CHECK (status IN ('uploading', 'uploaded', 'processing', 'ready', 'error')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
GRANT ALL ON public.video_projects TO service_role;
ALTER TABLE public.video_projects ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION public.set_video_projects_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = public
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

CREATE TRIGGER set_video_projects_updated_at
BEFORE UPDATE ON public.video_projects
FOR EACH ROW EXECUTE FUNCTION public.set_video_projects_updated_at();