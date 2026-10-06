# Этап 7 — полный реальный инженерный кейс

Дата: 07.10.2026.

## Цель

Пункт 7 проверяет ENGINEER OS не отдельными модулями, а одним воспроизводимым
кейсом: ТЗ → оригиналы → извлечение → evidence/source review → требования →
предметные пакеты → профильные роли → QC → case snapshot.

Этап 7 **не выполняет FINAL AUDIT** и не может выдавать ACCEPTED. Если реальные
нормативные или solver prerequisites пункта 6 ещё не подтверждены, кейс должен
сохранить их как BLOCK, а не обходить.

## 7A — case-level orchestration

Реализовано:

- append-only `real_case_snapshots` в локальной SQLite;
- снимок привязан к конкретному `CORE_RUN`;
- фиксируются SHA256/size всех оригиналов;
- фиксируется явный manifest ролей исходников: TOR, REPORT, CALCULATION_REPORT, MODEL, GEODESY, GRAPHICS, PHOTO, OTHER;
- фиксируются digest текущего ТЗ, evidence/review, domain packets и CORE result;
- стадии:
  - source_identity;
  - requirements;
  - evidence;
  - specialists;
  - domain_prerequisites;
  - qc;
- итог `point7_readiness`;
- revalidation старого снимка после изменения исходников/ТЗ/evidence/domain/core;
- старые снимки остаются историей и не становятся текущими автоматически;
- API `GET/POST /api/sessions/{sid}/real-case`;
- локальный UI для выбора завершённого CORE_RUN и фиксации snapshot;
- fail-closed:
  `engineering_status=BLOCK`,
  `acceptance_granted=false`,
  `FINAL AUDIT NOT_RUN`.

## 7B — реальный объект

Следующий проход должен использовать фактический комплект объекта
«БЦ, ул. Набережная, 28А» и зафиксировать один case snapshot с реальными
идентичностями исходников и фактическими результатами текущих проверок.

Ожидаемые реальные ограничения сейчас:

- историческая полнота V4 PDF остаётся BLOCK (523 UNCERTAINTY / 11 BLOCK);
- реальный normative engineering decision из пункта 6 отложен;
- реальный LIRA/SCAD solver execution из пункта 6 отложен;
- поэтому 7B может и должен завершиться воспроизводимым case snapshot,
  но не ACCEPTED.

## Граница завершения пункта 7

Пункт 7 можно считать технически выполненным, когда:

1. полный реальный комплект объекта проходит через один case-level workflow;
2. snapshot воспроизводим после рестарта;
3. все открытые зависимости отражены детерминированными BLOCK reasons;
4. изменение любого ключевого входа делает snapshot stale;
5. QC не теряет BLOCK профильных ролей;
6. нет FINAL AUDIT/ACCEPTED до пункта 8.


## 7C — фактическое закрытие Stage 7

07.10.2026 выполнен offline real-case run на полном фактическом комплекте объекта.

Результат:
- required source roles: все присутствуют;
- 10/10 source entries: identity/format PASS;
- два независимых запуска дали один и тот же case SHA256:
  `eb6f21893534b84ed2c5088347c530e3289b07b34c8ba0460d222d9b87e37060`;
- stale test: намеренная подмена ожидаемого SHA256 одного LIR перевела
  source identity в BLOCK, изменила case SHA и дала
  `BLOCKED_BY_SOURCE_INTEGRITY`;
- сохранён реальный QA snapshot:
  `docs/qa/2026-10-07-stage7-naberezhnaya-real-case.json`;
- воспроизводимый runner:
  `scripts/stage7_real_case_offline.py`.

Stage 7 считается **технически завершённым**:
`stage7_completion=COMPLETE_WITH_OPEN_ENGINEERING_BLOCKS`.

Это не означает инженерное ACCEPTED. Реальный кейс остаётся:
- `engineering_status=BLOCK`;
- `acceptance_granted=false`;
- `FINAL AUDIT NOT_RUN`.

Открытые причины относятся к отложенному пункту 6 и V4 completeness:
- V4_DOCUMENT_COMPLETENESS_BLOCK;
- POINT6_NORMATIVE_DECISION_PENDING;
- POINT6_SOLVER_DECISION_PENDING;
- ACTUAL_STRUCTURE_CORRELATION_PENDING.

Следующий этап по карте — пункт 8 FINAL AUDIT, но его нельзя считать
успешным до возврата и фактического закрытия указанных инженерных BLOCK.
