# ENGINEER OS1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Завершить существующее Windows-приложение по12release gates и19критериям с проверенным положительным инженерным пользовательским циклом.

**Architecture:** Существующие local_app/SQLite/Worker/UI/Ollama сохраняются. Предметные библиотеки engineering/* подключаются тонкими source-bound адаптерами; второй runtime/очередь/агентный framework не создаются. Принятие выдаёт защищённый предметный review workflow, а не model output или наличие файла.

**Tech Stack:** Текущий Python3.12/3.13,SQLite,PyMuPDF,Docling isolated profile,существующий OCR,ezdxf,IfcOpenShell,Pynite,Ollama,существующийJS UI/Playwright. Версии фиксировать испытанным Windows profile;не устанавливать latest поверх рабочего окружения.

**Spec:** `docs/development/release-v1-definition-20261015.md`; audit `docs/qa/2026-10-15-full-readiness-audit.md`; AGENTS.md; пользовательский MASTER PROMPT.

## Global Constraints

- «локальная работа»; «Windows 11»; «никаких обязательных платных API»; «сохранение оригиналов».
- «Не удаляй BLOCK без устранения его причины и проверки результата».
- «Не загружай тяжёлые OCR-модели автоматически в основное окружение».
- «Не начинай разработку заново»; «Сохрани существующий Ollama и AI Gateway».
- «Не утверждай эквивалентность исходному DWG без фактической сверки».
- «Не смешивай BIM-геометрию с подтверждённой расчётной схемой».
- «Пока проверяем ЛИРА/SCAD отдельно от обязательного выпуска базового приложения» — V01 отдельный поток, не подмена готовности vendor extension.
- Исходный dirty checkout/пользовательский server8765 не менять во время разработки. Поставку/миграцию выполнить отдельно с backup и откатом.
- Процент готовности не выводить из количества tests/модулей. Каждый gate имеет PASS receipt или остаётся OPEN/BLOCK.

## Review Focus

1. Stale source/rule/review после приёмки: T05,T10,T11 должны аннулировать доверие во всех зависимых данных.
2. Crash/resume и дубли: T04,T12 сверяют попытки/receipt IDs/accepted output, а не только SUCCEEDED.
3. Ресурсы и активный контент Office/CAD/IFC: T02,T03,T08,T09 доказывают limits/owned cleanup и отсутствие активации OLE/macros.
4. Ошибки знака/единицы/merged cell при хорошем тексте: T04,T06,T07 имеют независимые числовые и source-cell эталоны.
5. Update/key loss/другая машина: T01,T11,T12 проверяют version identity, миграцию, отзыв доверия и rollback.

## Порядок и зависимости

|Пакет|Приоритет|Зависит от|Выход|
|---|---|---|---|
|T01 Одна сборка|P0|нет|version/build/profile identity, безопасный путь поставки|
|T02 Windows engineering profile|P0|T01|воспроизводимая подготовка OCR/Office/optional capabilities|
|T03 Office source view|P0|T02|source-bound layout/objects/formulas на Windows|
|T04 Полнота/ТЗ/resume|P0|T03|квалифицированный document/evidence corpus|
|T05 Verification issuer|P0|T01;реальная приёмка послеT04/T06|защищённый review путь без ослабления gate|
|T06 Нормативные правила|P1|T04,T05|проверенный rule catalog и UI comparison/review|
|T07 Engineering runs / расчёты|P1|T01,T02|общий тонкий job adapter и контрольные расчёты в UI|
|T08 CAD|P1|T02,T07|bounded source census/геометрические проверки/roundtrip/UI|
|T09 BIM|P1|T02,T07|IFC UI/GUID Evidence/qualification|
|T10 Реальная приёмка|P1|T04–T09|свежий положительный case и отрицательный контроль|
|T11 Память/FINAL export|P1|T10|real accepted-origin memory и принятое заключение|
|T12 Windows qualification|P1|T01–T11|reboot/offline/update/backup/rollback receipts|
|T13 Release|P2|T12,всеR01–R11|main/tag/дистрибутив/FINAL_RELEASE_AUDIT|
|V01 Vendor ЛИРА/SCAD|отдельно|T02,T07|полные документированные vendor packets при достаточных исходниках|

T05 можно разработать на controlled fixtures параллельноT02–T04; это не закрывает
реальную приёмку. T08/T09 независимы после общегоT07. Инженерный положительный
кейс не обязан использовать vendor solver, если его управляющее ТЗ этого не требует.
Для текущего объекта требования расчёта и недоступные результаты остаются явными.

Общая проверка каждого пакета: failing regression → подтверждённый RED → минимальное
исправление → focused/integration/negative checks → отдельный reviewable commit/PR →
exact-head CI → обновление матрицы. Повторять full suite после итогового пакета,
не после каждой правки документации. Не дублировать уже зелёные проверки без причины.

## T01. Идентичность сборки и поставки

**Files:** Create `engineering/local_app/build_identity.py`, `scripts/build_release_manifest.py`, `tests/test_build_identity.py`; modify `server.py`, `tooling.py`, `ui/app.js`, `scripts/windows_supervisor.ps1`, `docs/development/release-checklist.md`.
**Consumes:** immutable release manifest + startup code/config paths.
**Produces:** `build_identity(manifest_path: Path) -> dict` с `version,tree_sha256,dirty,schema_version,profile,manifest_sha256`; GET `/api/build` и тот же startup identity в worker receipts. Dirty checkout помечается явно; venv path не считается build identity.

- [ ] Добавить `test_running_build_matches_release_manifest`, `test_dirty_or_changed_bundle_is_not_release`, `test_worker_ui_and_server_identity_match`; assert exact manifest hash/tree/profile и invalidation после изменения файла.
- [ ] RED: `python -m unittest tests.test_build_identity -v` до реализации; сохранять причину отказа.
- [ ] Реализовать startup-frozen identity и генератор manifest с отсортированными file digests; existing `/api/status` не менять несовместимо. UI показывает версию и выбранный profile.
- [ ] На тестовом порту сравнить API/worker/UI с manifest; никакой подмены running file tree за уже загруженный код. План поставки выбирает отдельную чистую папку вместо dirty132entries.
- [ ] GREEN+commit. **Done:**R01идентифицируется программно; пользователь видит, какая сборка работает.

## T02. Воспроизводимый Windows engineering profile

**Files:** Create `scripts/prepare_engineering_profile.ps1`, `engineering/local_app/capability_receipts.py`, `tests/test_engineering_profile.py`, `requirements-engineering-windows.lock`; modify `tooling.py`, `settings.py`, `windows_supervisor.ps1`, `local-environment.md`, `windows-runtime.yml`.
**Consumes:**T01build, существующие окружения/кеши; зависимости из текущих requirements.
**Produces:** `capability_report(profile: str) -> dict`: для каждой capability `installed,configured,probe_status,version,artifact_hashes,limitations`; SUCCESS только после реального fixed local probe. Отсутствующий optional IFC не мешает базовому чату.

- [ ] RED tests `test_installed_package_without_models_is_not_ready`, `test_offline_profile_uses_only_verified_cache`, `test_missing_optional_adapter_keeps_base_starting`; имитировать пустой/повреждённый cache и network denied.
- [ ] В отдельном окружении зафиксировать реально испытанные Windows wheels/модели/внешние executable hashes. Docling из другойvenv не объявлять установленным в runtime. Не копировать Linux lock в Windows.
- [ ] Подготовить явный выбор native/engineering profile и проверенные пути OCR/Office workers. Тяжёлые модели загружаются только отдельным действием подготовки; существующий Qwen переиспользуется.
- [ ] Доказать offline smoke: скан→OCR,таблица→reader,формула→passive preview,IFC/контрольная балка; отсутствие лицензии/бинарника/модели даёт конкретную capability error. Проверить licenses/redistribution до включения binaries.
- [ ] `python -m unittest tests.test_engineering_profile tests.test_windows_one_click -v`; повторная подготовка идемпотентна. **Done:**R02профиль воспроизводим; отсутствие Tesseract/LibreOffice не маскируется package presence.

## T03. Windows Office layout и объекты

**Files:** Create `engineering/local_app/office_render.py`, `engineering/local_app/windows_document_worker.py`, `tests/test_office_render.py`; modify `office.py`, `word_formula_preview.py`, `word_objects.py`, `source_assets.py`, `doc_conversion.py`; preserve `doc_sandbox.py` Linux contract.
**Consumes:**T02pinned renderer;original bytes/sha; source parts/relationships.
**Produces:** `render_office_source(source: Path, *, expected_sha256: str, destination: Path) -> dict`: неизменный original, отдельный rendered PDF/pages,renderer identity,page/part/asset map,limitations;не engineering_verified.

- [ ] RED `test_source_hash_and_all_objects_bound_to_render`, `test_merged_cells_omml_emf_and_rotated_images_located`, `test_external_links_macros_ole_never_activate`, `test_timeout_kills_only_owned_tree`, `test_legacy_doc_converts_only_in_controlled_windows_worker`.
- [ ] До открытия произвольного пакета испытать Windows worker isolation: новый профиль,Job Object resource/child limits,ограниченный токен/AppContainer без network capabilities,никаких макросов/внешних связей. Probe должен доказать доступ к нужному локальному IPC и запрет внешней сети;иначе worker UNAVAILABLE,а не фиктивный sandbox.
- [ ] Связать DOM/part/relationship объекты с производным render;физические страницы не выдумывать из logical units. Formula passive preview оставить отдельным: он не подтверждает исходный layout/math.
- [ ] На копиях текущих4DOCX получить renderer receipts и независимые PDF references. СтарыйV4PDF использовать только при проверенной source/renderer lineage.
- [ ] `python -m unittest tests.test_office_render tests.test_local_source_assets tests.test_formula_ipc_sandbox -v`; visual source comparison. **Done:**R03Windows source view существует, активный контент не исполняется, ограничения объектов явны.

## T04. Документная полнота, image-only ТЗ и возобновление

**Files:** Create `engineering/document_intelligence/qualification.py`, `scripts/qualify_document_corpus.py`, `tests/test_document_qualification.py`; modify `corpus_audit.py`, `asset_candidate_ledger.py`, `extraction.py`, `automatic_analysis.py`, `coverage.py`, `requirements.py`, `store.py`, `scripts/stage7_real_case_offline.py`; use existing reviewed-recovery scripts.
**Consumes:**T03render manifests;versioned private source manifest;existing parser/page/receipt identities.
**Produces:** `qualify_document(manifest: dict, observations: list[dict]) -> dict` с per-object/cell/number status and source locators; `qualified_scope,unaccounted_objects,critical_numeric_mismatches`. Полнота только при0unaccounted/0mismatches и достаточных reviews.

- [ ] RED fixtures caption-without-rows57/58,merged/raster table,decimal comma/minus/mm↔m,OMML,field/crop/rotation. `test_token_recall_cannot_mask_wrong_cell_value` ожидает BLOCK при одной неверной критической цифре.
- [ ] Сначала воспроизвести каждую реальную потерю, затем исправить соответствующий reader/recovery. Не снимать limitation после счётчика страниц; unsupported object остаётся в quality dossier.
- [ ] Image-only ТЗ:review transcription→original image hash/part/region→requirements set. Для текущегоТЗ сохранить scope исключения фундаментов;не расширять перечень работ произвольно.
- [ ] Устранить semantic mismatch offlineStage7 ZIP-only nativeLIR probe:разделить byte identity/unsupported format/engineering semantics;проверить bounded header read и input post-check. Не выдавать непонятный header за corruption.
- [ ] Полный текущий content corpus:5PDF/4DOCX,не backup/owner. Сверить все листы/объекты/критические значения с эталоном и независимыми fixtures. Все невозможные проверки фиксируются как конкретные remaining inputs,не PASS.
- [ ] Interrupt/resume в extraction и живом Qwen analysis:нет потерянных units,дубликатов принятого output,зависших RUNNING;source/parser/model change запрещает reuse. Полный новый journal не смешивать со старыми137/52BLOCK receipts.
- [ ] `python -m unittest tests.test_document_qualification tests.test_document_analysis_resume tests.test_source_corpus_audit tests.test_stage7_real_case_offline -v`; private full-corpus report. **Done:**R03/R04/документная частьR11;полныйV4 не подменён выборкой.

## T05. Защищённый verification issuer

**Files:** Create `engineering/local_app/verification.py`, `tests/test_engineering_verification.py`; modify `store.py`, `requirements.py`, `review.py`, `engineering_review.py`, `domain_packets.py`, `real_case.py`, `final_audit.py`, `server.py`, existing UI.
**Consumes:**immutable current subject/source/review revisions;source-qualified candidates;explicit responsible reviewer action.
**Produces:** `issue_verification(store,session_id,*,subject_kind,subject_id,expected_revision,decision,reviewer,method,source_refs,reason) -> dict`; `revalidate_verification(store,record) -> dict`. Record binds subject/source digests,scope/version/time and MAC from existing server-owned key. It authenticates local issuance,не civil identity/истинность факта.

- [ ] RED `test_model_or_import_cannot_self_issue`, `test_wrong_revision_cross_session_or_unqualified_source_refused`, `test_valid_review_record_invalidated_by_source_rule_or_review_change`, `test_missing_key_never_grants_acceptance`.
- [ ] Добавить append-only verification events/migration с backup. Метод issuer принимает review action,не готовую signature/engineering_verified из body;проверяет subject kinds,точныйscope,полноту source refs,актуальность и предметные prerequisites. Нельзя кнопкой обойти непроверенные нормы/измерения.
- [ ] Предварительные readers остаются предварительными;verified overlay применяется только после revalidation действительного record. Не менять `final_audit._verified_record` на принятие произвольного reviewer string.
- [ ] В существующем UI показать source→decision→reviewer/method→scope→подтверждение. Local API проверяет token/origin,explicit review intent и revisions;модель не инициирует действие. Действия revoke/re-review версионируются.
- [ ] `python -m unittest tests.test_engineering_verification tests.test_final_audit tests.test_tor_source_responsibility -v`; браузерная tamper/stale проверка. **Done:**штатный positive issuance работает на controlled contract,negative cases BLOCK;реальныйACCEPTED только вT10.

## T06. Нормативный каталог и UI-проверка

**Files:** Create `engineering/normative/catalog.py`, `tests/test_normative_catalog.py`; modify `rule_registry.py`, `source_verification.py`, `authority.py`, `substantive_review.py`, `local_app/domain_packets.py`, `server.py`, existing UI.
**Consumes:**T04ACTUAL/MEASURED/TESTED evidence,T05review authority;lawful full normative sources.
**Produces:** `load_rule_catalog(path: Path) -> RuleRegistry` и source-bound assessment receipts с rule digest/edition/clause/scope/effective dates/input classes/units. Ready arithmetic не равна normative ACCEPTED.

- [ ] RED `test_metadata_without_clause_text_is_not_rule`, `test_wrong_edition_scope_date_or_units_blocks`, `test_rule_change_invalidates_case`, `test_project_dimension_cannot_substitute_measured_value`.
- [ ] Из управляющегоТЗ построить перечень необходимых требований и источников;для каждого проверенный document→edition→scope→clause→requirement. Нет полного/законного source — правило не квалифицировано.
- [ ] Реализовать immutable catalog loading и connect registry→existing domain packet review. UI даёт открыть нормативный source/пункт и фактический evidence;разные редакции отображаются как conflict,не автоматически ERROR испытаний.
- [ ] Выполнить первый реальный scoped comparison с точным пунктом и достаточным actual input;signed subject выдаётT05после предметной проверки. Никаких вымышленных clause numbers.
- [ ] `python -m unittest tests.test_normative_catalog tests.test_normative_rule_registry tests.test_normative_substantive_review tests.test_domain_packets -v`. **Done:**R05на заявленном catalog,без недоказанного покрытия всех норм.

## T07. Общий engineering job adapter и контрольные расчёты

**Files:** Create `engineering/local_app/engineering_jobs.py`, `tests/test_engineering_jobs.py`, `tests/test_calculation_ui.py`; modify `store.py`, `worker.py`, `server.py`, existing UI;reuse `control_beam.py`, `planar_control.py`, `section_control.py`.
**Consumes:**source/config file IDs + exact versions,T01profile,T02capabilities.
**Produces:** `enqueue_engineering(store,session_id,*,tool,input_file_ids,options,expected_revision) -> dict` и `execute_engineering(store,job,stop) -> dict`. Tool allowlist:BEAM/PLANAR/RECTANGLE/CAD_INVENTORY/CAD_DIFF/CAD_ANNOTATE/DWG_CONVERT/IFC_INVENTORY/IFC_GEOMETRY/IFC_REQUIREMENTS/IFC_DIFF. Add `ENGINEERING_RUN` to existing job mode,не новая queue.

- [ ] RED `test_foreign_file_or_changed_config_refused`, `test_cancel_preserves_sources_and_partial_receipt`, `test_engineering_result_does_not_auto_create_accepted_evidence`.
- [ ] Хранить bounded request JSON/hash в связанном с существующимjob input record;не пихать64KiBconfig в8KiBchat prompt. Оригиналы/config сохраняются отдельно. Worker dispatch reusable adapters с explicit limits,not runtime duplication.
- [ ] В UI ввести единицы,материал,сечения,нагрузки/закрепления,source refs;показать схему,inputs hash,реакции/усилия/перемещения и limitation. Поддержка:UDLbeam,linearXYnodal-loadframe/truss,rectangle. Остальные нагрузки/геометрии не молча аппроксимировать.
- [ ] Проверить аналитические горизонтальную/вертикальную консоли,rigid elbow,axialbar,triangletruss,rectangleI/W;huge moment не скрывает force imbalance. Отдельный candidate может стать Evidence только с source reviewT05.
- [ ] `python -m unittest tests.test_engineering_jobs tests.test_calculation_ui tests.test_control_beam tests.test_planar_control tests.test_section_control -v`; Chromium UI path. **Done:**R06user-accessible и bounded;сам benchmark не принимает фактическую конструкцию.

## T08. CAD: геометрия, крупные файлы и roundtrip

**Files:** Create `engineering/cad/source_census.py`, `engineering/cad/geometric_checks.py`, `tests/test_cad_source_census.py`, `tests/test_cad_geometric_checks.py`; modify `conversion.py`, `dxf_workflow.py`, `roundtrip.py`, `local_app/cad.py`, `engineering_jobs.py`, UI.
**Consumes:**T07jobs,current source identities,independent native census when available.
**Produces:** `compare_source_to_derivative(source_manifest: dict, derivative_manifest: dict) -> dict` и `check_geometry(census: dict, rules: list[dict]) -> dict` с handle/layer/unit/source-located observations;separate loss ledger.

- [ ] RED lost block/text/dimension/proxy/units/cropped layout cases; `test_zero_exit_truncated_dxf_is_blocked`, `test_dimension_text_disagrees_with_measured_geometry`, `test_census_limit_never_reports_complete`.
- [ ] Минимизировать воспроизводимый graphics export failure НА КОПИИ:точные converter versions/logs,проблемный layout/entity/handle,зависимые resources. ODA/native both fail не доказывает corruption исходника. При необходимости получить исправленный экспорт от автора;источник не repair/save автоматически.
- [ ] Реализовать независимый source census для заявленных поддерживаемых объектов;если данных нет,эквивалентность остаётся BLOCK. Полный геометрический анализ lines/polylines/layers/blocks/dimensions/text/placement с явными coordinate frames/units.
- [ ] Дляlarge geodesy выбрать resource-bounded child/streamed inventory с chunked result storage. Сначала измеритьlimits,память/timeout/прерывание;не просто увеличить20MiB/50000/10000. Proxy/unknown entities не выкидывать из completeness.
- [ ] Сверить source→DXF→controlled annotation/export→reimport:geometry/resources/text/dimensions/units/layouts и визуальные листы. Все неизменяемые части exact/нормализованно совпадают;намеренные изменения перечислены. Отображение loss ledger в UI.
- [ ] `python -m unittest tests.test_cad_source_census tests.test_cad_geometric_checks tests.test_cad_conversion_route tests.test_cad_roundtrip_comparison tests.test_local_app_cad -v`. **Done:**R07на qualified corpus,текущие неудачи имеют проверенный исход/явную внешнюю зависимость,не скрытыйPASS.

## T09. BIM / IFC в пользовательском процессе

**Files:** Modify `ifc_adapter.py`, `ifc_geometry.py`, `ifc_requirements.py`, `engineering_jobs.py`, `evidence.py`, `source_binding.py`, `server.py`,UI;create `tests/test_ifc_evidence_ui.py`, `tests/test_ifc_worker_limits.py`.
**Consumes:**T07jobs/T02child limits,legal independent real IFC,existing syntheticfixture.
**Produces:**source-locator `kind='IFC_GUID',source_sha256,guid,model_revision,property_path`;registration validates actual GUID/property against same source,not model text.

- [ ] RED `test_unknown_or_wrong_model_guid_refused`, `test_units_and_numeric_types_cannot_be_relabelled_dimensionless`, `test_mesh_memory_timeout_and_nan_block`, `test_revision_diff_invalidates_old_evidence`.
- [ ] Подключить существующие inventory/geometry/requirements/diff в UI черезT07. IFC PROJECT остаётся PROJECT;actual_condition изBIMне выводится.
- [ ] Обеспечить hard child memory/output/time bounds до/во времяmesh,а не только vertices послеtriangulation. НаWindows использовать тот же испытанный process boundary,не новый универсальныйagentframework.
- [ ] Проверить реальный независимый IFC2X3/IFC4 corpus:storeys/elements/materials/quantities/units/relations/rules/diff;отсутствиеrepresentation=NOT_VISIBLE,не«элемента нет». Real IFC текущего объекта отсутствует:нужен корректный экспорт или отдельный legal qualification corpus.
- [ ] `python -m unittest tests.test_ifc_evidence_ui tests.test_ifc_worker_limits tests.test_ifc_adapter tests.test_ifc_geometry_completion -v`;ChromiumGUIDsource path. **Done:**R08,не утверждать автоматическую расчётную схему.

## T10. Реальный положительный и отрицательный инженерные кейсы

**Files:** Create `scripts/qualify_real_case.py`, `tests/test_real_acceptance_workflow.py`, `docs/qa/real-acceptance-protocol.md`;modify `real_case.py`, `final_audit.py` only for proven integration gaps.
**Consumes:**T04qualified requirements/evidence,T05records,T06norms,T07–T09applicable observations,source manifest.
**Produces:**source-bound immutable realcase/FINAL_AUDIT receipt,scope/decision/reviewer/method;redacted reproducible QA summary.

- [ ] RED `test_real_store_workflow_needs_all_verified_subjects`, `test_changed_source_or_rule_after_review_invalidates_audit`, `test_unsupported_domain_cannot_be_omitted_to_force_acceptance`.
- [ ] Выбрать достаточный реальный кейс и явно зафиксировать его управляющееТЗ/границы/required domains до решений. Узкий positivecase подтверждает свойscope;не закрывает автоматически всёV4или безопасность здания.
- [ ] Через штатный UI/API пройти upload→ТЗ→source review→Evidence/data classes→specialists→normative/calculation→responsible review→case QC→FINAL_AUDIT. Не писать подписи напрямую вSQLite и не вызывать тестовыйfixture для результата.
- [ ] Получить ACCEPTED либо ACCEPTED ALTERNATIVE только при достаточных фактах. Отдельно пройти действительный отрицательный/недостаточный/stale кейс;не придумывать дефект ради ERROR.
- [ ] `python -m unittest tests.test_real_acceptance_workflow tests.test_final_audit -v`;private original-preservation receipt + signed basis. **Done:**R09 и№14;при недостаточных данных остаётся точный input list,не переименование BLOCK.

## T11. Подтверждённая память и FINAL DOCX/PDF

**Files:** Modify `knowledge.py`, `conclusions.py`, `conclusion_export.py`, `server.py`, UI; Create `tests/test_final_conclusion_export.py`, `e2e/local_accepted_memory_report_ui_smoke.cjs`.
**Consumes:** T10 fresh accepted audit; T05 verified subjects; source refs и версии правил/расчётов.
**Produces:** `build_final(store,session_id,*,expected_audit_id,expected_revision,author) -> dict` и exact-source final export manifest. Existing draft build/export compatibility сохранена; final/draft — разные состояния.

- [ ] RED: `test_stale_or_revoked_audit_cannot_export_final`, `test_promoted_real_knowledge_revoked_after_source_change`, `test_report_numbers_units_evidence_and_illustrations_roundtrip`.
- [ ] Реально выполнить promote/recall accepted-origin в другой разрешённой session. Recall — контекст, не Evidence или приёмка нового объекта. Отзыв, обновление, удаление и key loss исключают прежние знания из доверенного recall.
- [ ] Добавить FINAL export только для свежего принятого основания: таблицы, изображения, расчётные приложения, пункты норм, Evidence, ограничения и точный audit ID. Правка авторского текста после приёмки создаёт новую draft revision, не сохраняет прежнюю подпись.
- [ ] Прочитать готовые DOCX/PDF заново, сверить все критические числа, единицы и ссылки. Рендер каждой страницы и визуальная проверка таблиц, обрезок и изображений. ZIP/PDF header не подтверждает правильность заключения.
- [ ] `python -m unittest tests.test_final_conclusion_export tests.test_confirmed_knowledge tests.test_conclusion_drafts tests.test_conclusion_illustrations -v`; новый Chromium real-origin path. **Done:** R10, №15/16 на реальном кейсе.

## T12. Windows install / update / reboot / offline / recovery

**Files:** Modify `windows_supervisor.ps1`, `windows_stop.ps1`, `windows_poststart_smoke.py`, launchers, backup/recovery UI; Create `scripts/windows_release_qualification.ps1`, `tests/test_release_upgrade.py`; update CI.
**Consumes:** T01 release identity, T02 profile, T10/T11 real data, qualified runtime.
**Produces:** qualification JSON с exact build/profile/OS/boot epoch, source preservation, history/receipts/keys, offline/start/update/rollback evidence. Проверки имеют отдельные поля; один флаг physical_verified их не заменяет.

- [ ] RED: `test_upgrade_and_rollback_keep_history_originals_and_key`, `test_key_loss_invalidates_acceptance_without_data_loss`, `test_busy_owner_and_wrong_port_are_never_killed`.
- [ ] На чистом Windows 11 в non-admin пути с кириллицей/пробелами выполнить подготовку и one-click запуск. Для существующей установки сначала создать backup; dirty source folder не перезаписывать. Миграция данных/ключа/receipts транзакционна; неподдерживаемый downgrade блокируется.
- [ ] После подготовки отключить внешний доступ и пройти document→Evidence→norm/control→case→report. Loopback Ollama работает; скрытых downloads/API dependencies нет.
- [ ] Reboot подтвердить разными фактическими boot epoch до/после и persistent session/source receipts. Подготовить scoped restart plan; не перезагружать ПК с несохранённой работой без согласованного окна. Отдельно проверить crash/kill собственного worker/resume, backup→clean restore и update→rollback.
- [ ] `python -m unittest tests.test_release_upgrade tests.test_local_backup_restore tests.test_data_backup tests.test_recovery_path_security -v`; Windows browser/live model и private reboot receipt. **Done:** R02/R11 доказаны на этой сборке; Linux CI и restart сервера не заменяют reboot.

## T13. Консолидация и стабильный выпуск

**Files:** Modify `release-checklist.md`, `ENGINEER_OS_PROJECT_MAP.md`, `master-plan.md`, `project-map-handoff.md`, CI/release packaging; Create `docs/qa/final-release-audit.md`, versioned artifact manifest.
**Consumes:** все gate receipts; T12 qualified tree; полный git main/candidate diff.
**Produces:** единственная поставляемая version, main/tag/release artifact/checksums/profile manifest/rollback instructions и FINAL_RELEASE_AUDIT.

- [ ] Заморозить код и corpus/profiles; пройти R01–R11 с actual receipts. Каждый SKIP сопоставить поддерживаемому scope: он не закрывает обязательную функцию. Открытых release blockers — 0.
- [ ] Классифицировать 57 открытых PR по фактическому tree/diff: included/superseded/new-required/conflicting. PR148 code включён через153 — повторно не объединять. PR149/151 проверить на новые доказательства и исторические данные; PR100/102 — vendor tools, не автоматические зависимости runtime. PR74 может стать единым main release PR после актуализации описания и CI.
- [ ] На exact final tree: full Python, JS, Chromium, Windows, optional Linux/Windows, guards, pip check; SAST/CodeQL, dependency/license/secret review. Security guard не подменяет проверку всех уязвимостей. Проверить полный diff 375+ commits, не усечённую API-страницу files.
- [ ] Проверить лицензию проекта и условия распространения bundled dependencies; предоставить source/notices, где требуется. Собрать дистрибутив без private sources, секретов и пользовательской venv; включать только проверенные разрешённые binaries/caches.
- [ ] После обязательного зелёного CI перенести candidate в main, проверить result tree/checks. Создать version/tag/checksums/release; выполнить clean install из скачанного артефакта. Не выпускать сборку из dirty checkout.
- [ ] **Done:** R12, все19 обязательных критериев приняты в заявленном scope; карта содержит единственную актуальную сводку. Исторические QA сохранены отдельно.

## V01. ЛИРА/SCAD — отдельный vendor qualification

**Files:** Existing `native_source.py`, `native_tables.py`, `native_results.py`, `vendor_adapters.py`, `solver_bridge.py`, `execution_identity.py`, `structure_correlation.py`; изучить exporters PR100/102 до переноса кода в приложение. Новые bridge/adapters/tests — только по подтверждённому SDK-контракту.
**Consumes:** документированный API/версия/битность, staged native files, полные сохранённые результаты/log/task context с model/run identity.
**Produces:** qualified exchange/results/solver-run/actual-structure packets; header-only compatibility недостаточно.

- [ ] Получить отдельно заведомо рабочий vendor result case. Сопоставить task title/path/result folder, COM context и API argument requirements с официальной документацией. 90 E_UNEXPECTED не устанавливают причину отказа или отсутствие результатов.
- [ ] Извлечь KE57 auxiliary stiffness, материалы/сечения, опоры/releases, единицы, нагрузки и сочетания. Учесть failed/empty/parameter-unavailable table types; проверить документированные text/native export варианты без binary guessing.
- [ ] Проверить native/result/run hashes, solver warnings, направления/units/results coverage и соответствие actual structure. Запуск solver не заменяет проверки схемы; работа только на копиях с owned cleanup.
- [ ] SCAD: сначала SDK/export compatibility и legal reference file. До этого adapter NOT_IMPLEMENTED/UNAVAILABLE, а не «поддерживается».
- [ ] `python -m unittest tests.test_lir_source_identity tests.test_solver_execution_integrity tests.test_calculation_model_intake -v` и отдельные реальные vendor receipts. **Done:** положительный и намеренно неполный/несовпадающий result case. Это не условие базового runtime, но необходимо для заявленной vendor feature или требующего её ТЗ.

## Передача исполнения и self-review

Первый пакет: T01→T02, затем T03/T04 и T05. Новые модели, перерисовка UI и публикация release не являются первыми действиями. Для каждого пакета сохранять код, проверку, receipt, remaining inputs и next action. Ни один будущий чек в этом плане не объявлен выполненным.

Охват MASTER: §5→T03/04; §6→T08; §7→T09; §8→T07/V01; §9→T06; §10→T01/02/05–09/12; §11→T10/11; отложенные инструменты §12 не добавляются; tests §13→всеT; GitHub §15→T13 и каждый PR. Все19 критериев сопоставлены в аудите. Новые файлы помечены Create; существующие пути проверены. Пять review focus привязаны к тестам. Неизвестные vendor semantics и external data не объявлены готовыми.

## Базовый выпуск и полный запрошенный объём

12release gates определяют базовый инженерный выпуск1.0. Это не отменяет ранее
запрошенное закрытие всех восьми направлений. Для заявления «весь исходный объём
готов на100%» дополнительно должен быть завершёнV01в заявленном vendor scope:
ЛИРА — полная проверяемая цепочка исходных данных/результатов, SCAD — подтверждённое
исследование API/export и совместимости без обещания неподтверждённой функции.
Если vendor-проверки нужны управляющемуТЗ или реклама включает их поддержку,
соответствующая готовность остаётся BLOCK до фактических receipts. Решение выпустить
базовую версию раньше не закрываетV01и не выдаётся за закрытие всей задачи.
