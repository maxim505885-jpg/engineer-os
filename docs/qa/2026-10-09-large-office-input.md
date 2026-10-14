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

## CI-discovered fixture and session corrections

The initial Linux PR job passed all 763 Python tests but exposed a stale session-list race in Drive DOM. Controlled response ordering reproduced an old bootstrap list overwriting a user-created conversation. The UI now renders only the latest list request, and initialization preserves a selected conversation or creation already in flight. Both regressions were RED before the fix and GREEN afterward. Both actual local HTTP/DOM scripts pass.

On the next head, Windows passed 23 regression tests, actual Qwen inference and the first two Chromium scenarios, then failed deleting the intake fixture's app.lock with EBUSY. That log does not establish execution of the SIGKILL timeout branch: the failure occurred shortly after scenario PASS. Separately, a deterministic regression proved that the existing forced-stop branch resolved before process closure. The shared fixture helper now installs listeners before signaling, waits for close, bounds forced shutdown and rejects before directory removal if the child does not close. Temporary-directory removal has five bounded retries for transient Windows locks. All seven Node tests pass; independent review has no unresolved Important issues.

Node documents that close follows process termination and stdio closure, while exit can precede stdio closure; rmSync supports bounded retries for EBUSY. References: https://nodejs.org/download/release/latest-jod/docs/api/child_process.html and https://nodejs.org/download/release/latest-jod/docs/api/fs.html. These semantics do not prove the exact Windows lock owner's timing.

Final frozen head:187b6d88448806f31781df7cf68f6bd6bf826b22; tree:2af4da649a69d4f60c7c51ffd7331af1ea6ccb80, equal to local9aa29f7724905137bb6c816a59101ef060a4cc57. Local Python:763 total,761PASS,2native Windows skips with actual rus+eng OCR. Local Chromium could not run because its binary is unavailable; actual browser and Windows verification is recorded from final CI, not inferred from the local scripts.

## 73.1. Итог полного Office-прохода: PR 97 принят

Все 9 CI checks на `187b6d88448806f31781df7cf68f6bd6bf826b22` SUCCESS. PR 97 принят в кандидат `f83c4d5fbaac8e602757ca6fac1646b86589cdff`. Дерево `2af4da649a69d4f60c7c51ffd7331af1ea6ccb80` равно проверенному опубликованному коду и локальному `9aa29f7724905137bb6c816a59101ef060a4cc57`. Linux PR/push: 763 Python-теста (761 PASS, 2 native Windows skips), 7 Node, 2 HTTP/DOM и 4 реальных Chromium-сценария PASS. Windows: 23 теста, clean start/cache repair/restart, настоящий Ollama qwen3:0.6b и все 4 Chromium-сценария PASS; очистка завершилась успешно. Физический Windows ПК по-прежнему NOT_VERIFIED. Receipts: docs/qa/2026-10-09-large-office-input-ci.json.

Полный доступный DOCX 147 МБ обработан: 14 678/14 678 логических единиц, 0 ошибок исполнения и обрезаний текста, исходник неизменён. Сохранены 41 OMML-уравнение с буквальными токенами и 6 300 объявлений объединённых ячеек; source XML сверка совпала. 7 022 единицы остаются BLOCK. 655 элементов графики и 642 media-файла, отображение таблиц, смысл и вычисление формул, полнота страниц/документа не приняты. Число физических страниц неизвестно; полный DOCX не объявлен проверенным V4 PDF. Три source-review решения на настоящем большом оригинале прошли без инженерной приёмки.

За проход закрыты конкретные программные дефекты: несовместимые входные лимиты большого Office, ограниченное чтение оригинала при source review, повторное полное хеширование на каждой единице, две гонки старых списков чатов и преждевременная очистка тестового процесса. Начальные падения CI сохранены, исправления проверены RED→GREEN и независимым ревью.

План остаётся **8 ✅ / 8 🟡 / 3 ❌**. Из пяти критериев закрыт CodeQL/единый программный кандидат; остальные частичны. Следующий шаг №13: квалифицированная сверка rendered tables/merged cells/formulas, всей графики и числовых конфликтов, V4 PDF и полного эталонного покрытия. Затем №6: восемь семантических расчётных ролей, актуальные нормативные основания, реальный solver-run и связь с фактической конструкцией. После этого №14: положительный FINAL AUDIT; на его основании принятая память и отчёт, CAD equivalence/roundtrip и live-provider receipts. Физический Windows и №19 release/main/tag — после закрытия продуктовых критериев. BLOCK не снят автоматически.
