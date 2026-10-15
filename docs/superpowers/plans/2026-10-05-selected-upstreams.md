# Selected upstream integration plan — 05.10.2026

Goal: добавить шесть выбранных репозиториев из принятого пользователем обзора, сохранив бесплатный локальный путь и инженерные gates.
Architecture: закреплённые git submodules в third_party; выборочные reference paths, отдельно включаемые memory/browser adapters. Внешние SKILL.md не загружаются существующим SkillLoader автоматически. OpenViking отложен.
Spec: обзор ENGINEER_OS_repository_review_2026-10-05.md и запрос «Все репозитории которые нам нужны добавляй».
Execution: самостоятельно в этой сессии; отдельная ветка от опубликованного PDF checkpoint d20d859, без переноса неопубликованных PDF-коммитов.

- [x] Закрепить шесть commits, лицензии, назначение и выбранные пути в integrations/upstreams.json и .gitmodules; получить исходники без исполнения их кода.
- [x] Тесты сначала: локальные URL, запрет redirects, project isolation памяти, недоверенный результат, disabled browser и ограниченные домены, отсутствие evidence acceptance.
- [x] Реализовать engineering/integrations/local_http.py, engineering/memory/agentmemory_http.py и engineering/integrations/browser_use_local.py.
- [x] Добавить CLI scripts/integration_tools.py: status, memory-recall, browser-run. Не включать runtime автоматически, не ставить платные провайдеры.
- [x] Документировать использование selected scientific/security/diagram/harness references; настройки локального runtime и Windows. Опциональные зависимости отдельно.
- [x] Полный unittest, Node проверки, compileall и diff-check; проверить pins. Live AgentMemory/Ollama/Windows отдельно NOT_RUN, если сервисов нет.
- [ ] Commit и публикация отдельной ветки/PR; актуализировать ту же карту проекта с точным scope и результатами.

Review focus: память другого проекта; пустой/некорректный backend response; redirects на внешний host; отключённый инструмент; неподтверждённый текст не превращается в инженерное принятие.
