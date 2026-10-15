# ENGINEER OS: проверка инструментов из двух статей, 2026-10-04

Источники: [Хабр: 100 проектов](https://habr.com/ru/articles/1075078/) и [Computerra: 23 проекта](https://www.computerra.ru/355671/github-obzor-top-samyh-poleznyh-i-neobychnyh-repozitoriev-iyulya-2026/).

Объём проверки: актуальные README и metadata каждого из 100 репозиториев, сопоставление со стеком и gates ENGINEER OS; для кандидатов дополнительно лицензии, требования и профильный код. Это отбор совместимости, не исчерпывающий аудит всех исходников/зависимостей и не доказательство качества OCR. Большие каталоги изучены как каталоги; вложенные тысячи проектов не запускались. Число звёзд и маркетинговые проценты не использованы как доказательство.

## Что реально изменено и проверено

- Обзор сайта: 4 параллельных точных HEAD/count запроса вместо 7 последовательных выборок ID с лимитом 1000. Ошибка отображается как неизвестное значение, а не ложный ноль. Измерения ускорения production-сайта не проводились.
- `scripts/pdf_source_preflight.py`: hash исходника, оригинальные номера страниц, нативный текст, raster/vector routing, эффективный DPI изображений; поворот страницы учтён. Это диагностические метаданные NOT_EVIDENCE, без автоматического снятия BLOCK.
- На оригинальном V4 с SHA256 `b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916` проверены все 534 страницы: 318 смешанных, 156 с нативным текстом, 20 raster, 40 vector без нативного текста в эвристическом body window. Классы не являются проверкой полноты страницы.
- Свежие локальные проверки: 186 Python tests, 4 Node tests, JavaScript syntax, compileall. Реальные PDF fixture-тесты запускаются в CI с PyMuPDF==1.26.6.
- OfficeCLI v1.0.153: Linux binary проверен по release digest; `view ... stats --json` и `validate ... --json` прошли на доступном DOCX. Это OpenXML/schema review, не инженерный PASS. Windows installer закреплён по SHA256, но не исполнялся: Windows/PowerShell недоступны.
- codebase-memory-mcp v0.11.0: checksum и CLI help проверены; index_repository завершился ошибкой process-fingerprint в этой среде. Индекс не создан, интеграция не активирована.

## PDF: что поможет и что не снимет BLOCK

1. Сначала preflight; нативные таблицы проверять по сетке и исходному тексту, raster области отправлять в OCR, vector чертежи просматривать отдельно. Маршрут страницы — эвристика, поля/штампы тоже требуют проверки.
2. Docling остаётся основным parser. `book-to-skill` использует его же, а не альтернативный OCR для сканов.
3. RAGFlow/DeepDoc — главный независимый кандидат для сравнения таблиц. Актуальный OSS 1.0.0-rc1 перешёл на Go/CPU DeepDoc; `internal/deepdoc/native/tsr.go` выдаёт boxes таблиц/строк/столбцов, не автоматически проверенные заполненные ячейки. `ocr_rec.go` зависит от rec.ort/ocr.res. Кириллицу конкретного model bundle надо подтвердить тестом, а не названием OCR. Рекомендуемая стартовая среда полного RAGFlow: 4 CPU, 16 GB RAM, 50 GB disk и Docker. Existing `deepdoc_http.py` уже есть, но реально работающий service, /health и /predict контракт новой версии не проверены; не считать adapter интеграцией в production.
4. PageIndex SDK local предназначен для text-based PDF без OCR/image understanding. Existing `pageindex_local.py` — retrieval adapter; LLM/Ollama runtime здесь не проверен. Search не заменяет extraction completeness.
5. Upscayl использует AI guessing деталей и Vulkan GPU. Дорисованные цифры/буквы нельзя использовать для закрытия engineering BLOCK; оригинал и hash должны сохраняться. Поэтому не включён в evidence pipeline.
6. Headroom/Caveman — возможная экономия вспомогательных логов; исходный текст evidence, координаты, числа, units и нормативные ссылки сохранять без потерь. Их заявленные benchmark проценты к V4 не переносятся.

Текущий подтверждённый checkpoint table-normalization: 25 страниц восстановлены для прежних table blockers, 103 страницы остаются BLOCK в combined recovery; весь документ BLOCK. Новая диагностика не уменьшает это число. Для следующего сравнения взять p15–16 как известную таблицу, p5–7 как плохой raster/mixed текст, p499 как vector, плюс реальные оставшиеся table blockers. Измерять сохранность Cyrillic/ячеек/bbox, SHA256/page, wall time и peak RSS; результаты держать неподтверждёнными до визуальной сверки.

## Запуск имеющейся диагностики

Из project venv с зависимостью `requirements-pdf-review.txt`, для выбранных исходных страниц:

```powershell
python scripts/pdf_source_preflight.py "C:\path\V4.pdf" --sha256 b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916 --pages 5 6 7 15 16 499 --output ".engineer-os/v4-source-preflight.json"
```

Без `--pages` проверяются все страницы. Exit 0 означает успешно выполненную диагностику, НЕ документ PASS/ACCEPTED. Ошибка исходника/hash возвращает BLOCK и exit 2. Глобально Docling не устанавливать.

Optional OfficeCLI для Word/Excel/PowerPoint, без PATH/MCP/профилей:

```powershell
powershell -File scripts/install_officecli.ps1
& ".\.engineer-os\tools\officecli\officecli.exe" --version
& ".\.engineer-os\tools\officecli\officecli.exe" view "C:\path\document.docx" stats --json
& ".\.engineer-os\tools\officecli\officecli.exe" validate "C:\path\document.docx" --json
```

Installer Windows x64 ожидает SHA256 `05dd712595690672ea1c220a516c0996a27f7c3e7f870a270c19d538e9fc04f3`. Успех schema validation не присваивает ACCEPTED. PDF экспорт OfficeCLI не является извлечением исходного PDF.

## Каждый из 100 проектов Хабра

Лицензия ниже — metadata/README и выборочная LICENSE-проверка для составных условий. `Не подтверждена` запрещает считать код свободным для копирования. Неустановленные проекты не объявляются рабочими интеграциями.

| № | Репозиторий | Лицензия/ограничение | Решение для ENGINEER OS |
|---|---|---|---|
| 1 | [openclaw/openclaw](https://github.com/openclaw/openclaw) | MIT | Личный агент и мессенджеры; дублирует runtime, не проверяет PDF. |
| 2 | [obra/superpowers](https://github.com/obra/superpowers) | MIT | Применяем практики диагностики, тестов и ревью; доступный skill уже используется, второй пакет не устанавливаем. |
| 3 | [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | MIT | Память личного агента; не заменяет Evidence Register и происхождение данных. |
| 4 | [n8n-io/n8n](https://github.com/n8n-io/n8n) | Sustainable Use / Enterprise | Автоматизация Drive/очередей возможна позже; дополнительный сервис и специальные лицензии. |
| 5 | [Significant-Gravitas/AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) | MIT / PolyForm Shield | Полная платформа агентов; дублирует приложение, отдельные MIT/PolyForm части. |
| 6 | [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl) | AGPL-3.0 | Для будущего сбора официальных нормативных веб-источников; не решает потерю PDF-ячеек. |
| 7 | [f/prompts.chat](https://github.com/f/prompts.chat) | MIT code / CC0 prompts | Примеры промптов для разработки; не нормативы и не проверенные инженерные инструкции. |
| 8 | [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui) | AGPL-3.0 | Генератор изображений; не инструмент достоверного восстановления скана. |
| 9 | [Snailclimb/JavaGuide](https://github.com/Snailclimb/JavaGuide) | Apache-2.0 | Java-справочник; другой стек, учебные материалы. |
| 10 | [langgenius/dify](https://github.com/langgenius/dify) | Dify modified Apache | Полная RAG-платформа; дополнительный Docker-стек, не нужна миграция существующего приложения. |
| 11 | [open-webui/open-webui](https://github.com/open-webui/open-webui) | Open WebUI custom | Сохраняем имеющуюся связку Ollama/Open WebUI; состояние Windows отдельно не проверено. |
| 12 | [langchain-ai/langchain](https://github.com/langchain-ai/langchain) | MIT | Компоненты RAG возможны позже; текущие adapters/gateway уже обеспечивают необходимую границу. |
| 13 | [x1xhlol/system-prompts-and-models-of-ai-tools](https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools) | GPL-3.0 | Архив чужих промптов; не источник инженерных доказательств. |
| 14 | [github/spec-kit](https://github.com/github/spec-kit) | MIT | Полезны сценарии и требования; не добавляем второй обязательный процесс поверх существующих AGENTS/tests. |
| 15 | [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI) | GPL-3.0 | Генерация медиа; не применять для восстановления букв и чисел в доказательствах. |
| 16 | [microsoft/generative-ai-for-beginners](https://github.com/microsoft/generative-ai-for-beginners) | MIT | Учебный курс; справочный материал, не runtime. |
| 17 | [supabase/supabase](https://github.com/supabase/supabase) | Apache-2.0 | Имеющаяся база/auth/storage; улучшены текущие точные счётчики, миграция не нужна. |
| 18 | [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli) | Apache-2.0 | Дополнительный кодинговый CLI; не нужен новый провайдер/ключ для текущего этапа. |
| 19 | [rasbt/LLMs-from-scratch](https://github.com/rasbt/LLMs-from-scratch) | Составная; проверить конкретный файл | Обучение LLM с нуля; не соответствует сроку, ресурсам и задаче OCR. |
| 20 | [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) | Apache-2.0 | Сжатие логов возможно отдельно; нельзя сжимать канонические evidence, числа и нормативные ссылки. |
| 21 | [hacksider/Deep-Live-Cam](https://github.com/hacksider/Deep-Live-Cam) | AGPL-3.0 | Подмена лиц; не имеет применения в обследовании зданий и PDF. |
| 22 | [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) | MIT | Каталог MCP; каждый сервер требует отдельной проверки, каталог не является готовой интеграцией. |
| 23 | [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem) | Apache-2.0 | Память сессий, hooks и облачные варианты; не подключаем автоматически к инженерным данным. |
| 24 | [infiniflow/ragflow](https://github.com/infiniflow/ragflow) | Apache-2.0 | Приоритет независимого сравнения OCR/TSR; current DeepDoc CPU, но полного сервиса не разворачиваем в малопамятном runtime. |
| 25 | [koala73/worldmonitor](https://github.com/koala73/worldmonitor) | AGPL-3.0 | Мировые новости; не обследование и не нормативная проверка объекта. |
| 26 | [lobehub/lobehub](https://github.com/lobehub/lobehub) | LobeHub Community | Ещё одна платформа агентов; не переносим существующий runtime. |
| 27 | [bytedance/deer-flow](https://github.com/bytedance/deer-flow) | MIT | Сложный harness с sandboxes; дублирование инфраструктуры, не OCR. |
| 28 | [netdata/netdata](https://github.com/netdata/netdata) | GPL core / NCUL UI | Мониторинг CPU/RSS полезен при диагностике OOM; отдельный демон сейчас не установлен. |
| 29 | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) | MIT | Правила интерфейса можно применять точечно; не делаем редизайн и не устанавливаем рекламируемые API. |
| 30 | [D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling) | BSD-3-Clause | Будущий сбор официальных нормативных страниц; сначала источник, версия, дата и hash, а не автоматическое принятие. |
| 31 | [unslothai/unsloth](https://github.com/unslothai/unsloth) | Apache-2.0 | Локальный inference/finetuning; нет проверенной видеокарты и обучающего датасета. |
| 32 | [hiyouga/LlamaFactory](https://github.com/hiyouga/LlamaFactory) | Apache-2.0 | Finetuning моделей; отложить до размеченного инженерного набора, не лечит нынешнее извлечение. |
| 33 | [OpenBB-finance/OpenBB](https://github.com/OpenBB-finance/OpenBB) | NOASSERTION | Финансовые данные; не относится к текущему инженерному документу. |
| 34 | [daytonaio/daytona](https://github.com/daytonaio/daytona) | Лицензия archived tag; не интегрируем | Открытая база архивирована, разработка перенесена в private; не брать как новый фундамент. |
| 35 | [code-yeongyu/oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent) | SUL-1.0 по README | Надстройка кодинговых агентов со специальной лицензией; не обязательная зависимость приложения. |
| 36 | [santifer/career-ops](https://github.com/santifer/career-ops) | MIT | Поиск работы; вне задачи. |
| 37 | [headroomlabs-ai/headroom](https://github.com/headroomlabs-ai/headroom) | Apache-2.0 | Экономия контекста возможна только на вспомогательных логах после отдельного теста сохранности фактов. |
| 38 | [microsoft/AI-For-Beginners](https://github.com/microsoft/AI-For-Beginners) | MIT | Учебный курс по AI; не продуктовый компонент. |
| 39 | [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) | MIT | Спецификации и сценарии полезны как практика; не добавляем второй CLI и каталог требований без необходимости. |
| 40 | [docling-project/docling](https://github.com/docling-project/docling) | MIT | Основной уже используемый parser; улучшение адаптера/региональных режимов вместо смены всей платформы. |
| 41 | [shanraisshan/claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice) | MIT | Практики разработки справочно; не копируем автоматические hooks и конфигурации без просмотра. |
| 42 | [mem0ai/mem0](https://github.com/mem0ai/mem0) | Apache-2.0 | Память предпочтений возможна позже; модельная память не равна проверенному evidence. |
| 43 | [asgeirtj/system_prompts_leaks](https://github.com/asgeirtj/system_prompts_leaks) | CC0-1.0 | Чужие системные промпты; нет пользы для снятия PDF BLOCK. |
| 44 | [sansan0/TrendRadar](https://github.com/sansan0/TrendRadar) | GPL-3.0 | Мониторинг новостей; для нормативов нужны официальные версии, не новостные сводки. |
| 45 | [microsoft/autogen](https://github.com/microsoft/autogen) | CC-BY docs; код проверять отдельно | Maintenance mode; не добавляем новый агентный framework поверх работающего runtime. |
| 46 | [meilisearch/meilisearch](https://github.com/meilisearch/meilisearch) | MIT / BUSL EE | Поиск по принятым данным возможен позже; отдельный индекс/сервис и смешанные MIT/EE лицензии. |
| 47 | [MemPalace/mempalace](https://github.com/MemPalace/mempalace) | MIT | Дословная память с поиском интересна для сессий; не переносим инженерную истину в ещё одно хранилище. |
| 48 | [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | MIT | Команды/Flows агентов; дублирует существующую оркестрацию и не восстанавливает таблицы. |
| 49 | [zylon-ai/private-gpt](https://github.com/zylon-ai/private-gpt) | Apache-2.0 | Локальный AI API/RAG; gateway уже имеется, PDF доказательства всё равно требуют проверки. |
| 50 | [AntonOsika/gpt-engineer](https://github.com/AntonOsika/gpt-engineer) | MIT | Генерация новой кодовой базы; противоречит продолжению существующего проекта. |
| 51 | [lencx/ChatGPT](https://github.com/lencx/ChatGPT) | Не подтверждена | Оболочка ChatGPT; не инженерная функциональность сайта. |
| 52 | [aaif-goose/goose](https://github.com/aaif-goose/goose) | Apache-2.0 | Дополнительный desktop/CLI агент; не заменяет parser и gate. |
| 53 | [dbeaver/dbeaver](https://github.com/dbeaver/dbeaver) | Apache-2.0 | SQL-клиент может помочь ручной диагностике Supabase; необязателен, существующие инструменты достаточны. |
| 54 | [jamiepine/voicebox](https://github.com/jamiepine/voicebox) | MIT | Речь и диктовка позже; не OCR и не расчётная часть. |
| 55 | [calesthio/OpenMontage](https://github.com/calesthio/OpenMontage) | AGPL-3.0 | Генерация видео; вне этапа. |
| 56 | [ClickHouse/ClickHouse](https://github.com/ClickHouse/ClickHouse) | Apache-2.0 | Аналитическая база для больших потоков; нет основания заменять Postgres/Supabase. |
| 57 | [upscayl/upscayl](https://github.com/upscayl/upscayl) | AGPL-3.0 | НЕ принимать дорисованные AI детали за исходные буквы/числа; GPU/Vulkan, только потенциальное визуальное пособие. |
| 58 | [mudler/LocalAI](https://github.com/mudler/LocalAI) | MIT | Альтернативный локальный model server; нынешний Ollama/gateway уже покрывает этот сценарий. |
| 59 | [rohitg00/ai-engineering-from-scratch](https://github.com/rohitg00/ai-engineering-from-scratch) | MIT | Обучающие примеры; не импортировать демонстрационные ответы как инженерные заключения. |
| 60 | [GitHubDaily/GitHubDaily](https://github.com/GitHubDaily/GitHubDaily) | CC-BY-NC-ND по README | Каталог проектов; не подключаем в runtime, лицензия материалов отдельная. |
| 61 | [jeecgboot/JeecgBoot](https://github.com/jeecgboot/JeecgBoot) | Apache-2.0 | Java low-code платформа; несоответствие стеку и дублирование приложения. |
| 62 | [elder-plinius/CL4R1T4S](https://github.com/elder-plinius/CL4R1T4S) | AGPL-3.0 | Архив промптов; не инженерные нормы или source evidence. |
| 63 | [zhayujie/CowAgent](https://github.com/zhayujie/CowAgent) | MIT | Личный помощник с управлением компьютером; лишняя инфраструктура на этом этапе. |
| 64 | [Kong/kong](https://github.com/Kong/kong) | Apache-2.0 | API gateway полезен при большом числе сервисов; нынешнему объёму не требуется новый сетевой слой. |
| 65 | [danielmiessler/Fabric](https://github.com/danielmiessler/Fabric) | MIT | Шаблоны AI-сценариев; нормативные выводы не строить на общих промптах. |
| 66 | [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | Apache-2.0 | Видео из HTML; не PDF extraction и не ускорение сайта. |
| 67 | [LibreChat-AI/LibreChat](https://github.com/LibreChat-AI/LibreChat) | MIT | Ещё один чат-интерфейс; сохраняем ENGINEER OS и Open WebUI, не мигрируем. |
| 68 | [agno-agi/agno](https://github.com/agno-agi/agno) | Apache-2.0 | AgentOS/framework; не переносим существующие контракты, статусы и audit в новый runtime. |
| 69 | [reactive-resume/reactive-resume](https://github.com/reactive-resume/reactive-resume) | MIT | Конструктор резюме; вне задачи. |
| 70 | [hpcaitech/ColossalAI](https://github.com/hpcaitech/ColossalAI) | Apache-2.0 | Distributed GPU inference/training; нет такой инфраструктуры и задачи обучения. |
| 71 | [pingcap/tidb](https://github.com/pingcap/tidb) | Apache-2.0 | Другая distributed SQL база; не нужна замена имеющегося Postgres. |
| 72 | [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | MIT | Checkpoints/retries пригодятся при развитии очередей; пока достаточно существующих chunk outputs и resumable batch. |
| 73 | [photoprism/photoprism](https://github.com/photoprism/photoprism) | AGPL + дополнительные условия | Фототека; фото обследования должны быть evidence с привязкой к объекту, не новой отдельной системой. |
| 74 | [mindsdb/mindshub](https://github.com/mindsdb/mindshub) | MIT | Agent workspace; дублирует приложения/агентов, не PDF parser. |
| 75 | [AstrBotDevs/AstrBot](https://github.com/AstrBotDevs/AstrBot) | AGPL-3.0 | Мессенджер-бот; не нужно добавлять новый frontend/runtime. |
| 76 | [The-Vibe-Company/quivr](https://github.com/The-Vibe-Company/quivr) | MIT | Репозиторий переехал и V2 ориентирован на потоки контента/поиск; описание старого RAG в статье устарело. |
| 77 | [RSSNext/Folo](https://github.com/RSSNext/Folo) | AGPL-3.0 | RSS для будущего мониторинга источников; не подтверждает актуальность нормативного требования. |
| 78 | [google-research/google-research](https://github.com/google-research/google-research) | Apache-2.0 | Исследовательский архив; требуется выбор конкретного проекта, общего install для ENGINEER OS нет. |
| 79 | [github/awesome-copilot](https://github.com/github/awesome-copilot) | MIT | Справочник skills; имеющиеся навыки достаточны, не импортировать hooks массово. |
| 80 | [LAION-AI/Open-Assistant](https://github.com/LAION-AI/Open-Assistant) | Apache-2.0 | Исследовательский ассистент; не источник принятых инженерных ответов. |
| 81 | [patchy631/ai-engineering-hub](https://github.com/patchy631/ai-engineering-hub) | MIT | Учебные RAG/OCR примеры; полезны для сравнения, каждый parser/model требует собственного benchmark. |
| 82 | [CopilotKit/CopilotKit](https://github.com/CopilotKit/CopilotKit) | MIT | Agent UI компоненты возможны позже; нынешний frontend vanilla JS, импорт означал бы лишнюю миграцию. |
| 83 | [babysor/MockingBird](https://github.com/babysor/MockingBird) | MIT по README; не интегрируем | Клонирование речи, README отмечает отсутствие активной поддержки; вне PDF этапа. |
| 84 | [Dokploy/dokploy](https://github.com/Dokploy/dokploy) | Специальная; не интегрируем | Self-host deployment возможен при собственном сервере; бесплатная программа не даёт бесплатный сервер и RAM. |
| 85 | [khoj-ai/khoj](https://github.com/khoj-ai/khoj) | AGPL-3.0 | Ещё один document assistant/RAG; не обходит контроль полноты извлечения. |
| 86 | [reworkd/AgentGPT](https://github.com/reworkd/AgentGPT) | GPL-3.0 | Автономный browser agent; не даёт проверенного evidence и дублирует приложение. |
| 87 | [continuedev/continue](https://github.com/continuedev/continue) | Apache-2.0 | README говорит read-only/no active maintenance; не выбирать новой обязательной зависимостью. |
| 88 | [blakeblackshear/frigate](https://github.com/blakeblackshear/frigate) | MIT | NVR/камеры; не текущий анализ PDF. |
| 89 | [VectifyAI/PageIndex](https://github.com/VectifyAI/PageIndex) | MIT | Существующий optional provider оставляем только для поиска; local SDK без OCR не снимает скановые BLOCK. |
| 90 | [DayuanJiang/next-ai-draw-io](https://github.com/DayuanJiang/next-ai-draw-io) | Apache-2.0 | Схемы процессов полезны позже; не структурный расчёт ЛИРА/SCAD и не PDF extraction. |
| 91 | [xitu/gold-miner](https://github.com/xitu/gold-miner) | Не подтверждена | Переводы статей; не первичный нормативный источник. |
| 92 | [explosion/spaCy](https://github.com/explosion/spaCy) | MIT | NLP сущностей/единиц после OCR возможно; не восстанавливает утраченную сетку таблицы. |
| 93 | [TabbyML/tabby](https://github.com/TabbyML/tabby) | Apache core / EE | Coding completion server; дополнительная модель и mixed EE лицензии, не нужен для OCR. |
| 94 | [Pythagora-io/gpt-pilot](https://github.com/Pythagora-io/gpt-pilot) | FSL-1.1-MIT | README сообщает прошлый supply-chain инцидент и отсутствие поддержки; не устанавливаем. |
| 95 | [MadsLorentzen/ai-job-search](https://github.com/MadsLorentzen/ai-job-search) | MIT | Поиск работы; вне задачи. |
| 96 | [lutzroeder/netron](https://github.com/lutzroeder/netron) | MIT | ONNX viewer полезен разработчику OCR при отладке моделей; не исполняет распознавание документов. |
| 97 | [JCodesMore/ai-website-cloner-template](https://github.com/JCodesMore/ai-website-cloner-template) | MIT | Клонирование сайта; не нужно пересобирать текущий ENGINEER OS. |
| 98 | [zeroclaw-labs/zeroclaw](https://github.com/zeroclaw-labs/zeroclaw) | Apache-2.0 | Rust runtime личного агента; не заменяем существующие engineering gates. |
| 99 | [SillyTavern/SillyTavern](https://github.com/SillyTavern/SillyTavern) | AGPL-3.0 | Чат с персонажами; нет пользы для PDF достоверности и расчётной части. |
| 100 | [iOfficeAI/AionUi](https://github.com/iOfficeAI/AionUi) | Apache-2.0 | Ещё одна оболочка CLI-агентов с OfficeCLI; берём OfficeCLI отдельно, без нового приложения. |

## Каждый из 23 проектов Computerra

| Репозиторий | Решение |
|---|---|
| [usestrix/strix](https://github.com/usestrix/strix) | Security scanner: отдельный будущий security review; не PDF. |
| [Dicklesworthstone/destructive_command_guard](https://github.com/Dicklesworthstone/destructive_command_guard) | Не интегрируем: custom rider исключает OpenAI/Anthropic и их агентов. |
| [alibaba/open-code-review](https://github.com/alibaba/open-code-review) | OCR означает code review; не optical character recognition. |
| [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) | Optional code graph; CLI smoke прошёл, index failed process-fingerprint. |
| [andrewyng/aisuite](https://github.com/andrewyng/aisuite) | Providers abstraction; текущий gateway уже поддерживает нужную границу. |
| [asgeirtj/system_prompts_leaks](https://github.com/asgeirtj/system_prompts_leaks) | Чужие промпты не являются инженерным evidence. |
| [virgiliojr94/book-to-skill](https://github.com/virgiliojr94/book-to-skill) | Docling и предварительный OCR; адаптирована идея preflight, без копирования кода. |
| [langchain-ai/openwiki](https://github.com/langchain-ai/openwiki) | Generated code wiki можно позже; не нормативные доказательства. |
| [MadsLorentzen/ai-job-search](https://github.com/MadsLorentzen/ai-job-search) | Поиск работы — вне проекта. |
| [iOfficeAI/OfficeCLI](https://github.com/iOfficeAI/OfficeCLI) | DOCX/XLSX/PPTX review; изолированный smoke успешен, pinned optional installer. |
| [JustVugg/colibri](https://github.com/JustVugg/colibri) | Disk-streaming LLM: нет подтверждённого hardware/budget, не OCR. |
| [huggingface/speech-to-speech](https://github.com/huggingface/speech-to-speech) | Речь — будущая optional функция. |
| [kyutai-labs/pocket-tts](https://github.com/kyutai-labs/pocket-tts) | TTS — не PDF blocker. |
| [agentscope-ai/QwenPaw](https://github.com/agentscope-ai/QwenPaw) | Личный агент — дублирование runtime. |
| [Nutlope/hallmark](https://github.com/Nutlope/hallmark) | UI/design practice можно точечно; не редизайн. |
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | Видео из HTML — вне этапа. |
| [OpenCut-app/OpenCut](https://github.com/OpenCut-app/OpenCut) | Видеоредактор — вне этапа. |
| [bradautomates/claude-video](https://github.com/bradautomates/claude-video) | Видеопроцессы — вне этапа. |
| [earthtojake/text-to-cad](https://github.com/earthtojake/text-to-cad) | Text-to-CAD не расчёт ЛИРА/SCAD и не source drawing verification. |
| [block/buzz](https://github.com/block/buzz) | Chat/task runtime — дублирование. |
| [stablyai/orca](https://github.com/stablyai/orca) | Agent/task platform — дублирование. |
| [different-ai/openwork](https://github.com/different-ai/openwork) | Mixed enterprise/core license и дублирование runtime. |
| [citrolabs/ego-lite](https://github.com/citrolabs/ego-lite) | macOS-first/Windows beta по README; не внедряем на неподтверждённой среде. |

## Границы внедрения

Ни main, ни merge/deploy не выполнены. Runtime зависимости для новых агентных платформ не добавлены. Непроверенный OCR не записан в Supabase/Evidence Register как принятый. Полная extraction и FINAL AUDIT остаются обязательными.
