# Пункт 6 — матрица завершения программных гейтов

Дата: 06.10.2026. Эта матрица отделяет **готовность программного маршрута**
от фактической инженерной верификации конкретного объекта.

## Нормативная ветка

Программно предусмотрены:

1. source-bound нормативная цепочка: документ → редакция → область → пункт →
   требование → фактическое состояние → сопоставление → вывод;
2. SHA256 исходного нормативного файла;
3. identity-bound authority source verification;
4. отдельный applicability review;
5. привязка величин к точной цитате и ограниченная Decimal/SI арифметика;
6. проверка engineering data class каждого source candidate;
7. fresh revalidation после изменения original/review;
8. итоговый `point6_readiness`.

Когда все программные prerequisite-гейты проходят, пакет получает
`READY_FOR_ENGINEERING_DECISION`. Это **не PASS/ACCEPTED**:
экспертное решение и FINAL AUDIT выполняются отдельно.

## Расчётная ветка

Программно предусмотрены:

1. 9 обязательных ролей расчётного комплекта;
2. semantic review каждой роли;
3. documented LIRA/SCAD adapter boundary без угадывания proprietary binary;
4. ENGINEER OS exchange manifest;
5. controlled external solver bridge, shell=false;
6. SHA256 executable и fingerprint команды;
7. input/output/log SHA256 receipt;
8. verification output/log против receipt;
9. completeness / consistency / log review;
10. critical findings gate;
11. correlation:
    - GEOMETRY;
    - MATERIALS_SECTIONS;
    - LOADS_COMBINATIONS;
    - SUPPORTS_RELEASES;
    с источниками фактической конструкции;
12. engineering data-class review;
13. единый `point6_readiness`.

Полный программный маршрут заканчивается
`READY_FOR_ENGINEERING_DECISION`, но всё равно сохраняет:
`status=BLOCK`, `acceptance_granted=false`,
`engineering_verified=false`, `FINAL AUDIT NOT_RUN`.

## Что больше нельзя честно закрыть только кодом в текущей среде

Для фактического завершения пункта 6 на реальном кейсе нужны входные подтверждения:

- официальный нормативный исходник нужной редакции с проверяемым SHA/источником;
- реальная проверка применимости пункта нормы к объекту;
- реальный LIRA/SCAD documented text/API export пользовательской модели;
- подтверждённые executable/аргументы конкретной установленной версии solver;
- реальный solver run;
- реальные output/log артефакты;
- фактические данные объекта для correlation с моделью;
- инженерное решение после всех prerequisite-гейтов.

Эти пункты являются **данными/исполнением**, а не отсутствующими software gates.

## Граница с дальнейшим планом

Пункт 6 не должен выдавать FINAL AUDIT или ACCEPTED.
После реального ENGINEERING DECISION результат используется в пункте 7
(полный реальный инженерный кейс), затем пункте 8 (FINAL AUDIT/acceptance).
Финальная Windows-проверка локального приложения остаётся пунктом 9.
