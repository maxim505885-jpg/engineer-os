# Окружение локального кабинета

## Минимальный режим: чат и native PDF

Python 3.12+ и Ollama с установленной моделью запускаются локально. Кабинет
использует стандартную библиотеку Python и PyMuPDF 1.26.6. Google Drive, Browser
Use, SymPy, Supabase и Docling для этого режима не обязательны.

Linux/macOS, из корня проекта:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-local-app.txt
.venv/bin/python -m pip check
.venv/bin/python scripts/run_local_app.py --no-browser
```

Windows — инструкция подготовлена, проверка её выполнения относится к пункту 9:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-local-app.txt
.\.venv\Scripts\python.exe -m pip check
```

После подготовки запустить Start_ENGINEER_OS.cmd. Он предпочитает .venv,
проверяет Python >=3.12 и открывает кабинет. Он не устанавливает зависимости или
модель. Не создавать новое окружение поверх рабочего OCR-окружения; сначала
сохранить его состав. Python 3.13/3.14 удовлетворяет проверке launcher, но
готовность конкретного набора зависимостей не следует из версии Python.

Данные по умолчанию сохраняются в .engineer-os/local-app. Не удалять их при
обновлении кода. Порт 8765; занятый порт требует остановить прежний экземпляр либо
передать --port. Для проверки, не затрагивающей историю пользователя, передавать
отдельный --data-dir. Один каталог данных допускает один экземпляр приложения.

Модель: ENGINEER_OS_LOCAL_PROVIDER=ollama, URL http://127.0.0.1:11434,
ENGINEER_OS_LOCAL_MODEL=qwen3:8b по умолчанию. Open WebUI выбирается отдельно
через provider=openwebui, URL и серверный API key. Файлы .env не загружаются
автоматически; настройки передаются через окружение процесса.

## Отдельный optional OCR-режим

Минимальное окружение не содержит Docling и не обещает распознавание сканов.
Для OCR создать отдельную .venv-ocr, установить в неё requirements-local-app.txt
и совместимый Docling с RapidOCR/onnxruntime. Состав испытанного Linux/Python3.12 CPU окружения
закреплён в requirements-ocr-linux-cpu.lock; ограничения качества и совместимости
описаны в [отчёте живой проверки](live-document-runtime-2026-10-06.md).
Этот snapshot не является Windows lock и не подтверждает полноту OCR.
Не считать произвольный latest Docling воспроизводимым рабочим окружением.

Официальные инструкции: [установка Docling](https://github.com/docling-project/docling/blob/main/docs/getting_started/installation.md),
[локальные веса](https://docling-project.github.io/docling/usage/advanced_options/),
[CLI моделей](https://docling-project.github.io/docling/reference/cli/).
Веса скачиваются отдельно; приложение не выполняет installer/download command.

В процессе, запускаемом именно Python этого OCR-окружения, задать:

- ORT_DISABLE_TELEMETRY=1 — до любого импорта ONNX Runtime;
- HF_HUB_DISABLE_TELEMETRY=1; HF_HUB_OFFLINE=1 — после подготовки весов;
- ENGINEER_OS_DOCUMENT_INTELLIGENCE=true;
- ENGINEER_OS_DOCLING_ARTIFACTS_PATH — абсолютный каталог подготовленных моделей;
- ENGINEER_OS_ATTACHMENT_PARSER=docling — для автоматической обработки вложений.

Start_ENGINEER_OS.cmd по умолчанию выбирает .venv, а не .venv-ocr. OCR-режим
запускать явно Python из .venv-ocr через scripts/run_local_app.py. Сначала выставить ORT_DISABLE_TELEMETRY=1; затем
проверить import docling/onnxruntime, состав весов и конвертацию representative
PDF. Это не подтверждает правильность OCR/таблиц: результат ещё сверяется с
источником. Результаты живой проверки относятся к пункту 2;
[правила отключения телеметрии](docling-privacy.md).

## Среда разработки и CI

Node.js нужен только для тестов интерфейса. e2e/package-lock.json закрепляет
jsdom и транзитивные зависимости. Пользователю Python-кабинета Node не нужен.

```bash
python -m unittest discover -s tests -p 'test_*.py'
python -m compileall -q engineering runtime e2e scripts
node --test tests/dashboard_counts.test.cjs
npm ci --prefix e2e --ignore-scripts --no-audit --no-fund
PYTHON=/absolute/path/to/.venv/bin/python npm test --prefix e2e
```

Перед полной Python-suite установить requirements-dev.txt: он добавляет Pillow
для pixel assertions в тестах preview. Pillow не требуется самому кабинету.

CI использует Python 3.12 и Node 22, requirements-dev.txt и npm ci. Push
main/fix/**/feat/** и pull_request на любую base branch запускают проверки.
DOM тесты используют actual local HTTP, synthetic model/Google transport;
это не проверка живого qwen3/OAuth, browser layout/CSP или Windows.
