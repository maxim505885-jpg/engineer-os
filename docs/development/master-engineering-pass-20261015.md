# Автономный проход по MASTER DEVELOPMENT PROMPT, 15.10.2026

Управляющее ТЗ: предоставленный пользователем MASTER DEVELOPMENT PROMPT.
Цель: сохранить локальное приложение/Ollama, исправлять доказанные потери,
подготовить независимые инженерные адаптеры без обязательного облака.

База: db29e4c946e4db5e088e8fdd727c6165365dcc4d, отдельный managed worktree.
Первоначальная папка architecture/openwebui-integration содержит staged и untracked
изменения; они не переносятся и не изменяются. Прямые fetch/push пока недоступны;
GitHub читается connector-ом. Open PR149/151 содержат более новую документацию,
чем handoff в candidate. Никакого автоматического merge.

Порядок и критерии:

- [x] Сверить локальные ветки, открытые PR, актуальные инструкции и CI базы.
- [x] Воспроизвести потерю parser limitations в SQLite/page journal.
- [x] Сохранять ограничения и table-loss diagnostics, обнаруживать смену source.
- [x] Проверить read-only DXF comparison на сохранении/потере/изменении/единицах.
- [x] IFC adapter: lazy optional dependency; bounded source-bound inventory,
  units/relationships/properties/materials, GUID locators, model diff;
  синтетический IFC integration fixture, corrupt/missing units/identity tests.
- [x] Контрольная балка Pynite: SI input, source/evidence identity, аналитический
  benchmark, реакции/усилия/прогиб, invalid input tests. Рамы/фермы/сечения
  отдельно, до эталонной квалификации не поддерживаются.
- [x] Выполнить доступные нормативные, memory/report, backup/UI/Windows проверки.
- [x] Сохранить матрицу всех 19 пунктов: код, проверки, границы, критерий/next step.
- [ ] Обновить карту/master-plan/handoff, записать точные результаты, подготовить PR.

Ограничения: не скачивать OCR-модели; не активировать OLE; не менять оригиналы;
не превращать BIM в расчётную схему; не выдавать synthetic PASS за реальный
ACCEPTED case или full release. Не удалять реальные BLOCK без source qualification.

Фактическое дополнение: real V4 page57 offline rerun сохранил23 блока с BLOCK
TABLE_CAPTION_WITHOUT_VERIFIED_ROWS; source unchanged, acceptance=false. Не выдавать
этот ограниченный прогон за проверку полного V4. Финальный focused run60 PASS,
Chromium7/7 PASS; full1085 Windows suite имеет7errors/47skips, детали в QA.
