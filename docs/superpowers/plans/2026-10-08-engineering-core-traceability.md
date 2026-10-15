# №7 — воспроизводимая сверка требований и ролей

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans. Native one-pass execution is explicitly requested by the user; no intermediate approval handoffs.

**Goal:** Сохранять предметную связку требование→наблюдение роли→проверяемый источник→расхождение/остаток, без повышения черновика до инженерного принятия.

**Architecture:** Отдельная детерминированная сверка поверх существующих requirements/source gates и CORE_RUN. Не менять acceptance gate и не пытаться заменить реальные нормы/solver. Обратная совместимость старого четырёхполевого ответа; новые наблюдения могут явно указывать requirement_ids и relation. Неуказанные/непокрытые требования и неподтверждённые источники не становятся закрытыми.

**Tech Stack:** Existing Python/SQLite, plain JavaScript, native PDF/Office, optional local model; no paid service.

**Spec:** docs/development/master-plan.md №7; AGENTS.md; ENGINEER_OS_PROJECT_MAP.md §58.

## Global constraints
- acceptance=false, FINAL AUDIT NOT_RUN; реальные нормы №8, solver №9, Windows №16.
- Противоречия учитываются как заявленные, без семантического угадывания по тексту.
- Снимок результата фиксирует требования, source/review SHA и роли; актуальные данные не переписывают исторический вывод.

## Review focus
- Старый ответ без requirement IDs не скрывает непокрытое ТЗ.
- Неизвестный/чужой ID не привязывается к требованию.
- SOURCE_CONFIRMED не подтверждает тип P/F/M и инженерное заключение.
- BLOCK отдельной роли или непрочитанных частей не исчезает в итоговой сводке.
- Источник/ревизия ТЗ/проверка изменились во время работы — результат не сохраняется как завершённый.

## Tasks
1. [x] RED→GREEN: optional explicit requirement_ids/relation in parse_draft; controlled IDs in direct and automatic role calls, unchanged legacy contract.
2. [x] RED→GREEN: engineering_review.report(requirements, records) maps per-requirement role findings/source gates, missing mapping, declared conflict, source limitations; immutable digest and scope. CORE aggregate enforces deterministic BLOCK without replacing ERROR. Identity includes implementation.
3. [x] RED→GREEN: UI shows requirement mapping and reasons for completed role output; HTTP/DOM/Chromium verify no manufactured acceptance; case snapshot consumes saved review.
4. [x] Real-source ToR/report inspection, reproducible source-bound case and negative conflicts; whole suite and independent review; GitHub draft stacked on PR79; same map/plan update with honest criterion and open inputs.

## Actual outcome
556 Python,4 Node,DOM/Chromium PASS. QA: docs/qa/2026-10-08-engineering-core-traceability.md. One reviewer found2 Important; fixes passed RED→GREEN. Real-source negative case:12 BLOCK, native region AMBIGUOUS, ToR unverified. Software traceability implemented; entire №7 remains open pending substantive source/actual-structure checks.

Draft PR80 published; living map §59 and master plan preserve №7 open.
