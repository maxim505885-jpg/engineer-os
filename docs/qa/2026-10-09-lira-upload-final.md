# LIRA upload final verification — 2026-10-09


[PR 99](https://github.com/maxim505885-jpg/engineer-os/pull/99) объединён в `integration/release-candidate-v1`: `8009b9375de516fdce5d90b7237933441b562c61`. Проверенный head: `5586e5ec10a8aa2db0d85137a3d6559fd964b7c4`; локальное дерево: `097b72e53a9494fbae9aa3dab01b1f6da3597cd9`. На ПК пользователя эта версия не установлена; выпуск и физический Windows остаются непроверенными.

Штатный загрузчик сохраняет оригиналы и SHA256, автоматически разбирает полный UTF-8 TXT ЛИРА, протоколы, ALD/COP и ZIP-комплекты. Карточка файла и контекст анализа содержат наблюдения. Подсчёт узлов/КЭ и буквальная проверка ordinal-ссылок выполняются по всему TXT независимо от preview 100 000 символов. Прерванный журнал получает INTERRUPTED_BY_USER; статический контроль не считается завершением всего расчёта. COP отделён от фактических усилий; ALD не считается результатами. ZIP ограничен 64 записями и 100 MiB распакованных данных; без распаковки на диск, рекурсии, ZIP64/шифрования/ссылок.

Финальный Linux CI: 792 теста — 790 PASS и 2 Windows-only skip; 7 Node, 2 HTTP/DOM и 4 Chromium PASS. Windows: 23 теста, startup/restart, реальный Ollama qwen3:0.6b и 4 Chromium PASS. Все три финальных workflow завершились SUCCESS. 22 новых регрессионных теста PASS. Независимое ревью выявило пять ошибок повреждённых ZIP/TXT, все исправлены; повторное ревью без оставшихся Important. Реальная уязвимость XML через UTF16 без BOM исправлена parser-level RejectDTD и запретом NUL/неподдержанной кодировки; тесты UTF16/UTF32 и независимый parser callback PASS. Повторный CodeQL alert39 проверен как ложное предупреждение о нераспознанном callback, review thread закрыт с подтверждённым основанием.

На трёх исходных TXT получены узлы/КЭ 119779/127776, 37083/44086, 83152/94775; буквальных расхождений node/stiffness references не найдено. Реальный HTTP upload/download сохранил секцию2 побайтно. Один ZIP с десятью исходниками, 52 226 306 expanded bytes, распознал все десять файлов и оба прерванных журнала. Оригиналы не изменялись.

№6 остаётся 🟡; план 8 ✅ / 8 🟡 / 3 ❌. Готов только программный приём и ограниченный разбор источников. Binary LIR semantic decoder, RAR, квалифицированная грамматика/семантика/опоры/сочетания/единицы/грунт, фактические таблицы результатов, завершённые runs, точная связь LIR→TXT→run, нормы и actual correlation остаются открыты; acceptance=false. QA: `docs/qa/2026-10-09-lira-upload-final.md`. Следующий шаг — обновление приложения на ПК и подключение результатов расчёта, затем инженерная верификация.

## Receipts

- Linux workflow37941006248; Windows37941006529; Security37941006694 — SUCCESS at tested head5586e5ec10a8aa2db0d85137a3d6559fd964b7c4.
- Linux full regression792 tests, 790 passed, 2 skipped (97.410s). Windows workflow includes23 checks and real Ollama qwen3:0.6b. Browser TXT/log upload and reload checks PASS on both systems.
- Local full regression792 tests, 775 passed, 17 environment-dependent skips (65.275s); not substituted for the CI result.
- Source originals remain separate from derived observations and no artifact roles/verified norms/engineering acceptance are created automatically.
- CodeQL38 was a real encoding bypass. CodeQL39 on the custom parser is a reviewed false positive: RejectDTD.doctype rejects every DOCTYPE before entity expansion; direct parser tests verify protection independently of the regex/NUL filters, with internal/external/parameter entity cases checked during independent review. Review threads PRRT_kwDOUiM3os6qzg0I and PRRT_kwDOUiM3os6qz2NG were resolved only after verification.

## Remaining delivery limits

The user's local app still needs updating. A single proprietary LIR supports identity inspection only; full semantic verification requires readable model/results exports. RAR and automatic native LIRA control are not implemented. Qualified grammar, result units/combinations/supports/soil, run binding, norms and actual-structure correlation remain open.
