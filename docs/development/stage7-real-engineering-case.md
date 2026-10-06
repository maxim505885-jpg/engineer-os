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
