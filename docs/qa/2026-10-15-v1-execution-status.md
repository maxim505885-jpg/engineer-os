# Выполнение шести этапов — проверенные результаты

Статус: IN_PROGRESS. Все шесть этапов ещё не закрыты. Этот документ не является
FINAL_AUDIT или разрешением выпуска. Работы ведутся в отдельном managed worktree
на `codex/v1-completion-20261015`; пользовательский dirty checkout не обновлялся.

|Этап|Выполнено и проверено|Что остаётся|
|---|---|---|
|1. Сборка и окружение|T01: manifest/API/UI/worker identity; Windows Start/Start/Stop на18768; старый8765 правильно отклонён без остановки. T02: explicit offline probes PDF/OCR/IFC/beam|T02: воспроизводимый wheel/model profile, защищённый Office renderer, offline tables; T12: поставка именно этой сборки|
|2. Документы и ТЗ|Повторно сверены все29исходников,828577307байт: SHA-256 совпали с corpus manifest,0добавлений/удалений|T03/T04: source-bound Windows layout, все объекты/формулы/ячейки и критические числа; image-only ТЗ и полнота V4. Наличие текста не закрывает эти проверки|
|3. Приёмка и нормы|Существующий fail-closed gate сохранён; unsigned inventory/model output не выдаёт engineering_verified|T05 production review issuer; T06 квалифицированный каталог полных нормативных источников и предметные сравнения|
|4. Расчёты/CAD/IFC в приложении|Новая ENGINEERING_RUN в существующей очереди, immutable bounded input records, typed SI calculations; Chromium rectangle/beam; Windows bounded beam/frame child; схема/цифры/полная квитанция; cross-project isolation fix|Полная квалификация T07, bounded CAD/IFC jobs и GUID Evidence T08/T09; исходы обоих DWG; независимый реальный IFC|
|5. Реальная приёмка, память, итог|Предварительные выводы и запрет автоматического принятия сохранены|T10 положительный source-backed realcase; T11 accepted-origin memory и FINAL DOCX/PDF. Тестовый эталон не принимается за обследованный объект|
|6. Windows и выпуск|Проверены schema2 migration recovery, backup/restore engineering inputs; пользовательский8765/PID39004 оставлен работающим|T12 reboot/offline/update/rollback всей поставки; T13 exact-head CI/release gates/main/tag/дистрибутив. Релиз не объявлен|

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

Отдельный V01 остаётся открытым: сохранённые результаты9ЛИРА-моделей ранее
недоступны через vendor API (0x8000FFFF); наличие `.lir` не доказывает расчёт.
В текущей папке нет IFC/SCAD. Требуются достаточные реальные источники, полные
нормативные тексты и ответственный reviewer для предметной приёмки.
