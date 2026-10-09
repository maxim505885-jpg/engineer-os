# Large CAD inventory — verification

Read-only DXF entity inventory and source locators now use a separate 50,000 block-entity budget. Annotation derivation and export verification retain the 10,000 entity gate and all geometry, resource, audit, source-hash and session restrictions. Inventory reports remain BLOCK when a source is ineligible for editing; resource lists and modelspace locators stay bounded at 100.

Regression: the original 10,001-line DXF test failed because inventory returned no entity counts. After the change, the same source produces complete entity counts and bounded locators while annotation is rejected. The inventory budget boundary is separately covered. Independent review found no Critical/Important issues.

Local validation: 22 focused tests PASS; full suite 731 tests, 729 PASS and 2 native-Windows-only skips. OCR language models were present. Diff check PASS. Native Windows and full GitHub CI must be checked on the published commit before candidate integration.

Real source: unchanged derived DXF SHA256 `dddb5edf86015cf7603f9e95d485d18ee03c4916c30c46e8e88cca4fd9ed18d0`, 16,034,803 bytes, separately converted earlier from the preserved DWG original. Session-bound inventory read 10,172 graphical entities across blocks in 4.324 seconds; measured peak RSS 141,108 KiB on this Linux process. The earlier 15,906 count refers to all entitydb records, including non-graphical records. Counts describe the derived DXF, not proven DWG geometry equivalence.

Real inventory remains BLOCK: CAD_ENTITY_LIMIT, UNSUPPORTED_ENTITY_FOR_EDIT, OUT_OF_PLANE_SOURCE_FOR_EDIT, INVENTORY_TABLE_LIMIT, CUSTOM_BLOCK_FOR_EDIT, DXF_AUDIT_ERRORS_OR_REPAIRS. Entity counting is complete; bounded resource lists remain incomplete. Original bytes are unchanged; engineering acceptance, geometry equivalence and controlled native DWG roundtrip remain unverified.
