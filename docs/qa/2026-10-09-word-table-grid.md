# Native Word table grid — 2026-10-09

The full available147MB report contains118tables and12826native XML cells. Earlier extraction preserved6300merge declarations but exposed XML cell ordinals only. The new source_grid locator preserves ordinal coordinates and adds declared grid-column intervals plus exact vertical restart anchors. No cell values are inherited or propagated; no rendering, formula evaluation or engineering acceptance is granted.

The resolver reads tblGrid, gridSpan, gridBefore/gridAfter and vMerge. Omitted vMerge val means continue; a continuation requires the exact same grid interval in the immediately preceding valid row. Plain or empty rows interrupt continuity. Numeric parsing and grid width are bounded at1024columns; duplicate/missing/unsupported declarations, legacy hMerge, width conflicts, structural wrappers and tracked table/row/cell grid revisions remain unresolved. Bookmarks are transparent annotations. Original MERGED_CELL_UNVERIFIED warnings remain; consistent native structure does not establish displayed layout.

Initial native source read mapped all12826cells consistently and5759vertical continuations. All118source tblGrid declarations and6300merge declarations remain source data; the complete actual Store extraction and final CI receipts are recorded separately after finishing. Physical pages and qualified ground truth remain unverified.

Seven behavioral regressions reproduced missing locators and false consistent states before the corresponding fixes. Independent review identified skipped wrapped rows and ignored tracked properties; both fixed RED→GREEN, with no remaining Critical/Important findings. Existing Office behavior, exact originals and fail-closed acceptance are retained. The implementation hash and1024column bound are part of parser identity; previous Office jobs require fresh checkpoints.

Semantics grounded in Microsoft Open XML documentation:
- https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.verticalmerge?view=openxml-3.0.1
- https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.verticalmerge.val?view=openxml-3.0.1
- https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.gridbefore?view=openxml-3.0.1
- https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.gridafter?view=openxml-3.0.1

This implements native source topology only. Plan13/document completeness, qualified rendered tables/formulas/graphics, normative calculation/positive FINAL AUDIT, accepted memory/report, CAD/provider receipts, physical Windows and release remain open in their stated scope. Overall plan8complete/8partial/3open.
