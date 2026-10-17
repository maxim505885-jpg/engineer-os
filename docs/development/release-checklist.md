# Контрольный список выпуска ENGINEER OS1.0

Актуализация15.10.2026. Candidate3f87eed93f1460715a35df0a6cbf0d8550d380e3 после
PR153 имеет квалифицированное дерево b91c33d7cbb11e008e15516ecae4a74d33ac69bd.
Это не стабильный релиз. Исторические статусы прежних PR не являются текущими.

Основание: [полный аудит](../qa/2026-10-15-full-readiness-audit.md),
[12release gates](release-v1-definition-20261015.md),
[план исполнения](../superpowers/plans/2026-10-15-engineer-os-v1-completion.md).

## Подтверждённая основа

- [x] PR153 объединён; программное дерево совпало с проверенным.
- [x] Exact-head Core/Windows/Security/Optional Linux+Windows SUCCESS.
- [x] Нативный Windows suite1161tests OK(55skips);7Chromium;отдельный живой Qwen.
- [x] Backup/restore/recovery и3Start/Stop с сохранением session проверены в описанном scope.
- [x]29оригиналов private corpus сохранены; hashes/локальные receipts не включены в Git.

## Обязательные критерии выпуска — ещё не закрыты

- [ ] R01: одна идентифицируемая поставляемая и работающая сборка.
- [ ] R02: воспроизводимый полный Windows engineering profile и offline startup.
- [ ] R03: документная полнота и source-view в заявленном scope.
- [ ] R04: проверенное source-bound ТЗ/Evidence, все required inputs учтены.
- [ ] R05: квалифицированный catalog нормативных правил и real comparison.
- [ ] R06: контрольные расчёты доступны через UI с provenance/units/review.
- [ ] R07: CAD geometry/loss ledger/qualified roundtrip и bounded large route.
- [ ] R08: IFC UI/GUID Evidence, independent corpus и hard resource limits.
- [ ] R09: production review issuer и реальный положительный FINAL_AUDIT.
- [ ] R10: реальная accepted memory и fresh FINAL DOCX/PDF readback/visual QA.
- [ ] R11: Windows clean install/reboot/offline/update/key-loss/rollback qualification.
- [ ] R12: все предыдущие PASS,консолидация57PR,full diff/SAST/licenses,
      main/version/tag/артефакт/checksums/clean artifact install/FINAL_RELEASE_AUDIT.

ЛИРА/SCAD — отдельныйV01. Если управляющееТЗ конкретного кейса требует vendor
results,его приёмка блокируется до их проверки; базовое приложение не должно
выдавать такую невозможность за собственную поддержку полного vendor API.

Каждый чек требует exact build/profile/source scope, команды/метода, фактического
результата и immutable receipt. SUCCESS счётчика страниц или unit tests не
подменяет инженерную квалификацию. SKIP обязательной функции не считается PASS.
