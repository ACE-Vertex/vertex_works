# VERTEX WORKS — Explorer Authoritative Binding Probe 000059

Purpose: determine the exact frontend render anchor that must bind `XrayFolder.path`
to the visible Project Explorer row.

This artifact is READ-ONLY with respect to production source. It adds only this
probe script and this note, then runs the probe through Vertex Works verification.

Required architecture after the probe:
- Explorer row identity comes from backend `XrayFolder.id/path/relative_path`.
- Scoped X-Ray consumes that authoritative path.
- No pointer/DOM inference may silently fall back to `G:\Vertex_Project\Development`.
- If an exact row path is unavailable, Ray fails closed instead of scanning the project root.


## 000060 CP932 hotfix
The probe now forces UTF-8 stdout/stderr with backslash replacement and uses an ASCII banner, preventing Windows CP932 encode failures while printing source excerpts.
