# Выбранные upstream-подключения ENGINEER OS

Закреплены шесть репозиториев как git submodules в `third_party/`; точные commits, лицензии и выбранные пути находятся в [upstreams.json](upstreams.json). Исходники сторонних проектов не исполняются при запуске ядра и не загружаются автоматически SkillLoader. OpenViking отложен.

## Подготовка источников

В существующем checkout после получения этой ветки:

```powershell
git submodule update --init --depth 1 -- third_party/browser-use third_party/agentmemory third_party/scientific-skills third_party/diagram-design third_party/cybersecurity-skills third_party/harness-patterns
py -3.13 scripts/integration_tools.py status
```

Это загрузка исходников закреплённых версий, а не установка всех их runtime-зависимостей. На новой машине можно клонировать ветку с `--recurse-submodules`. Обновления upstream выбирать и проверять вручную, не использовать `git submodule update --remote` в рабочем режиме.

## Что применять

| Инструмент | Выборочные источники | Применение |
|---|---|---|
| Scientific skills | skills/sympy, statistical-analysis, matplotlib, scientific-critical-thinking, geopandas | Формулы, единицы, анализ измерений и графики. Следовать зависимостям конкретного навыка в отдельном окружении |
| Diagram Design | skills/diagram-design/references/type-architecture.md и assets/example-architecture.html | Карта архитектуры и доказательств; убрать внешние Google Fonts для автономного экспорта |
| Cybersecurity skills | testing-api-for-broken-object-level-authorization, testing-jwt-token-security, testing-prompt-injection-in-rag-pipelines | Свои тестовые пользователи/проекты, ожидаемые запреты, защита от инструкций во входных документах. Не выполнять штатные атакующие scripts без адаптации |
| Harness patterns | README.md | Checkpoints, ограниченные инструменты, воспроизводимые результаты, восстановление очереди; не новый движок |
| Agent Memory | src/triggers/api.ts; наш AgentMemoryHTTPAdapter | Только scoped/latest контекст проекта, UNVERIFIED / NOT_EVIDENCE |
| Browser Use | browser_use; наш run_browser | Явно включаемый локальный браузер + Ollama; отдельный временный профиль и разрешённые домены |

Полные SKILL.md доступны как reference в исходниках, но не являются автоматически принятыми инженерными инструкциями. Пользовательское ТЗ, AGENTS.md, evidence gates и FINAL AUDIT сохраняют приоритет. Ссылки на нормы/решения проверять по их источникам.

## Agent Memory

Требует Node>=20 и iii engine 0.22.1. Для запуска пользоваться README закреплённого submodule: Windows `iii.exe` либо WSL2/Docker. Собрать именно эту checkout-версию; не использовать незакреплённый `npx ...@latest`. Запуск сервиса не включён в запуск ENGINEER OS автоматически.

Для локального бесплатного режима BM25 не требует ключа. LLM-компрессию не включать до выбора бесплатного локального провайдера; ключевые данные проекта не отправлять в облако. Опциональные local embeddings требуют загрузки модели и отдельной проверки русского поиска.

После запуска сервиса на 127.0.0.1:3111:

```powershell
# Авторизация включена upstream по умолчанию. Клиент читает ~/.agentmemory/secret
# только для loopback-сервера; явный AGENTMEMORY_SECRET имеет приоритет.
py -3.13 scripts/integration_tools.py memory-recall --enable --project engineer-os --query "где остановились"
```

Используется реальный REST endpoint `GET /agentmemory/memories?project=...&q=...&latest=true&limit=10`, подтверждённый по закреплённому api.ts. Это поиск сохранённых memories, не всех hook-observations. Пустая память даёт пустой контекст. Чужой project, устаревшая запись, malformed/duplicate ответ дают отказ. Адаптер не сохраняет память, не превращает ответы в AgentResult и не выдаёт ACCEPTED. Для наполнения использовать штатный Agent Memory plugin/capture workflow выбранного локального агента; карта остаётся самостоятельным входом нового чата.

## Browser Use + Ollama

Подготовить отдельное окружение Python>=3.11. Установка бесплатных библиотек потребует сети; локальное выполнение требует браузера и установленной модели Ollama.

```powershell
py -3.13 -m venv .engineer-os/integrations-venv
.engineer-os/integrations-venv/Scripts/python.exe -m pip install -r requirements-integrations.txt
$env:ANONYMIZED_TELEMETRY="false"
$env:BROWSER_USE_CLOUD_SYNC="false"
.engineer-os/integrations-venv/Scripts/python.exe scripts/integration_tools.py browser-run --enable --domain 127.0.0.1 --task "Открой http://127.0.0.1:8080 и опиши видимые элементы без внесения изменений"
```

При отсутствии Chromium следовать локальной установке браузера из закреплённого Browser Use README. Облачный Browser Use и платные LLM не нужны этому адаптеру. Домены ограничивают навигацию; это не полноценная сетевая песочница и не гарантия отсутствия сетевых ресурсов внутри разрешённой страницы. Для проверки автономности отдельно контролировать исходящие соединения.

Без `--enable` оба runtime-инструмента откажутся запускаться. Браузерный текст — NOT_EVIDENCE; модель не принимает инженерные решения вместо ядра. Для текстовой qwen3:8b отключена передача изображений. Запросы Ollama обходят переменные прокси и не следуют redirects; запрос модели ограничен 60 секундами, выполнение агента — 300 секундами. Профиль, downloads и рабочие файлы временные; отдельный каталог screenshots, созданный закреплённым Agent, удаляется при штатной очистке. Аварийное завершение процесса может оставить временные файлы.

Browser Use применяет собственные правила доменов: корневой домен также разрешает его www-вариант. Поэтому список hostnames не является строгой изоляцией каждого hostname/порта. Wildcards и URL-префиксы в нашем CLI не принимаются. Наш Windows/Ollama/AgentMemory live smoke пока NOT_RUN; качество qwen3:8b в браузерных сценариях не установлено.

## Проверки этой поставки

Тестируется наш контракт и транспорт на локальном синтетическом HTTP-сервере. Полные upstream suites и научные окружения отдельно не проверялись. Успех наших unit-тестов не означает, что весь набор навыков или Windows runtime настроен. Текущий PDF BLOCK эти подключения не снимают.
