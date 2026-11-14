# Rebuild order for the Q&A section
build_qa.py needs SUPABASE_KEY (anon key is enough) and regenerates every qa page from the `qa` table. It does NOT produce everything on the live pages, so run the rest after it:

1. `SUPABASE_KEY=... python3 build_qa.py`
2. `python3 tools/qa_videos.py inject`      – restores the 655 "Watch:" video blocks, their CSS and click-to-play script (data/qa_videos.json)
3. `python3 tools/sync_qa_lists.py`          – category pages list every answer page that exists; counts match
4. `python3 tools/dedupe_canonicals.py`      – duplicate cross-category answers canonicalize to one copy
5. `python3 tools/fix_meta_lengths.py`       – titles <= ~60, descriptions <= 160 (removal only)
6. `python3 tools/set_descriptions.py`       – hand-written descriptions for pages where the generic ones are too short
7. `python3 tools/add_og_tags.py` and `python3 tools/add_jsonld.py` (only if build_qa output lacks them)
8. `python3 tools/build_sitemaps.py`

If you add new videos to answer pages by hand, run `python3 tools/qa_videos.py extract` afterwards so a rebuild does not drop them.
