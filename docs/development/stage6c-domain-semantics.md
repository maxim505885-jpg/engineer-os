# Пункт 6В — semantic calculation review + normative authority contract

Дата: 06.10.2026. Основание: stage6B / PR59. Этот этап продолжает пункт 6 и не закрывает его.

## Что добавлено

1. `engineering/normative/authority.py`
   - типизированный authority/applicability review;
   - document/edition/clause/authority/source_ref/applicability_basis/decision;
   - VERIFIED даёт только `READY_FOR_EXPERT_APPLICABILITY_REVIEW`;
   - receipt не является самоподтверждающимся доказательством и не даёт acceptance.

2. `engineering/calculation/semantic_review.py`
   - semantic review отдельно по каждой из 9 ролей расчётного комплекта;
   - source IDs, statement, basis и decision;
   - дубликаты/пропуски/REJECTED/NOT_VERIFIED блокируют маршрут;
   - полный комплект даёт только `READY_FOR_SOLVER_VERIFICATION`;
   - solver execution и связь с фактической конструкцией остаются открыты.

3. `engineering/local_app/domain_packets.py`
   - существующие NORMATIVE/CALCULATION packets обратно совместимы;
   - NORMATIVE может содержать `authority_review`, который обязан совпадать с identity chain;
   - CALCULATION может содержать `semantic_reviews`, источник каждой semantic роли обязан принадлежать той же binding-role;
   - fresh report повторно проверяет semantic/authority records;
   - общий status остаётся BLOCK, acceptance=false, FINAL AUDIT NOT_RUN.

4. Тесты
   - authority identity mismatch отклоняется;
   - verified authority receipt не снимает applicability BLOCK;
   - все 9 semantic reviews не снимают solver BLOCK;
   - semantic review не может заимствовать source candidate другой роли.

## Что это НЕ делает

- не декодирует бинарную семантику LIR/SCAD;
- не запускает solver;
- не проверяет подлинность authority source во внешнем реестре;
- не доказывает применимость конкретной редакции СП/ГОСТ;
- не подтверждает фактическую конструкцию;
- не выдаёт PASS/ACCEPTED.

## Следующий шаг пункта 6

Нужен воспроизводимый solver/input route:
- документированный текстовый/обменный экспорт модели конкретной версии ЛИРА/SCAD;
- parser геометрии, материалов/сечений, нагрузок/сочетаний, опор;
- solver receipt с identity версии/модели/input hash/output hash;
- source-bound результаты и сопоставление с фактической конструкцией;
- независимая проверка нормативной authority/applicability цепочки.

Windows остаётся пунктом 9.
