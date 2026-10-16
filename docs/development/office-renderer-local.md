# Local controlled Office PDF copies

The existing file card provides Create PDF copy for DOC,DOCX andRTF. Tasks use
the existing engineering queue and cancellation controls. Output appears as a
separate unverified PDF file with original hash/fileID/job lineage. It never
creates accepted engineering evidence or overwrites the original.

The Windows development route requires the pinned local QEMU/image/seed bundle
and a local data-root office-renderer.json containing exactly bundle_root
(absolute directory) and manifest_sha256 (trusted SHA256 pin). This setting is
not accepted from a browser/document request. Missing configuration disables
the catalog entry and reports that the local converter is not configured.

Bundle manifest schema1 contains files (relative-path toSHA256 mapping) and
guest_worker_sha256. Fixed roles:qemu/qemu-system-x86_64.exe,worker.qcow2 and
worker-seed.iso. All other entries must be under qemu. The exact file set and
hashes are checked before/after each task. The trusted builder must verify
that the seed embeds the matching runtime/office_guest.py;hashes alone do not
prove seed semantics. Guest-source changes require rebuilding and repinning.

Runtime safety controls:Windows AppContainer0capabilities,owned JobObject,
fixed noNIC/no shared folders command,per-job image/input copies,guest UID/GID
65534 Office,macro3/link2 profile,resource limits,timeout/cancel and output checks.
Output thresholds are polled;they are not kernel disk quotas. TCG itself is not
the host security boundary. Windows/AppContainer ACLs remain authoritative.

This is the tested local development route,not a standalone release installer.
Real document font/layout/formula/source equivalence must be reviewed separately.
Current qualification evidence and open limits are in the new-corpus QA log.
