# MASTER PLAN — ENGINEER OS

**Этот раздел является текущим главным планом проекта и имеет приоритет над более ранними промежуточными статусами в этой карте.**
Старые разделы сохраняются как история разработки. Новый чат обязан начинать работу с разделов 47–48 и не возвращать проект к старому состоянию.

### Правило работы по плану

После каждого рабочего прохода обязательно писать и фиксировать в этой карте:

- ✅ что полностью выполнено и фактически проверено;
- 🟡 что реализовано программно, но требует реального запуска/внешнего подтверждения;
- ❌ что ещё не выполнено;
- **Следующий активный пункт: №N — название**;
- branch / PR / head SHA / CI run, если изменялся код;
- реальные BLOCK/UNCERTAINTY нельзя снимать ради продвижения плана.

**100% проекта означает не количество написанного кода, а выполнение всех критериев MASTER PLAN и финальный воспроизводимый релиз.**

### Текущее состояние

| № | Этап | Статус | Критерий завершения |
|---|---|---|---|
| 1 | Единый integration candidate | ✅ | локальный инженерный контур собран |
| 2 | Реальная проверка OCR/model quality | ✅ | качество измерено fail-closed на реальных примерах |
| 3 | Large-document resume/recovery | ✅ | checkpoints/identity/retry/budgets работают |
| 4 | DOCX/XLSX/DOC | ✅ | форматы подключены с provenance |
| 5 | ТЗ → evidence → assessments | ✅ | versioned requirements и source-bound review работают |
| 6 | Реальная нормативная + расчётная верификация | 🟡 | software gates готовы; реальные norm/LIRA/SCAD decisions ещё не закрыты |
| 7 | Полный реальный инженерный case workflow | ✅ | Stage-7 real case выполнен воспроизводимо |
| 8 | FINAL AUDIT / acceptance layer | ✅ | immutable audit, stale invalidation, acceptance gate и реальный BLOCK audit работают |
| 9 | Windows one-click runtime | 🟡 | код/CI готовы; нужен фактический Windows cold-start/restart/end-to-end |
| 10 | Release consolidation / единый source of truth | ✅ | официальный защищённый release-candidate собрал stacked/side streams и прошёл clean checkout + CI |
| 11 | Product Design / UI/UX проработка | ✅ | дизайн-система, workflow UX, normal/advanced modes, responsive/accessibility и Chromium baseline подтверждены |
| 12 | Reliability: Backup/Restore + browser release gate + recovery | ❌ | данные восстанавливаются; настоящий Chromium gate; crash/restart/data-lock проверены |
| 13 | Document Intelligence production completeness | ❌ | OCR/on-demand Windows route, сложные таблицы/графика, completeness workflow доведены до универсального состояния |
| 14 | Закрытие реального инженерного BLOCK и повторный accepted-case | ❌ | после №6/13 Stage7+Stage8 повторены; чистый кейс способен честно получить ACCEPTED |
| 15 | Confirmed engineering memory | ❌ | только ACCEPTED cases → reusable memory → recall → обязательная re-verification в новой задаче |
| 16 | Report Generator | ❌ | evidence-bound DOCX/PDF выпуск с таблицами/рисунками/выводами и FINAL AUDIT |
| 17 | CAD/DWG Agent | ❌ | безопасный DWG/DXF workflow: import/read/review/edit/export/verification |
| 18 | Multi-AI connector | ❌ | одинаковые инженерные gates для локального и optional external providers; платные провайдеры не обязательны |
| 19 | v1.0 FINAL RELEASE AUDIT | ❌ | clean install/release candidate/backup/restore/Windows/real accepted case/docs/version tag полностью воспроизводимы |

---

### №9 — Windows one-click runtime — ОТЛОЖЕНО ДО WINDOWS

По указанию пользователя Windows проверяется последней; сейчас активен №10 — единый кандидат выпуска. Фактические Windows checks остаются незавершёнными.

Историческая Windows-база (PR67), не текущий общий release candidate:
- branch: `feat/windows-one-click-stage9-20261007`;
- PR67;
- head после hardening: `87fccbafbf6a944443e2f503acddf48f33e3b17e`;
- PR mergeable;
- push run 37540039590 SUCCESS;
- PR run 37540067054 SUCCESS;
- 473 Python tests PASS в зафиксированном прежнем CI; текущая локальная база содержит474, общий кандидат с guard —480;
- PowerShell syntax PASS;
- compile PASS;
- actual HTTP/DOM PASS.

Уже автоматизировано:
- `.venv` create/reuse;
- dependency fingerprint;
- Ollama start/reuse;
- qwen3:8b presence/pull;
- Open WebUI detection/reuse/start when available;
- Drive/local env load without printing secrets;
- ENGINEER OS + built-in worker background start;
- readiness;
- browser auto-open;
- duplicate-process protection;
- logs/startup-state;
- safe stop helper.

Чтобы поставить №9 ✅, выполнить на реальном Windows:
1. cold start двойным кликом `Start_ENGINEER_OS.cmd`;
2. browser opens automatically;
3. Ollama/model ready;
4. Open WebUI reused/started if installed;
5. ENGINEER OS + worker ready;
6. повторный двойной клик не создаёт дубли;
7. закрыть/запустить приложение повторно;
8. reboot Windows → one-click start;
9. история/SQLite/files/reviews/case/audit сохранены;
10. реальные PDF/DOC/DOCX/XLSX/LIR принимаются;
11. Drive import проверен при наличии OAuth;
12. CORE_RUN → Stage7 → FINAL AUDIT проходит с ожидаемым fail-closed результатом;
13. кириллица/пробелы/длинные пути проверены;
14. логи не содержат secrets;
15. stale lock/process отсутствует после restart.

---

### №10 — Release consolidation / единый source of truth

Статус: ✅ ЗАКРЫТ.

Официальный source of truth разработки: `integration/release-candidate-v1`, PR74.
Включены Stage9, stacked PR38–67, боковой Chromium stream PR60 и актуальный main security baseline.
Release-candidate защищён: force-push/delete запрещены, обязательны `core-tests` и `repository-guard`.
Проверено: 480 Python tests, 4 Node tests, HTTP/jsdom, real Chromium, architecture guard, security guard, compile и отдельный clean checkout.

Merge в `main` не является критерием закрытия №10: он намеренно отложен до последующих release criteria, чтобы старый стабильный main не подменять незавершённым продуктом. PR74 является официальным воспроизводимым release-candidate.

**Проблема:** рабочая версия сейчас живёт в stacked PR, а `main` значительно старее. Текущий Stage-9 head примерно на 308 commits впереди main и затрагивает около 280 файлов.

Сделать:
1. создать `integration/release-candidate-v1` от полного проверенного Stage-9 tree;
2. проверить ancestry/trees всех нужных PR #38–#67;
3. убедиться, что боковые полезные изменения не потеряны;
4. вернуть настоящий Playwright/Chromium gate из UI/QA stream;
5. удалить только реально obsolete/dead compatibility paths после проверки;
6. полный CI на release candidate;
7. clean checkout smoke;
8. после №6/№12 и release criteria — merge в `main`;
9. закрыть/архивировать старые stacked draft PR с документированным superseded-by.

Критерий ✅: один официальный reproducible branch/main содержит весь актуальный продукт.

---

### №11 — Product Design / UI/UX проработка — ✅ ЗАКРЫТ

**Почему здесь:** дизайн должен выполняться после №10, когда продукт уже собран в единый release-candidate, но до финальных browser/reliability проверок. Иначе UI придётся повторно переделывать после объединения веток.

Сделать:
- аудит всех экранов и пользовательских сценариев;
- единая информационная архитектура приложения;
- чёткое разделение: чат / файлы / ТЗ / evidence / domain packets / CORE_RUN / Stage7 / FINAL AUDIT / настройки;
- дизайн-система: typography, spacing, buttons, forms, tables, status badges, panels, dialogs;
- визуальная иерархия инженерных статусов PASS / WARNING / UNCERTAINTY / BLOCK / ACCEPTED;
- понятное отображение причин BLOCK и следующего действия;
- desktop-first UX для инженерной работы;
- адаптация под ноутбук/планшет/мобильный просмотр;
- loading / empty / error / offline / reconnect states;
- большие документы и длинные таблицы без поломки layout;
- accessibility: keyboard navigation, focus states, contrast, readable text;
- drag-and-drop/upload UX;
- progress/resume UI для больших документов;
- понятный workflow от загрузки файлов до FINAL AUDIT;
- дизайн Stage7/Stage8 экранов без скрытия доказательной трассировки;
- минимизация количества технических JSON-полей в обычном пользовательском режиме;
- advanced/debug mode оставить отдельно;
- визуальный аудит в реальном Chromium;
- screenshots/reference states для regression;
- никакой дизайн-полировки не должна менять инженерную семантику или обходить fail-closed.

Критерий ✅ выполнен:
1. основной инженерный маршрут вынесен в явную навигацию Sources → ТЗ → Evidence → проверки → кейс → FINAL AUDIT;
2. обычный режим скрывает low-level JSON/manual extraction, advanced mode сохраняет доступ;
3. PASS/WARNING/UNCERTAINTY/BLOCK имеют текстовую + визуальную семантику;
4. desktop/mobile layout проверен реальным Chromium без горизонтального overflow;
5. accessibility smoke подтверждает labels/aria-labels; focus/reduced-motion правила зафиксированы;
6. reference screenshots сохраняются как CI artifacts;
7. дизайн зафиксирован в release-candidate через PR86 / merge `a7d39f270cf7145a3435e5ee70949a510cecb0f3`.

Stage11 не менял серверную инженерную семантику и не снимал BLOCK/UNCERTAINTY.

---

### №12 — Reliability / Backup / Restore / Browser Gate — СЛЕДУЮЩИЙ АКТИВНЫЙ ПУНКТ

Сделать:
- `Backup_ENGINEER_OS.cmd`;
- `Restore_ENGINEER_OS.cmd`;
- backup SQLite + originals + evidence + reviews + requirements + domain packets + Stage7 + FINAL AUDIT + non-secret config;
- manifest SHA256 и проверка backup integrity;
- restore только после validation;
- real Chromium/Playwright CI gate;
- crash/restart test;
- stale lock recovery;
- disk-full/partial-write handling для критичных записей;
- backup before schema migration;
- restore test на отдельном data-dir.

Критерий ✅: потеря процесса/обновление/backup+restore не теряют проект и не создают ложный ACCEPTED.

---

### №13 — Document Intelligence production completeness

Не ставить целью «сделать любой OCR PASS». Цель — универсальный воспроизводимый workflow.

Сделать:
- Windows-compatible OCR environment/service;
- on-demand запуск OCR, а не постоянное потребление RAM;
- one-click supervisor умеет обнаружить OCR capability;
- сложные raster/mixed tables;
- graphics/legends;
- coverage/completeness report;
- visual review queue;
- source coordinates/provenance;
- large-document resume;
- представительские real-document fixtures;
- V4 11 BLOCK разобрать как реальный regression corpus;
- проверить, можно ли снять BLOCK доказательствами; если нельзя — BLOCK остаётся.

Критерий ✅: пользователь загружает документ один раз, система сама выбирает native/OCR/review route и честно выдаёт доказуемую completeness state.

---

### №6 — Возврат и фактическое закрытие инженерных specialist gates

После Windows/release foundations вернуться к пункту6.

Нормативная часть:
- authoritative source нужной редакции;
- source SHA;
- authority verification;
- scope/applicability;
- exact clause/requirement;
- evidence-bound actual condition;
- expert engineering decision.

LIRA/SCAD:
- конкретная установленная версия пользователя;
- документированный export/API snapshot;
- geometry;
- materials/sections;
- loads/combinations;
- supports/releases;
- units;
- solver executable/version/command identity;
- реальный solver run;
- output/log receipt;
- result semantic verification;
- actual-structure correlation.

Критерий ✅: реальный normative + calculation packet получает `READY_FOR_ENGINEERING_DECISION` на фактических проверенных данных, а инженерное решение закрывает prerequisites без synthetic substitutions.

---

### №14 — Повтор реального кейса после закрытия BLOCK

После №6 и №13:
1. повторить Stage7 на «Набережная 28А» либо на другом полностью подтверждаемом объекте;
2. все source identities/reviews fresh;
3. requirements/evidence/domain/specialists/QC complete;
4. Stage8 FINAL AUDIT повторить;
5. acceptance только если действительно нет BLOCK/ERROR/недопустимой UNCERTAINTY.

Критерий ✅: существует минимум один **реальный** ACCEPTED engineering case с полной audit trail. Если реальный объект объективно не может быть ACCEPTED из-за недостатка исходных данных, использовать отдельный реальный полностью подтверждаемый case; нельзя искусственно снимать BLOCK.

---

### №15 — Confirmed engineering memory

Текущая memory boundary безопасна, но read-only/contextual.

Сделать:
- запись только из ACCEPTED audit/certificate;
- project/object scoping;
- source refs + case/audit SHA;
- immutable versions;
- recall;
- remembered fact всегда NOT_EVIDENCE в новой задаче до повторной source verification;
- delete/export/backup;
- защита от cross-project leakage;
- тест, что BLOCK/UNCERTAINTY никогда не обучают confirmed memory.

Критерий ✅: система действительно накапливает подтверждённый инженерный опыт, не превращая память в доказательство.

---

### №16 — Report Generator

Сделать production workflow:
`accepted evidence + calculations + normative decisions → structured report → DOCX/PDF → review → FINAL AUDIT`.

Обязательно:
- traceable sections;
- source/evidence IDs;
- таблицы;
- изображения;
- conclusions;
- normative references;
- templates;
- no invented measurements/defects;
- revision history;
- compare generated report against ТЗ;
- export DOCX/PDF.

Критерий ✅: готовый технический документ воспроизводимо формируется из подтверждённых данных и не превышает evidence.

---

### №17 — CAD/DWG Agent

Текущий CAD/DWG функционал практически не реализован, хотя он входит в исходную концепцию.

Сделать отдельным fail-closed контуром:
- DWG/DXF intake и identity;
- безопасный конвертер/reader;
- layers/blocks/text/dimensions/entities inventory;
- связь графики с объектом/evidence;
- controlled edits;
- before/after diff;
- export;
- human review;
- никаких изменений оригинала без отдельной derived copy.

Критерий ✅: один реальный CAD case проходит read → review → controlled edit → export → verification.

---

### №18 — Multi-AI connector

Не делать обязательной зависимостью v1 local mode.

Сделать:
- единый provider contract;
- Ollama остаётся default/free;
- Open WebUI optional;
- external providers only when user configures them;
- одинаковые source/evidence/acceptance gates независимо от модели;
- provider identity/version in receipts;
- no provider may bypass FINAL AUDIT.

Критерий ✅: переключение провайдера меняет только inference runtime, но не инженерную доказательность.

---

### №19 — v1.0 FINAL RELEASE AUDIT

Финальная проверка 100%:
- clean checkout;
- one-click Windows install/start;
- offline/local mode;
- dependency locks;
- real Chromium gate;
- backup/restore;
- migration/upgrade;
- representative PDF/DOC/DOCX/XLSX/LIR;
- Drive;
- accepted engineering case;
- confirmed memory;
- report generation;
- CAD case;
- optional multi-AI;
- security/secrets review;
- docs;
- release notes;
- version/tag;
- main matches release tree;
- no open critical/high defects;
- FINAL RELEASE AUDIT record.

**Только после выполнения №19 проект считать 100% завершённым по полной исходной концепции.**

---
