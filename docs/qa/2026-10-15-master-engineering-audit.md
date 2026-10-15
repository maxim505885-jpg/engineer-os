# MASTER audit / implementation pass — 15.10.2026

Это отчёт о разработке, не FINAL_AUDIT объекта. Инженерный ACCEPTED и выпуск v1.0
не заявлены. Программный PASS всегда ограничен описанным сценарием.

## Идентичность и источники

- Первоначальная папка: `architecture/openwebui-integration`, HEAD `98b9c4c`,
  большой staged/untracked набор. Не изменён и не включён в пакет.
- Через GitHub Git refs API подтверждён официальный кандидат
  `integration/release-candidate-v1` = `db29e4c946e4db5e088e8fdd727c6165365dcc4d`.
  Изолированный managed worktree создан именно от него; рабочая ветка
  `codex/master-engineering-audit-20261015`.
- GitHub CI базы: Core #1022 / Windows #222 / Security #845 — success.
  Это проверки базы, а не нового пакета.
- PR148 открыт, head `f53a6f45e6d46486e8d2103af610565591fef494`; изменения launcher
  не объединялись автоматически. PR149/151 — открытые обновления документации;
  их более новые результаты отличаются от handoff в официальном candidate.
  PR145 также открыт. Ранние ориентиры не приняты за текущую ветку.
- Прямые Git fetch/ls-remote завершились permission/network ошибками; `gh` нет.
  Чтение GitHub выполнено connector-ом, а не выдано за успешный fetch.

## Документы: факты и границы

Воспроизведён ERROR реализации: Docling возвращал `limitations`, а
`local_app.extraction.execute` терял их. На текстовой странице с caption без
проверенных строк журнал сохранял UNCERTAINTY вместо BLOCK. Регрессионный тест
упал до исправления и прошёл после: текст сохранён, limitation и BLOCK записаны
в SQLite, оригинал byte-identical, acceptance=false.

Предупреждение Docling об отброшенных ячейках теперь собирается в самом адаптере,
включая внутренние pipeline threads. Конвертации адаптера сериализованы, чтобы
не смешивать предупреждения параллельных вызовов. Сохраняется фиксированный код,
а не текст/содержимое диагностического сообщения. Исходный SHA проверяется до/после
конвертации. Независимое review выявило первоначальную ошибку thread filter;
она воспроизведена отдельным тестом и исправлена.

Свежая read-only проверка доступного старого `v4-extraction-review.json` показала
534 страницы в scope, 397 страниц с блоками, 29 231 блок, 137 blocked chunks,
status BLOCK. Это старый набор, не новый v12 rerun. В документации PR151/handoff
другой копии зафиксирован более поздний v12: 534/534, 31 268 blocks,
52 BLOCK / 55 UNCERTAINTY, 31 table-loss warning, 74.8% weighted unique-token
recall; DOCX 553/553 units с 112 BLOCK. Эти новые числа в этом проходе не
пересчитывались из полного приватного корпуса. **441 UNCERTAINTY не подтверждено
как актуальный счётчик.** Наборы не складываются и не подменяют друг друга.
Полнота №13 остаётся BLOCK. OCR/визуальный эталон полного комплекта не выполнен.

Свежий ограниченный реальный прогон выполнен на проблемной странице57 V4 новым
кодом, используя уже установленный Docling2.130.0 / ONNX Runtime1.30.0 и локальный
кеш моделей. Заданы HF_HUB_OFFLINE=1 и telemetry opt-out; новые модели не
устанавливались. Exit0 означает сохранение reviewable partial output:23 блока,
status BLOCK, `TABLE_CAPTION_WITHOUT_VERIFIED_ROWS`, acceptance=false. Исходный
SHA до/после совпал. Это подтверждённое сохранение частичного текста с реальным
BLOCK, не полнота страницы. Приватные JSON/stdout/stderr и summary сохранены в
ignored `.engineer-os/master-pass/`; содержание/идентичность оригинала не добавлены
в этот публичный отчёт.

## Реестр 19 пунктов

В колонке проверок указан существующий исполнимый контракт, включённый в полный
локальный прогон, либо отдельный явный запуск. Общая регрессия не полностью зелёная;
цифра прежних DONE не переносится как новая инженерная приёмка.

| № | Код / было | Сделано и проверки этого прохода | Статус в заявленном объёме | Осталось / критерий и следующий шаг |
|---|---|---|---|---|
| 1 | Candidate + старый грязный checkout | Git refs/PR/CI сверены, отдельная ветка от db29e4c | PASS: идентичность базы | Довести PR→проверенный candidate; main/release отдельно |
| 2 | `local_app/ocr.py`, model gateway | Сохранены Ollama/OCR; `test_local_ocr`, `test_model_gateway` в regression | PARTIAL: качество реальных данных | Эталонный source-bound OCR; живой specialist inference, без загрузки новых моделей |
| 3 | extraction/automatic_analysis/store checkpoints | `test_document_analysis_resume`, receipt recovery и большие Office в regression | PASS: программный resume scope | Реальная completeness не следует из resume; сверять receipts при каждом большом run |
| 4 | native PDF, Office, images + provenance | Native/Office regression и Chromium загрузка/перечитывание PASS | PASS: имеющиеся форматы | Не расширять обещание на любую графику/формулу; qualified corpus отдельно |
| 5 | requirements/source_binding/evidence | ТЗ/глобальные gates в regression; Evidence UI в Chromium PASS | PASS: программная трассировка | Полное реальное ТЗ/evidence для принятого объекта |
| 6 | normative + vendor calculation adapters | Новый optional Pynite benchmark; нормативные tests в regression | PARTIAL | Только одна линейная UDL балка квалифицирована; рамы/фермы/section-properties, vendor API и реальные norms открыты |
| 7 | real_case/stage7 offline | Негативные case tests в regression; прежний реальный объект BLOCK | PASS: отрицательный workflow | Не выдавать replay за новый реальный accepted run |
| 8 | core acceptance / FINAL AUDIT gates | `test_acceptance_trust_boundary`, `test_final_audit` в regression | PASS: программная граница | Положительный квалифицированный объект отдельно №14 |
| 9 | Windows supervisor / launcher | PowerShell parse PASS; реальный локальный server/restart в браузерных тестах PASS; отдельный restart test PASS | PARTIAL | PR148 не merged; clean install, reboot, transfer и one-click user acceptance не выполнены |
| 10 | Candidate и открытые потоки | Состояние PR148/149/151 и несовпадение handoff зафиксированы | PARTIAL | Проверить и консолидировать PR, не переписывая чужие изменения |
| 11 | Существующий local_app UI | 7/7 настоящих Chromium маршрутов PASS; 10 Node tests PASS | PASS: проверенные маршруты | Приёмка UI на реальном инженерном объекте; IFC/FEM пока CLI, без нового интерфейса |
| 12 | backup/restore/lock/security | Backup/restore/no-replace в Chromium PASS; regression без assertion failures | PARTIAL | 6 symlink tests не исполняются без Windows privilege; transient app.lock teardown error отдельно повторён PASS; release security review открыто |
| 13 | Docling/native/Office completeness | Исправлены потеря limitations, worker-thread loss diagnostics, source change; red→green тесты | BLOCK | Визуальное/табличное/формульное соответствие реальных оригиналов, новые source-bound outputs после изменения parser identity |
| 14 | Реальный положительный ACCEPTED отсутствует | Ни один BLOCK не снят; синтетические тесты не повышают статус | BLOCK | Достаточные ТЗ/измерения/evidence/применимые нормы/расчёты; затем qualified FINAL_AUDIT |
| 15 | `local_app/knowledge.py`, confirmed knowledge | Memory gate/изоляция/обязательная перепроверка в regression + Chromium PASS | PARTIAL | Реальный ACCEPTED→knowledge→revoke/update сценарий |
| 16 | conclusion drafts/illustrations/templates | Chromium DOCX/PDF download, история/иллюстрации PASS; regression генератора | PARTIAL | Это черновики; полноценный accepted report с повторным чтением и визуальной сверкой реального документа |
| 17 | ezdxf inventory/controlled annotations, DWG BLOCK | Новый read-only DXF comparison; 21 CAD tests PASS, существующий Chromium CAD PASS | PARTIAL | Исходный DWG→DXF losses, converter logs по типам, DWG roundtrip не квалифицированы; FreeCAD не установлен |
| 18 | Ollama/Open WebUI AI Gateway | Не менялся; model/gateway regression и synthetic browser workflow | PARTIAL | Живой provider receipt/specialist run; synthetic model не заменяет локальный inference |
| 19 | Выпуск v1.0 отсутствует | Release BLOCK сохранён, CI optional adapters подготовлен | BLOCK | Закрыть инженерные и physical Windows критерии, exact-head CI, release checklist, затем main/tag |

## Новые optional маршруты

- `engineering/cad/roundtrip.py`: exact serialized DXF comparison с missing/added/
  changed handles и группировкой по типу, units/layers/resources/audit guards.
  PASS ограничен DXF_SERIALIZED_DATA_ONLY; DWG equivalence=false.
- `engineering/bim/ifc_adapter.py`: lazy IfcOpenShell; IFC STEP identity, project/
  building/storey structure, beams/columns/walls/slabs, declared quantities,
  properties/materials, explicit length units, storey relationships и GUID locators;
  diff по целевым GUID. Данные PROJECT, не MEASURED. Нет geometry qualification,
  clash/IDS/formal requirements, actual evidence registration или solver model.
  Неизвестные/противоречивые единицы, duplicate GUID, повреждение/лимиты → BLOCK.
- `engineering/calculation/control_beam.py`: Pynite линейная шарнирная балка с
  постоянными E/Iz и равномерной вертикальной нагрузкой, явные N/m/Pa и source/
  evidence references. Реакции, поперечная сила, момент и прогиб сверяются с
  независимыми формулами и равновесием. Для L=6 m, q=1000 N/m, E=210 GPa,
  Iz=8e-6 m4: реакции 3000 N, |Mmid|=4500 Nm, |v|=0.010044642857 m.
  Это CALCULATED benchmark, не проверка несущей способности реальной конструкции.
- `scripts/engineering_tools.py`: CLI этих трёх адаптеров, JSON stdout,
  exit2 для BLOCK. Исходники не перезаписываются.

## Инструменты, лицензии и воспроизводимость

Испытаны в отдельной `.venv-engineering`: IfcOpenShell 0.8.5 (LGPL), PyniteFEA 3.2.0
(MIT), ezdxf 1.4.4 (MIT). Применён существующий PyMuPDF pin 1.26.6 (AGPL/commercial
dual license) и olefile 0.47 из requirements проекта. Базовый runtime не расширен
обязательными IFC/FEM зависимостями; новых платных API нет. Публичная дистрибуция
должна сохранять лицензии upstream; лицензия самого проекта этим не меняется.

Docling, pdfplumber, img2table, PaddleOCR в системном Python не обнаружены;
это не утверждение об их отсутствии во всех отдельных окружениях пользователя.
Тяжёлые OCR модели не скачивались. img2table/PaddleOCR не включались без A/B
квалификации. FreeCAD/LibreDWG/section-properties/IfcTester/IfcClash/IfcDiff не
включены в этот пакет: требуются отдельные эталоны, реальные converter logs и
подтверждение пользы. Jan/LocalAI/llama.cpp, cloud/FEM/BIM servers не добавлялись.

Официальные источники, проверенные 15.10.2026:

- [IfcOpenShell units](https://docs.ifcopenshell.org/autoapi/ifcopenshell/util/unit/index.html).
- [Pynite quickstart](https://pynite.readthedocs.io/en/latest/quickstart.html).
- [ezdxf content API](https://ezdxf.readthedocs.io/en/stable/tasks/get_entity_content.html).
- [ЛИРА-САПР 2024 R2](https://lira.land/lira/release-notes/2024/2024-r2),
  [COM API](https://lira.land/lira/release-notes/api-and-input-tables).
  Наличие актуального COM API не подтверждает ABI/совместимость установленной
  версии 2024. Существующие native/API adapters не заменены.
- [SCAD text archive](https://scadsoft.com/help/SCAD/ru/SCAD1049/archives-export_import.htm),
  [официальный API](https://scadsoft.com/download/SCADAPI.pdf).
  Документация экспорта не доказывает выполнение solver на этом ПК.

## Проверки и ограничения

- Red→green: runtime Docling limitation; layout-loss warning; source mutation;
  pipeline-worker warning; IFC invalid unit semantics. Независимое review:
  две actionable ошибки исправлены и перепроверены, других замечаний к fixes нет.
- 50 Docling/extraction/evidence/privacy tests PASS до дополнительного review;
  после review 24 Docling/runtime/IFC tests PASS. CAD 21 PASS. Optional IFC/FEM/CLI
  11 PASS. Пересекающиеся запуски не складываются в новый общий счётчик.
- Итоговый focused run после всех code/review fixes:60 tests PASS (Docling,
  runtime, IFC, Pynite, CLI, CAD, tooling HTTP, Windows PDF preflight), diff-check
  PASS. Дополнительно NaN в идентичном DXF отклоняется отдельным red→green тестом.
- Полный global Python run: 1071, 4 failures, 11 errors, 56 skips — не PASS.
  Причины основных failures: незакреплённый PyMuPDF1.28.2 печатал import warning
  в JSON worker stdout; olefile отсутствовал. Глобальное окружение не изменялось.
- Полный pinned run: 1085, 0 assertion failures, 7 errors, 47 skips. 6 errors —
  WinError1314 symlink privilege; 1 — app.lock WinError32 при cleanup после kill.
  Тот же restart test отдельно PASS; общий suite всё равно не объявляется PASS.
  Эти totals относятся к запуску до двух дополнительных review regressions.
- 7/7 real Chromium workflow PASS, synthetic model=true, engineering acceptance=false;
  formula_rendered=false и genuine OCR=false сохранены как ограничения.
- jsdom PDF DOM PASS; local app DOM PASS. Drive DOM сначала timeout при общем
  запуске, затем отдельно PASS; нестабильность не скрыта. 10 Node tests PASS после
  исправления CRLF-sensitive cleanup regex в тесте.
- PowerShell supervisor syntax и architecture_guard PASS. Физическая перезагрузка,
  чистая установка, перенос на другой ПК и финальный релиз не выполнялись.

Следующий приоритет: реальный источник-связанный completeness rerun после смены
Docling implementation identity; визуальная сверка проблемных ячеек/формул/OCR.
Параллельные product расширения не снимают этот BLOCK. Не использовать старые
cached receipts как результаты нового parser. Матрица норм ждёт законных
актуальных редакций и проверенных исходных параметров; новые нормативные пункты
не придумывались. Дальше — настоящий DWG conversion loss ledger и IFC formal
requirements; только затем расширение расчёта на рамы/фермы.
