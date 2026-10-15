# Пункт 6Д — documented LIRA/SCAD adapter boundary + controlled solver bridge

Дата: 06.10.2026. Основание: stage6D / PR62. Пункт 6 остаётся открытым.

## Подтверждённые внешние возможности

- LIRA-FEM умеет создавать текстовый файл задачи на входном языке процессора.
- LIRA-FEM API официально предоставляет COM/ActiveX-доступ к документу и таблицам ввода.
- SCAD официально экспортирует исходные данные расчетной схемы в текстовый архив, включая геометрию, связи и нагрузки.

ENGINEER OS не придумывает vendor-specific command-line switches и не декодирует бинарный .lir/.spr предположениями.

## Реализовано

### 1. Documented vendor adapter boundary

Добавлен `engineering/calculation/vendor_adapters.py`.

Поддерживаемые source kinds:
- `LIRA_FEM_API`
- `LIRA_PROCESSOR_TEXT`
- `SCAD_TEXT_ARCHIVE`

Snapshot обязан иметь source version, source SHA256 и явные sections. Для перехода в ENGINEER OS exchange нужны:
- GEOMETRY
- MATERIALS_SECTIONS
- LOADS_COMBINATIONS
- SUPPORTS_RELEASES
- UNITS

Неизвестные секции не интерпретируются как инженерные данные. Неполный/пустой источник -> BLOCK.
Полный источник -> только `READY_FOR_EXCHANGE_NORMALIZATION`.

### 2. Controlled external solver bridge

Добавлен `engineering/calculation/solver_bridge.py`.

Bridge:
- требует абсолютный существующий executable;
- запускает только `shell=False`;
- принимает bounded args;
- input/output/log должны находиться внутри выделенного cwd;
- не передаёт произвольное окружение/ключи в solver;
- фиксирует SHA256 input/output/log;
- ограничивает timeout;
- если ожидаемый output отсутствует, завершает маршрут fail-closed и receipt не создаётся.

Vendor command line намеренно не зашит: параметры конкретной установленной версии должны быть подтверждены отдельно.

### 3. Regression

Проверяется:
- нормализация документированного source snapshot в exchange manifest;
- отсутствие обязательного раздела -> BLOCK;
- неизвестная "угаданная" binary section -> BLOCK;
- реальный subprocess test через controlled test executable;
- hash identity input/output/log;
- запрет output вне рабочей директории;
- zero-exit без ожидаемого output -> fail-closed;
- receipt остаётся только `READY_FOR_RESULT_VERIFICATION`, acceptance=false.

## Не завершено

- Windows COM bridge к установленной LIRA-FEM;
- чтение реального пользовательского LIRA text export;
- чтение реального SCAD text archive;
- подтверждённые CLI/API команды запуска solver конкретной версии;
- LIRA-FEM RES API / SCAD result adapter;
- сравнение результатов с исходными данными и фактической конструкцией;
- FINAL AUDIT / ACCEPTED.

## Следующий шаг

На Windows пункт 9 пока не запускается как финальная приемка, но для пункта 6 потребуется
узкая инструментальная проверка установленного LIRA/SCAD интерфейса: получить один
официальный text/API export реальной модели и определить подтверждённый solver/result API.
После этого adapter должен быть дополнен fixture из реального export и result parser.
