# Контрольный список выпуска

Рабочий источник: integration/release-candidate-v1. Кандидат не означает FINAL RELEASE AUDIT.

- [x] Зафиксирован exact candidate HEAD/tree; все нужные stacked и side PR включены или явно отложены.
- [x] Clean checkout: pinned Python dependencies/pip check, npm ci, Python/Node/compile, security и architecture guards.
- [x] Actual HTTP/jsdom и real Chromium workflows проходят на этом же HEAD; synthetic model явно обозначена.
- [x] Нет секретов/приватных исходников в diff, QA, logs, artifacts.
- [ ] Windows cold-start/restart/reboot и local end-to-end фактически проверены.
- [ ] Backup/Restore данных приложения, crash recovery и migration проверены.
- [ ] Полнота документов и реальные normative/calculation decisions подтверждены.
- [ ] Реальный ACCEPTED case, confirmed memory, report/CAD и остальные MASTER PLAN criteria закрыты.
- [ ] В main после согласованной интеграции обязательны repository-guard и core-tests; старые PR закрыты с superseded-by.
- [ ] Финальные docs/version/tag и FINAL RELEASE AUDIT сохранены.

Не удалять legacy compatibility paths только потому, что новый путь существует. Сначала доказать отсутствие callers и проверить поддержанные сценарии.

Stage10 consolidation is complete. PR74 is the official protected release candidate. Remaining unchecked items belong to later MASTER PLAN stages and final release audit.
