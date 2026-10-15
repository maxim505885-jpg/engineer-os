# Пункт 1: единая проверяемая локальная версия

Основа кандидата — PR49, remote commit 22641c3d3dead8f6619fbda2bff2f758705e46bd,
local commit 478dfe56e27276917f8ed6d305eb178ba8dc40b3, одинаковое дерево
92b593a6c9245725fba621e33431551e46be9c94. Новая ветка
fix/local-release-readiness-20261006 добавляет окружение, актуальные инструкции и CI.
Это кандидат для проверки; main, deployment и Windows не обновлены.

## Окружение и проверки

- requirements-local-app.txt включает закреплённый PyMuPDF 1.26.6 через прежний
  requirements-pdf-review.txt. Чистая Python 3.12 venv установлена без наследования
  system site-packages; pip check PASS.
- Из минимальной venv actual launcher + HTTP/jsdom кабинет и Drive scenarios PASS.
  Модель/Google transport synthetic, OCR не установлен; Node нужен только тестам.
- Первый полный прогон чистой venv дал 3 ERROR: test_preview_is_bounded_png_and_original_unchanged,
  test_rotated_preview_has_highlight_at_rotated_location,
  test_rotated_cropped_pages_keep_source_outline_in_all_orientations — missing PIL.
  requirements-dev.txt добавляет Pillow 12.3.0 только для pixel assertions.
- jsdom 26.1.0 и транзитивные зависимости закреплены e2e/package-lock.json;
  npm ci установил 39 пакетов. Offline npm ci не прошёл из-за отсутствующего
  xmlchars в cache; обычный npm ci PASS. Offline bootstrap Node не заявляется.
- Исправлен workflow: Python 3.12 вместо 3.11, feat/** pushes и PR на любую base,
  требования разработки, pip check, JS syntax, 4 dashboard tests, full Python suite,
  compileall и оба actual HTTP/jsdom сценария через npm test.
- Обновлены local-app/README/extraction инструкции: preview20 отдельно от
  автоматического PDF-анализа, большие документы по частям, resume ограничен,
  live OCR/model/Windows не выдаются за проверенные.

Финальные результаты команды Python/CI и точные SHA после публикации фиксируются
в живой карте ENGINEER_OS_PROJECT_MAP.md и утверждённом плане. Локальный зелёный
прогон не означает успешный GitHub Actions run.

## Порядок интеграции

Кандидат содержит наследуемый код цепочки PR38 →39 →40 →41 →42 →43 →44 →45
→46 →47 →48 →49 и выбранные интеграции PR37. Каждый stacked PR направлен на
предыдущую ветку; не сливать их в случайном порядке и не считать PR49 полной
заменой main только по статусу mergeable. PR37 сам основан на опубликованной
PDF-ветке. Общую PDF/runtime цепочку до main нужно проверить на отдельном
интеграционном кандидате, включая пересекающиеся старые PR; опубликованные refs
и точные деревья — основание для отбора, не номер PR.

После зелёного CI кандидата: проверить diff и состав дерева относительно main,
выделить нужную цепочку зависимостей, исключить дубли альтернативных веток,
подготовить reviewable интеграционный PR и проверять CI его точного commit.
Слияние/deployment — отдельные действия, в этой работе не выполняются.

## Отдельные PDF-исправления

Неопубликованный recovery code e649885 и replay summary 13200ab из отдельного
checkout не включены в этот кандидат. Для включения нужны собственный diff,
source-bound replay и соблюдение ранее зафиксированной границы публикации.
Прежний V4 результат 523 UNCERTAINTY/11 BLOCK остаётся историческим проверенным
результатом; full acceptance не выдан. Кабинет не зависит от устранения этих
11 BLOCK для проверки своего пользовательского маршрута.

## Решения выполнения

Ruling: пункт 1 не закрывается одним обновлением документации — нужен CI на
точном кандидате и проверенный путь интеграции; иначе легко принять локальное
дерево за установленную пользователю версию.

Ruling: OCR lock будет закреплён в пункте 2 после живой проверки совместимости.
Сейчас minimal окружение воспроизводимо, отдельное OCR окружение описано, но
его готовность не заявляется. Цена неверного предположения — parser failure,
поэтому live test предшествует пометке готовности.

Ruling: новый Python код не нужен для этого подэтапа. Верификация конфигурации
идёт настоящими установками, existing regression suite и actual launcher;
тесты, зеркалящие текст инструкций или YAML, не добавлены.
