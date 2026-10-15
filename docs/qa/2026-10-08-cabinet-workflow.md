# №4 — приёмка программного маршрута кабинета
Дата:08.10.2026. Draft PR77 к PR76. Main не изменён.

Закрыт маршрут проекта в программных границах: диалог/оригиналы → ТЗ → источники → нормы/расчёты → снимок/финальный аудит → архив. Роли выбираются формой без обязательного JSON. Устаревшие результаты направляют на обновление. Генератор заключений отдельно №10, реальное принятие №12.

Режим обслуживания: Stop_ENGINEER_OS.cmd → Recover_ENGINEER_OS.cmd → путь архива/нового каталога → backup/verify/restore → activate → Start_ENGINEER_OS.cmd. Модель и worker в обслуживании не запускаются. Активный владелец отказывает backup/activate. No-replace и старый каталог сохраняются. Каталог выбирается текстовым абсолютным путём; нативный picker не предусмотрен. Linux developer launch: scripts/run_data_recovery.py; Windows native flow ещё №16.

Проверки:517 Python PASS (10 новых), полный свежий прогон40.250s; 4 Node PASS; architecture guard/compileall/diff check PASS; HTTP/DOM кабинет/Drive PASS. Backend архив:410 сообщений205 задач, стабильные курсоры, изоляция проекта. Recovery API: копия/verify/restore, hash/история/очередь, no-replace, authentication/origin, busy owner, relative path, activate failure preserves selection, serial operation guard.

Chromium: штатный launcher/worker с контролируемой моделью; файл/ответ/история; архив; отказ backup активного приложения; остановка; копия/verify/restore; выбор каталога с кириллицей/пробелами; запрет повторной замены; сравнение original bytes; запуск выбранного каталога с прежним ответом и файлом. Всего1 модельный запрос, завершённая работа не повторяется. Live Ollama/OAuth и Windows не проверены.

Ревью: Critical отсутствуют. Important stdout encoding в Windows helper исправлен -X utf8; Linux Unicode-путь проверен, native Windows —16. Предыдущие два Important навигации аудита/freshness из раздела55 также исправлены и сохраняются регрессии.

Implementation remote 1c91c8885970335e338ec3a7ed371d110c2226e7, local78c673e542ddb4fe9c8ae68a74bd6cfbe999bb44, tree9a052698bc255f34a60dddede8c481d27fdc5735. Документальные коммиты могут изменять HEAD. CI нового HEAD подтверждать отдельно.

Следующая работа: №5 — Стабильная локальная модель и управление задачами. Не выдавать ACCEPTED по модельным черновикам; реальные issuer/нормы/solver остаются№7–9.
