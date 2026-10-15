# Stage 7B — реальный комплект объекта «БЦ, ул. Набережная, 28А»

Дата: 07.10.2026.

Этот inventory фиксирует фактически найденные оригиналы для case-level прогона.
Приватные Drive/Library ID намеренно не публикуются в репозитории.
Идентичность задаётся именем, размером и SHA256.

| Роль кейса | Файл | Размер, байт | SHA256 | Текущий статус |
|---|---|---:|---|---|
| TOR + REPORT | 15.09.2026 ТЗК БЦ ул. Набережная 28А V4 сшито с графикой.pdf | 74522583 | b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916 | Document completeness BLOCK: исторически 523 UNCERTAINTY / 11 BLOCK; acceptance=false |
| CALCULATION_REPORT | Расчет  .docx | 2754000 | 7b7fd508058e7cf91cf051d5a214bd9b1af09df9d361f32273d4942577bf61db | Office parsing/source binding available; engineering semantics not accepted |
| CALCULATION_REPORT | Расчет  .doc | 3029504 | ae8ba034b8970eefe8283577598da8529e1f94f9f0200c7309d3d6bc84357a76 | Derived conversion route required; original identity preserved |
| OTHER / CALCULATION_DATA | Таблицы.xlsx | 10004 | 305a8e47342c7d552095b936c382547b22fc0a933c4996f2422e8a8f7fe01c1f | Spreadsheet source available; semantic use in calculation not accepted |
| MODEL | 048 секция 1_А2_011123.lir | 42047193 | a753162adf1f1b2de8ab92ab1355eac4d0c23e9241bf6e0e97f39d3ee6205ca9 | Native binary semantic payload NOT_DECODED; solver NOT_RUN |
| MODEL | Секция 3 _S 011123.lir | 32397127 | fd300a06f23f455a00d120276c2daed3e6142de4abe9edb39d036c2a50f990ca | Native binary semantic payload NOT_DECODED; solver NOT_RUN |
| GEODESY | Геодезические измерения 03.09 пакетная печать(1).pdf | 7563047 | 6092ab2298bf328a545379a850b0a740cc40f3c5592703fbf876c32f459913ce | Real source available; full engineering interpretation not accepted |
| GRAPHICS | Графика 03.09.2026.pdf | 10793106 | fc2e720d13039b5fa9628b05125e8ce3bc6ba2c8756bfcb882243a67ec69d44c | Real graphics source available; full semantic cross-check not accepted |
| OTHER / MODEL_BINDING | привязки секций к модулю грунт.xlsx | 665732 | d04e2fc60d7110d3b1a13095c1e50c67c2bdd24fd7d4eac60cc2e1145510139e | Binding source available; units/coordinate semantics not accepted |

## Case manifest

Для Stage 7B исходники должны быть назначены минимум так:

- `TOR`: V4 PDF;
- `REPORT`: V4 PDF;
- `CALCULATION_REPORT`: DOCX (DOC сохраняется как дополнительный оригинал);
- `MODEL`: оба LIR;
- `GEODESY`: геодезический PDF;
- `GRAPHICS`: графический PDF;
- `OTHER`: XLSX таблиц и XLSX привязок.

## Ожидаемый результат первого реального прогона

Первый Stage 7B snapshot **не должен быть ACCEPTED**.

Ожидаемые блокировки:
- V4 document completeness остаётся открытой;
- normative engineering decision из пункта 6 отложен;
- LIRA/SCAD semantics и реальный solver receipt отложены;
- correlation модели с фактической конструкцией не завершена.

Цель первого прогона — доказать, что весь реальный комплект проходит через
единый case-level workflow, идентичность всех исходников сохраняется, открытые
гейты не теряются, а snapshot становится stale после изменения любого
контролирующего входа.
