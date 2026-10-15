# Контрольный список выпуска

Рабочий инженерный источник текущего прохода: feat/master-plan-completion-20261009 поверх объединённого31ec638. Официальный кандидат integration/release-candidate-v1 пока не содержит этот проход. Кандидат не означает FINAL RELEASE AUDIT.

- [ ] Зафиксирован свежий exact candidate HEAD/tree; общий PR91 перенесён после проверок.
- [ ] Свежие pinned dependency/clean-checkout/CI и CodeQL результаты подтверждены для переносимого HEAD.
- [x] Actual HTTP/jsdom и четыре real Chromium workflows текущего локального дерева проходят; synthetic model явно обозначена.
- [x] Нет секретов/приватных исходников в diff, QA, logs, artifacts.
- [ ] Windows cold-start/restart/reboot и local end-to-end фактически проверены.
- [x] Backup/Restore данных приложения, crash recovery и migration проверены.
- [ ] Полнота документов и реальные normative/calculation decisions подтверждены.
- [ ] Реальный ACCEPTED case, confirmed memory, report/CAD и остальные MASTER PLAN criteria закрыты.
- [ ] В main после согласованной интеграции обязательны repository-guard и core-tests; старые PR закрыты с superseded-by.
- [ ] Финальные docs/version/tag и FINAL RELEASE AUDIT сохранены.

Не удалять legacy compatibility paths только потому, что новый путь существует. Сначала доказать отсутствие callers и проверить поддержанные сценарии.

Прежняя консолидация PR74 — исторический результат. Текущая консолидация PR91 ещё не перенесена; CodeQL на31ec638 показал27 предупреждений. Воспроизведённые файловые проблемы исправлены, но новый скан/разбор всех сообщений требуется отдельно. Живая карта §67 и master-plan.md содержат актуальные19 критериев.
