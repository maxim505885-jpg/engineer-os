# Выполнение шести этапов — проверенные результаты

Статус: IN_PROGRESS. Все шесть этапов ещё не закрыты. Этот документ не является
FINAL_AUDIT или разрешением выпуска. Работы ведутся в отдельном managed worktree
на `codex/v1-completion-20261015`; пользовательский dirty checkout не обновлялся.

|Этап|Выполнено и проверено|Что остаётся|
|---|---|---|
|1. Сборка и окружение|T01: manifest/API/UI/worker identity; Windows Start/Start/Stop на18768; старый8765 правильно отклонён без остановки. T02: explicit offline probes PDF/OCR/IFC/beam|T02: воспроизводимый wheel/model profile, защищённый Office renderer, offline tables; T12: поставка именно этой сборки|
|2. Документы и ТЗ|Повторно сверены все29исходников,828577307байт: SHA-256 совпали с corpus manifest,0добавлений/удалений|T03/T04: source-bound Windows layout, все объекты/формулы/ячейки и критические числа; image-only ТЗ и полнота V4. Наличие текста не закрывает эти проверки|
|3. Приёмка и нормы|T05: явный локальный issuer, типизированные подписи, отзыв и freshness; UI; узкий положительный цикл PROJECT/plaintext через production issuer|Полная предметная приёмка T05 после T04/T06; T06 квалифицированный каталог полных нормативных источников и предметные сравнения|
|4. Расчёты/CAD/IFC в приложении|ENGINEERING_RUN, immutable bounded inputs, SI calculations; Chromium rectangle/beam; Windows bounded child; IFC upload→bounded inventory→элементы/GUID/receipt; cross-project isolation|Полная квалификация T07; CAD T08; IFC geometry/requirements/diff/GUID Evidence T09; исходы обоих DWG; независимый реальный IFC|
|5. Реальная приёмка, память, итог|Предварительные выводы сохранены; controlled production issuer→case→FINAL_AUDIT→memory проходит с сохранением PROJECT scope, source change/revocation снимают доверие|T10 положительный source-backed realcase; T11 FINAL DOCX/PDF. Тестовый эталон не принимается за обследованный объект|
|6. Windows и выпуск|Schema3 migration recovery, backup/restore журнала проверок и engineering inputs проверены; пользовательский8765 оставлен работающим|T12 reboot/offline/update/rollback всей поставки; T13 exact-head CI/release gates/main/tag/дистрибутив. Релиз не объявлен|

## Проверки текущего пакета

- 48 focused profile/OCR/tooling/startup tests: PASS.
- 67 worker/HTTP/CORE integration tests: PASS.
- 49 migration/backup/build tests: PASS.
- 38 calculation tests: PASS, включая реальные Windows beam/frame child и
  отрицательную пробу ограничения памяти Windows Job Object.
- 31 process/source/profile boundary tests: PASS.
- Chromium: desktop/mobile rectangle, actual bounded beam, no accepted Evidence,
  cross-project reset: PASS. Existing jsdom chat/Drive workflows: PASS при
  отдельном повторе; один Drive bootstrap timeout при concurrent suite зафиксирован.
- Fresh full native Windows pass: 1196tests,34skipped,1failure. Единственный
  оставшийся сбой — реальная OCR-ошибка «Прогиб20мм»→«Прогид20мм».
- Architecture/repository guards, dependency consistency, JS syntax: PASS.
- Независимое code review: найден один P2 — перенос видимых расчётных данных между
  проектами. Воспроизведён failing browser test, исправлен и подтверждён PASS.

Число тестов не является процентом готовности. Installed Tesseract fast models
остаются исходным профилем. Отдельные официальные tessdata_best rus/eng оценены
и отклонены из-за5расхождений; installed models и исходники не заменены.

## Дополнение T05: локальный issuer

131 интеграционный тест PASS: issuer/HTTP, требования, real case, FINAL_AUDIT,
память, черновые выводы, backup/restore и automatic analysis. Chromium
desktop/mobile: явная выдача решения по P, source-review invalidation,
очистка формы при смене проекта PASS. Независимое чтение кода: actionable
замечаний нет; независимый запуск тестов ограничен sandbox и не объявлен PASS.

Поддерживаемая область принятия — только `PROJECT_PLAINTEXT_REPORT_REVIEW_ONLY`,
`actual_structure_verified=false`. ТЗ должно быть полным небольшим TXT/MD;
image-only ТЗ объекта этот путь не закрывает. Классы F/M/T/C и DOMAIN не
принимаются. Детали: `docs/engineering-verification.md`. Общая свежая регрессия
этого пакета записывается отдельно в ledger; прежние1196tests относятся к T07.

Свежая общая Windows-регрессия T05: 1216tests,34skipped,1failure за323.514s.
Сбой прежний: реальная OCR-цитата «Прогиб20мм» распознаётся «Прогид20мм».
Assert и эталон не ослаблены. Общий suite не PASS, выпуск остаётся открыт.
Пользователь подтвердил, что папка «ДЛЯ ИИ» содержит весь предоставленный
комплект; отсутствующие IFC/SCAD и недоступные vendor results учитываются
как ограничения этого комплекта, а не как обещанные дополнительные файлы.

## Дополнение T09: декларации IFC в приложении

Включён только IFC_INVENTORY. Оригинал до50MiB сохраняется без автоматического
разбора. Явная задача копирует проверенные байты во временную папку; native
parser запускается после применения того же Job Object/RLIMIT boundary,
что используется расчётами. Рост исходника ограничен при хешировании и
копировании; SHA перепроверяется после задачи. В UI показаны типы/GUID и
полная квитанция; данные PROJECT, acceptance=false, Evidence автоматически
не регистрируется. Geometry/requirements/diff и GUID Evidence не включены.

104 интеграционных теста PASS, включая реальный Windows child, отказ при16MiB,
отмену до запуска, source-change negative, source growth и backup/build/HTTP.
Chromium: rectangle+actual beam, IFC inventory desktop/mobile, scoped review
PASS; смена проекта очищает результаты. Независимое чтение кода без actionable
замечаний; независимые tests недоступны из-за sandbox temp permissions.
Добавлены optional Windows/Linux CI checks; пока это настройка, не receipt CI.
Общая регрессия нового пакета записывается в ledger после завершения.

Свежая общая Windows-регрессия после IFC-пакета: 1223tests,34skipped,
1failure за346.688s. Единственный сбой — прежнее OCR «Прогиб20мм»→«Прогид20мм».
Новых сбоев в этом проходе нет; общий suite не объявляется PASS. Новый код
испытан в изолированной ветке, пользовательская работающая сборка не заменена.

На опубликованном87ea23b Linux optional tests и три Chromium-сценария PASS,
security guard PASS. Windows optional CI выявил два неверных отрицательных
теста: импорт библиотек не обязан превысить16MiB committed memory. Добавлен
фиксированный diagnostic child, выделяющий и затрагивающий64MiB: при обычном
лимите PASS, при16MiB отказ. Он не является доступным engineering tool.
40 focused worker/calculation tests PASS после исправления. Прежние1223tests
относятся к дереву до этой правки; результаты нового exact-head CI учитываются
отдельно. Изолированный jsdom workflow PASS; concurrent Drive-status timeout
при общей регрессии сохранён как наблюдение, а не скрыт повтором.

После исправления на90b0d26: Core Tests, Security Guard и optional engineering
workflow на Windows/Linux PASS, включая фиксированную память и3browser flows.
Полный Windows runtime workflow оценивается отдельно. Дополнительно локальный
Chromium теперь проверяет PLANAR: JSON схемы/закреплений/нагрузок, видимый SVG,
SI inputs и перемещение консоли по независимой аналитической формуле. PASS;
новый browser test не меняет production calculation code. Последующий exact-head
CI относится к новому коммиту теста, а не автоматически наследует90b0d26 PASS.

Отдельный V01 остаётся открытым: сохранённые результаты9ЛИРА-моделей ранее
недоступны через vendor API (0x8000FFFF); наличие `.lir` не доказывает расчёт.
В текущей папке нет IFC/SCAD. Требуются достаточные реальные источники, полные
нормативные тексты и ответственный reviewer для предметной приёмки.
