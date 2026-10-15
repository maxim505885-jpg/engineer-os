-- Stage 13: store only unverified source-bound asset candidates.
-- Applied to engineer-os Supabase on 2026-10-10; repeatable schema snapshot.
-- Existing validated evidence RPC is intentionally unchanged.
CREATE TABLE IF NOT EXISTS public.document_asset_candidates (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
 document_id uuid NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
 candidate_id text NOT NULL CHECK (candidate_id ~ '^doc-asset:[0-9a-f]{64}$'),
 source_sha256 text NOT NULL CHECK (source_sha256 ~ '^[0-9a-f]{64}$'),
 asset_sha256 text NOT NULL CHECK (asset_sha256 ~ '^[0-9a-f]{64}$'),
 asset_kind text NOT NULL CHECK (asset_kind IN ('table_cells','omml_formula','emf_graphic','embedded_image')),
 source_location text NOT NULL CHECK (btrim(source_location)<>''),
 page_number integer CHECK (page_number>=1),
 status text NOT NULL DEFAULT 'UNCERTAINTY' CHECK (status='UNCERTAINTY'),
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE (document_id,candidate_id)
);
ALTER TABLE public.document_asset_candidates ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.document_asset_candidates FROM PUBLIC,anon,authenticated;
REVOKE UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER ON public.document_asset_candidates FROM service_role;
GRANT SELECT,INSERT ON public.document_asset_candidates TO service_role;

CREATE OR REPLACE FUNCTION public.persist_unverified_document_asset_candidate(
 p_project_id uuid,p_document_id uuid,p_source_sha256 text,p_candidate_id text,
 p_asset_sha256 text,p_asset_kind text,p_source_location text,p_page_number integer DEFAULT NULL
) RETURNS uuid
LANGUAGE plpgsql SECURITY INVOKER SET search_path=public
AS $$
DECLARE v_doc public.documents%rowtype;
        v_saved public.document_asset_candidates%rowtype;
BEGIN
 SELECT * INTO v_doc FROM public.documents WHERE id=p_document_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'DOCUMENT_NOT_FOUND'; END IF;
 IF v_doc.project_id IS DISTINCT FROM p_project_id THEN RAISE EXCEPTION 'DOCUMENT_PROJECT_MISMATCH'; END IF;
 IF v_doc.source_checksum IS NULL OR lower(v_doc.source_checksum)<>p_source_sha256 THEN RAISE EXCEPTION 'SOURCE_CHECKSUM_MISMATCH'; END IF;
 IF p_candidate_id !~ '^doc-asset:[0-9a-f]{64}$' THEN RAISE EXCEPTION 'INVALID_ASSET_CANDIDATE_ID'; END IF;
 IF p_asset_sha256 !~ '^[0-9a-f]{64}$' THEN RAISE EXCEPTION 'INVALID_ASSET_SHA256'; END IF;
 IF p_asset_kind NOT IN ('table_cells','omml_formula','emf_graphic','embedded_image') THEN RAISE EXCEPTION 'INVALID_ASSET_KIND'; END IF;
 IF nullif(btrim(p_source_location),'') IS NULL THEN RAISE EXCEPTION 'INVALID_SOURCE_LOCATION'; END IF;
 IF p_page_number IS NOT NULL AND p_page_number<1 THEN RAISE EXCEPTION 'INVALID_PAGE_NUMBER'; END IF;
 INSERT INTO public.document_asset_candidates
  (project_id,document_id,candidate_id,source_sha256,asset_sha256,asset_kind,source_location,page_number,status)
 VALUES
  (p_project_id,p_document_id,p_candidate_id,p_source_sha256,p_asset_sha256,p_asset_kind,p_source_location,p_page_number,'UNCERTAINTY')
 ON CONFLICT (document_id,candidate_id) DO NOTHING;
 SELECT * INTO v_saved FROM public.document_asset_candidates
 WHERE document_id=p_document_id AND candidate_id=p_candidate_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'CANDIDATE_NOT_SAVED'; END IF;
 IF v_saved.project_id IS DISTINCT FROM p_project_id
 OR v_saved.source_sha256 IS DISTINCT FROM p_source_sha256
 OR v_saved.asset_sha256 IS DISTINCT FROM p_asset_sha256
 OR v_saved.asset_kind IS DISTINCT FROM p_asset_kind
 OR v_saved.source_location IS DISTINCT FROM p_source_location
 OR v_saved.page_number IS DISTINCT FROM p_page_number
 OR v_saved.status<>'UNCERTAINTY'
 THEN RAISE EXCEPTION 'IMMUTABLE_CANDIDATE_CONFLICT'; END IF;
 RETURN v_saved.id;
END $$;
REVOKE ALL ON FUNCTION public.persist_unverified_document_asset_candidate(uuid,uuid,text,text,text,text,text,integer)
 FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.persist_unverified_document_asset_candidate(uuid,uuid,text,text,text,text,text,integer)
 TO service_role;
