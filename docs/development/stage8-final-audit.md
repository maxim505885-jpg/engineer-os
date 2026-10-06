# Этап 8 — FINAL AUDIT / acceptance

Дата: 07.10.2026.

## Цель

FINAL AUDIT — последний fail-closed барьер ENGINEER OS. Он не повторяет
профильные проверки и не "улучшает" их статус. Он проверяет, что текущий
Stage-7 snapshot актуален, все обязательные стадии готовы, acceptance basis
полон и нет открытых BLOCK/ERROR/UNCERTAINTY, после чего выдаёт только одно из
двух решений: `ACCEPTED` или `BLOCK`.

## Реализовано

- append-only таблица `final_audits`;
- FINAL AUDIT всегда привязан к текущему Stage-7 case ID/SHA;
- восемь обязательных измерений:
  CASE_FRESHNESS, SOURCE_IDENTITY, TZ_TRACEABILITY, EVIDENCE_REVIEW,
  SPECIALIST_COVERAGE, DOMAIN_PREREQUISITES, CASE_QC, ACCEPTANCE_BASIS;
- автоматическое решение без ручной кнопки "принять";
- acceptance certificate создаётся только при чистом ACCEPTED;
- изменение Stage-7 case после аудита делает старый audit stale и эффективное
  решение становится BLOCK;
- GET/POST `/api/sessions/{sid}/final-audit`;
- локальный UI пункта 8;
- acceptance gate возвращает true только для свежего текущего ACCEPTED audit;
- Stage-7 clean case получает `READY_FOR_FINAL_AUDIT`, но ещё не ACCEPTED.

## Реальный объект

FINAL AUDIT выполнен над сохранённым Stage-7 snapshot «Набережная 28А».

Результат:
- `final_audit=COMPLETED`;
- `decision=BLOCK`;
- `acceptance_granted=false`;
- audit SHA256:
  `4e032ee1ca9716fc4511e5dedb1efa3f9ec18c8b6493d8a02bf8fae94aabc298`.

Сохранённые blocker codes:
- ACTUAL_STRUCTURE_CORRELATION_PENDING;
- POINT6_NORMATIVE_DECISION_PENDING;
- POINT6_SOLVER_DECISION_PENDING;
- V4_DOCUMENT_COMPLETENESS_BLOCK;
- CASE_ENGINEERING_STATUS_NOT_READY.

Это корректный FINAL AUDIT: он выполнен до конца, но не скрывает незакрытые
инженерные prerequisites.

## Критерий закрытия этапа 8

Этап 8 считается технически завершённым, когда:
1. существует неизменяемая история FINAL AUDIT;
2. audit привязан к точному case identity;
3. stale audit не может дать acceptance;
4. все обязательные измерения проверяются;
5. BLOCK любого upstream gate сохраняется;
6. чистый synthetic contract имеет единственный путь к ACCEPTED;
7. реальный объект проходит FINAL AUDIT и получает фактическое решение;
8. API/UI/unit/HTTP/DOM regression проходят.

Положительный ACCEPTED реального объекта не является критерием готовности
механизма Stage 8; он зависит от фактического закрытия upstream инженерных
гейтов пункта 6/V4.
