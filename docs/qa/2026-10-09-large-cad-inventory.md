# Large CAD inventory — verification

Read-only DXF entity inventory and source locators now use a separate 50,000 block-entity budget. Annotation derivation and export verification retain the 10,000 entity gate and all geometry, resource, audit, source-hash and session restrictions. Inventory reports remain BLOCK when a source is ineligible for editing; resource lists and modelspace locators stay bounded at 100.

Regression: the original 10,001-line DXF test failed because inventory returned no entity counts. After the change, the same source produces complete entity counts and bounded locators while annotation is rejected. The inventory budget boundary is separately covered. Independent review found no Critical/Important issues.

Local validation: 22 focused tests PASS; full suite 731 tests, 729 PASS and 2 native-Windows-only skips. OCR language models were present. Diff check PASS. Native Windows and full GitHub CI must be checked on the published commit before candidate integration.

Real source: unchanged derived DXF SHA256 `dddb5edf86015cf7603f9e95d485d18ee03c4916c30c46e8e88cca4fd9ed18d0`, 16,034,803 bytes, separately converted earlier from the preserved DWG original. Session-bound inventory read 10,172 graphical entities across blocks in 4.324 seconds; measured peak RSS 141,108 KiB on this Linux process. The earlier 15,906 count refers to all entitydb records, including non-graphical records. Counts describe the derived DXF, not proven DWG geometry equivalence.

Real inventory remains BLOCK: CAD_ENTITY_LIMIT, UNSUPPORTED_ENTITY_FOR_EDIT, OUT_OF_PLANE_SOURCE_FOR_EDIT, INVENTORY_TABLE_LIMIT, CUSTOM_BLOCK_FOR_EDIT, DXF_AUDIT_ERRORS_OR_REPAIRS. Entity counting is complete; bounded resource lists remain incomplete. Original bytes are unchanged; engineering acceptance, geometry equivalence and controlled native DWG roundtrip remain unverified.

## Published CI and integration

PR 93 merged into integration/release-candidate-v1 at `9bf58d02659d9ff0f330b3c310046f406802f088`. Tree `2cb8e47cd4d5f199edee708cb784e4db83a7c62d` exactly matches verified source `fd4e8da9b933dd2ab3c8065a6c1aafcb816122dc`. All 9 check runs SUCCESS. Linux PR/push: 731 tests (729 PASS, 2 native-Windows-only skips), 4 Node, 2 HTTP/DOM, 4 Chromium. Native Windows PR: 23 tests, actual Ollama qwen3:0.6b and 4 Chromium PASS. Windows workflow on this branch runs for PR only. Physical PC installation/reboot and engineering acceptance remain unverified.

Offline OCR region feasibility probe is recorded separately; higher confidence without transcription ground truth does not establish accuracy or coverage and is not a shipped feature.
