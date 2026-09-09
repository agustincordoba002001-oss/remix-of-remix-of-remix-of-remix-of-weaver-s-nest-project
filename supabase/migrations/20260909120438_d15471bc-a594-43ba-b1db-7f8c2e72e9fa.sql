CREATE POLICY "Project services manage video projects"
ON public.video_projects
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);