# Large Office originals — 2026-10-09

The available full business-centre report is a 147,210,288-byte DOCX. The former 100 MiB upload limit, 8 MiB per-XML limit and 32 MiB whole-ZIP expansion limit rejected this real source before extraction. This change permits DOCX/XLSX originals up to 256 MiB consistently in UI, authenticated HTTP, preservation and Drive download; other formats remain at 100 MiB.

ZIP safety remains bounded: 512 MiB declared expansion across all members, 32 MiB aggregate declared XML/relationships, 16 MiB per XML read, and 32 MiB cumulative actual XML requests. Unread media are not decompressed. Existing entry-count, traversal, duplicate, encryption and XML entity guards remain. Limits and implementation are part of parser identity.

Office extraction hashes the immutable source before parsing and at completion, verifies the parsed byte snapshot, and checks stat identity before each logical unit. It no longer rehashes a 147 MB original for each of 14,678 units. Source review uses existing streaming SHA verification instead of the old 100 MiB capped read.

## Actual full-source run

Original SHA256: `b253439bdd673a775eaf209ca7d398d766efae5f4a18ac33fa6679f7faae28a5`. Package declared expansion: 307,316,114 bytes; main XML: 8,614,936 bytes. All 14,678 logical units processed in 244.411 seconds, 0 execution failures, 0 text truncations, 1,095,842 stored characters. Original identities unchanged.

7,022 units remain BLOCK. Source inventory contains 41 OMML equations (literal tokens independently matched source XML), 6,300 cells with merge declarations, 655 Word drawing elements and 642 media members. Warning counts: DRAWING_NOT_READ 509, FIELD_NOT_EVALUATED 68, NO_TEXT 438, MERGED_CELL_UNVERIFIED 6300, BODY_STRUCTURE_UNVERIFIED 11, EQUATION_NOT_READ 70; warning counts can overlap units and are not media/member counts.

On logical unit 7, a native-source quote was registered against this real large original. SOURCE_CONFIRMED, REJECTED and NEEDS_DATA each completed with streaming original verification. All events remain SOURCE_REVIEW_ONLY, actor_verified=false and acceptance_granted=false. This is source-path regression coverage, not qualified engineering review.

The complete DOCX native structure is now accessible; physical pages, rendered layout, formula interpretation/evaluation, drawing semantics, qualified ground truth and full V4 PDF completeness remain unverified. No document acceptance is granted. The 19-point plan remains 8 complete in specified software scope / 8 partial / 3 open.

## Validation

Upload/HTTP/Drive/UI assertions and bounded-hash regression reproduced failures before implementation. Independent review found an important source-review cap and minor stale UI wording; both fixed, with regression coverage. Focused 47 Python and 5 Node tests PASS; architecture, compilation, JS syntax and diff checks PASS. Final full-suite and remote CI receipts are recorded separately after completion.
