# Локальный Docling: отключение телеметрии

При живой проверке пункта 2 ONNX Runtime 1.30.0 попытался отправить
телеметрию Microsoft. Автоматическая проверка безопасности отклонила продолжение;
первый OCR запуск не считается завершённым.

Официальная документация сообщает, что в native builds телеметрия включена
по умолчанию. На Linux/macOS полный process-lifetime opt-out —
`ORT_DISABLE_TELEMETRY=1` **до первого импорта ONNX Runtime**. Вызов
`disable_telemetry_events()` после импорта сам по себе не предотвращает
инициализационное событие. На Windows этот API также отключает platform events;
Windows здесь не проверялся.

[Документация Microsoft](https://github.com/microsoft/onnxruntime/blob/main/docs/Privacy.md)
и [Python API](https://onnxruntime.ai/docs/api/python/api_summary.html).

Docling adapter выставляет process opt-out до optional imports и вызывает
API отключения platform events. Если ONNX Runtime уже загружен без этой
настройки, converter блокируется: нужен перезапуск процесса. Позднее изменение
окружения не отменяет ранее отправленные события. В embedding-процессе вызывающий
код должен выставить переменную до любых сторонних импортов ONNX Runtime.

Linux/macOS:

```bash
ORT_DISABLE_TELEMETRY=1 HF_HUB_DISABLE_TELEMETRY=1 HF_HUB_OFFLINE=1 \
ENGINEER_OS_DOCUMENT_INTELLIGENCE=true \
ENGINEER_OS_DOCLING_ARTIFACTS_PATH=/absolute/path/to/models \
.venv-ocr/bin/python scripts/run_local_app.py --no-browser
```

Веса должны быть заранее подготовлены. `HF_HUB_OFFLINE` запрещает загрузки
Hugging Face, но не является общим запретом сетевых соединений. Эти настройки
не заменяют сетевую изоляцию и не отключают автоматически телеметрию каждой
будущей зависимости.

Проверка системных вызовов через strace в текущей среде недоступна: ptrace
запрещён. Поэтому сетевой аудит всего процесса не объявляется выполненным.
Защитные unit tests проверяют порядок opt-out/import и блокировку небезопасного
порядка и не являются доказательством качества OCR.
