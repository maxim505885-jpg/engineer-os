# Regional OCR — scope and verification ledger

Base: `9bf58d02659d9ff0f330b3c310046f406802f088`. Task branch: `feat/ocr-regions-20261009`.

This bounded extension supports `ENGINEER_OS_OCR_LAYOUT=regions` alongside the default `whole` mode. The existing OCR extraction task and automatic attachment pipeline are reused. No paid service or new dependency is required.

The regional mode executes the whole-page pass first and then four overlapping regions. Coordinates refer to the unrotated original crop; rotation and crop are preserved. Overlap is at most 32 PDF points or 10% of the smaller page dimension. Each candidate retains its pass ID. Automatic model input labels overlapping alternatives explicitly and carries the warning even on an UNCERTAINTY page. Repetitions do not establish independent evidence or agreement.

Shared page limits: 60 seconds, 2 MiB TSV output, 20,000 words, 45 million total rendered pixels and 9 million per pass. Document text and block retention limits remain in force. The dossier records executed coverage, successful pass bounds and incomplete execution. Executed coverage is not recognition completeness, accuracy or engineering acceptance. All candidates remain unverified.

For a local runtime with rus+eng models available, enable the existing OCR route and this mode before launching. PowerShell:

```powershell
$env:ENGINEER_OS_ATTACHMENT_PARSER = 'ocr'
$env:ENGINEER_OS_OCR_LAYOUT = 'regions'
```

Changing layout, implementation, engine, language models or limits changes parser identity; completed/partial old extraction is not silently reused. Use a new extraction task after a configuration change.

## Verification ledger

- Baseline: 8 existing OCR tests PASS with actual rus+eng language models.
- Feature RED: 15 tests ran, 4 failures and 3 errors demonstrated missing layout, shared budgets and dossier fields; missing APIs were not described as clean assertion failures.
- First GREEN: 15 tests PASS. Deadline regressions then showed two assertion failures; subprocess timing was extended to cover PNG preparation and late returns. 16 tests PASS after that correction.
- Fresh independent review found two Important issues: final parsing deadline and flattened regional alternatives in automatic model input. Both reproduced by two failing tests before fixes. No Critical issue or acceptance bypass was observed.
- Ruling: keep whole as default and preserve labelled regional alternatives rather than merge or deduplicate without ground truth. Incorrect recognition remains visible and unverified.
- Deferred minor: dossier lists completed pass descriptors; an interrupted pass lacks its own explicit failed entry and remaining planned bounds. Aggregate planned/completed counts and INCOMPLETE coverage disclose the gap. This does not claim completed recognition.

Final suite, actual-source run, CI and integration results are recorded below after execution. The complete project still requires independently verified document completeness, actual normative/calculation grounds, an accepted case and physical Windows installation/reboot before final release.

## Final local verification

Both Important review findings fixed in one pass, each reproduced RED before the fix. The parsing/transformation stage now rechecks the deadline before completing a pass. Automatic analysis preserves pass labels, carries the unmerged-alternatives warning regardless of page BLOCK status, and marks each batch reference as overlapping alternatives rather than independent evidence.

35 OCR/automatic-analysis tests PASS. Full suite: 741 tests in 67.918 seconds, 739 PASS and 2 native-Windows-only skips. Actual rus+eng models were available. Four Node tests, architecture guard, compile and diff checks PASS. Local DOM/browser attempts could not run because jsdom and the expected Chromium executable were unavailable; published CI must verify those workflows.

Initial real-source run before the final review fixes processed 43/43 pages, 215 passes, zero failed pages and zero retained-text truncations; all pages retained BLOCK/unverified status. Maximum aggregate page pixels 32,080,286, TSV bytes 326,472 and words 2,432. Preserved originals unchanged. A fresh real-source rerun on the final implementation is in progress; its final evidence is recorded separately, not inferred from the earlier run. Source MuPDF xref/object warnings still prevent a claim of rendering completeness or engineering acceptance.

## Published final evidence

PR 94 merged into `integration/release-candidate-v1`: `cca057f6fdd2e1f3751485727543d15b33e1879a`. Tree `2ae639262b28d21707d3f8f628d49fd2370c9e91` equals verified remote source `6db015bb9ad5c38a5143f747f2508eabc5fe97eb` and local source `2114726136e2f43db5a6eff767bec84b057e5ecf`. All 9 CI checks SUCCESS. Linux PR 37907033468: 741 tests (739 PASS, 2 Windows-only skips), 4 Node, 2 HTTP/DOM, 4 Chromium. Native Windows PR 37907033565: 23 tests, actual Ollama qwen3:0.6b and 4 Chromium PASS. Physical PC installation/reboot remains unverified.

Final actual-source rerun on matching parser implementation hashes: 43/43 pages, 215 passes, zero failed pages, zero retained-text truncation, preserved originals and boxes within source pages. Two PDFs took 109.297 and 244.320 seconds. Maximum page pixels 32,080,286, TSV bytes 326,472, words 2,432. All pages remain BLOCK/UNVERIFIED; source MuPDF xref warnings persist.

Assistant visual spot check of three selected numbers: two matches and one mismatch. This is neither complete ground truth nor qualified engineering acceptance. Region OCR is a verified software route; document completeness remains open. Next: localized numeric/table/formula reference comparison, then representative graphic/page/V4 coverage. Exact private source texts and coordinates are retained in private verification artifacts, not published here.
