# Пункт 6Г — воспроизводимый solver/input route

Дата: 06.10.2026. Основание: stage6C / PR61. Пункт 6 остаётся открытым.

## Реализовано

### 1. ENGINEER OS calculation exchange manifest

Добавлен `engineering/calculation/exchange_manifest.py`.

Это собственный детерминированный обменный формат ENGINEER OS, а не декодер
проприетарного LIR/SCAD binary. Он принимает только UTF-8 JSON с:

- format = ENGINEER_OS_CALC_EXCHANGE;
- version = 1;
- source_sha256;
- sections: GEOMETRY, MATERIALS_SECTIONS, LOADS_COMBINATIONS,
  SUPPORTS_RELEASES, UNITS;
- SHA256 для каждой секции;
- bounded records.

Пропущенные или пустые разделы дают BLOCK. Полный manifest даёт только
`READY_FOR_SEMANTIC_CROSSCHECK`, потому что native solver input и фактическая
конструкция ещё не доказаны.

### 2. Solver receipt

Добавлен `engineering/calculation/solver_receipt.py`.

Receipt хранит:

- solver_name;
- solver_version;
- input_sha256;
- output_sha256;
- log_sha256;
- exit_code;
- started_at / finished_at.

Non-zero exit даёт BLOCK. Exit 0 даёт только `READY_FOR_RESULT_VERIFICATION`.
Это не подтверждает качество solver, семантику input, смысл output или
соответствие реальной конструкции.

### 3. Domain packets

CALCULATION packet опционально принимает `exchange_manifest` и
`solver_receipt`. Fresh report перепроверяет их. При наличии корректного
receipt причина становится `SOLVER_EXECUTION_NOT_ACCEPTED`, а не
`SOLVER_NOT_RUN`. Общий engineering status остаётся BLOCK, acceptance=false,
FINAL AUDIT NOT_RUN.

### 4. Regression

Добавлены проверки:

- complete exchange manifest -> только semantic crosscheck;
- missing/empty/duplicate/unknown sections -> BLOCK/reject;
- non-zero solver exit -> BLOCK;
- zero exit -> только result verification;
- domain packet с полным semantic review + exchange + zero-exit receipt всё
  равно остаётся BLOCK.

## Что не сделано

- native .lir/.scad binary decoder;
- автоматический экспорт из конкретной версии ЛИРА/SCAD;
- реальный solver runner;
- semantic parser конкретного текстового процессорного формата ЛИРА;
- проверка solver outputs/results/logs;
- сопоставление расчётной модели с фактической конструкцией;
- инженерное ACCEPTED.

## Следующий подэтап пункта 6

Нужен adapter конкретного экспортного формата ЛИРА/SCAD и реальный solver
execution bridge с неизменяемой identity: executable/version, input hash,
command/config fingerprint, output/log hash. После этого — result verification
и actual-structure correlation. Windows остаётся пунктом 9.
