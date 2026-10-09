# Office source structure — 2026-10-09

Point 13: preserve declared native structure, not rendered-layout or engineering acceptance.

Word equations were previously warnings with no math syntax sent to analysis. Merged Word cells and XLSX ranges likewise had warnings without precise merge declarations. Now Word OMML equations are separate logical units containing normalized source XML and literal tokens, with their original paragraph/cell parent locators. Tokens are not a linearized formula. Word cell locators and candidate text preserve namespace-qualified merge attributes; columns remain XML cell ordinals. XLSX merged range declarations are separate logical units even when corresponding cell records are absent. No values are propagated. Formula presence is recorded independently of formula text, including shared formula followers.

No formula is evaluated, rendered layout verified, or completeness/acceptance granted. Existing warnings and source/checkpoint/byte/unit/text-budget gates remain. Office parser identity changes, so old checkpoints must not be reused as results of this implementation.

Verification against all three available native Office originals: DOCX 489/489 units, XLSX 125/125 and 51/51, total 665/665. No failed or truncated units; original hashes unchanged. Source XML inventory independently matches two Word equations and their literal tokens, fourteen Word cells with merge declarations, three XLSX merged ranges and four formula cells. The previous total 660 grows by two equation units plus three merged-range units.

Correction: the previously reported 48 XLSX merged cells were 48 unit-level `MERGED_CELLS_UNVERIFIED` warnings inherited from a worksheet, not 48 distinct merged ranges. The source declares three ranges. Historical warning counts remain valid as warning counts.

TDD: initial four assertions failed for absent structure/locators/model data; manifest formula count and shared-follower checks also failed before implementation. Review found namespace attribute collisions and equation sibling tails; both reproduced RED and fixed GREEN. Focused 22 tests pass. Pre-final suites 751/754 passed with two native Windows-only skips; final frozen suite and remote CI are recorded separately after completion.

Remaining: 31 Word drawings, physical-page/layout fidelity, formula interpretation/evaluation, rendered tables/merged-cell topology, full V4 and qualified document ground truth. OCR regional/selected outputs and prior numeric mismatches remain unverified. Project readiness stays 8 done / 8 partial / 3 open.

## 72.1. Итог Office-прохода: PR 96 принят

Все 9 checks на `1230aa3a24c1bb46fe4dbacb30d86b1777927388` SUCCESS. Кандидат `f2a58399384dacaff600714cc79e7b85ad3e03a9`, дерево `2ab64d8c8db402ed3146327162ab19356c9809ea` равно проверенному опубликованному и локальному `10d58f3`. Linux PR/push: 755 тестов (753 PASS, 2 native Windows-only skips), 4 Node, 2 HTTP/DOM и 4 фактических Chromium сценария PASS. Windows: 23 теста, startup/cache/restart, реальный qwen3:0.6b через UI и 4 Chromium PASS. Physical Windows NOT_VERIFIED. Полные receipts: docs/qa/2026-10-09-office-source-structure-ci.json.

Три реальных Office-оригинала обработаны полностью в пределах объявленных logical units: 665/665; native source structure и literal tokens сверены, но page/layout/document completeness не подтверждены. Приёмка не выдана. Точный XLSX merged-range count — 3; прежние 48 — unit warnings, не число объединений.

План 8✅ / 8🟡 / 3❌. По пяти критериям: CodeQL/единый программный кандидат закрыт; документальная полнота, нормы/расчёты/реальный FINAL AUDIT, принятая память/отчёт/CAD/providers и physical Windows/release частичны. Далее №13: rendered tables/formulas/31 Word drawings/7 XLSX media members, числовые OCR-конфликты и полный V4 по qualified ground truth. После этого актуальные нормативные основания и 8 semantic calculation roles с реальным solver-run/actual correlation, ACCEPTED-кейс и оставшиеся product gates. Новый результат не снимает BLOCK автоматически.
