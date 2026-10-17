# Адресная сверка документа с эталоном

T04: `engineering.document_intelligence.qualification.qualify_document(manifest, observations)` сравнивает каждый объявленный объект, его locator, тип, SHA полезной нагрузки и source/reference/parser identities. Пропущенный объект, несовпадение и устаревшая версия блокируют сравнение; повторный или чужой ID отклоняется. Число объектов не заменяет адресную сверку.

Manifest schema1 содержит source_sha256, reference_sha256, parser_sha256 и непустой objects. Поля объекта: object_id, kind (paragraph/table_cell/formula/image/embedded_object), source_locator, reference_locator, payload_sha256, critical_numeric. Observation повторяет поля объекта и три identity. Неизвестные поля, неподдержанные типы, некорректные SHA и избыточные размеры запрещены. Максимум50000объектов; JSON вход CLI не более16MiB, source/reference не более256MiB каждый.

CLI: `python scripts/qualify_document_corpus.py --source SOURCE --reference REFERENCE --manifest MANIFEST.json --observations OBSERVATIONS.json --output NEW-RESULT.json --backend docx`. Он проверяет реальные SHA обоих файлов и текущую parser identity; квитанция привязывается к точным прочитанным байтам JSON, затем все входы и parser повторно проверяются. Результат записывается отдельно с exclusive create/readback, входы и существующий output не перезаписываются. Symlink/junction inputs не поддержаны. Source/reference файлы не исполняются. CLI требует уже подготовленные reference/observations; он сам не создаёт достоверный эталон и не выполняет renderer.

Успех — comparison_status=PASS и READY_FOR_INDEPENDENT_REVIEW. Полнота документа, достоверность эталона, визуальная семантика и engineering acceptance остаются НЕ подтверждены: document_completeness=NOT_QUALIFIED, qualified_scope=[], acceptance_granted=false. Это компонент подготовки проверки, не новый issuer и не завершённый UI-процесс приёмки.

`critical_numeric_mismatches` перечисляет расхождения критически помеченных объектов, включая identity/locator, а не доказывает ошибку фактического измерения. При byte/tree comparison несовпадение полезной нагрузки не локализует автоматически изменённую цифру. Нормы, математическая правильность формул и фактическое состояние конструкции этим путём не оцениваются.

## Native text ячеек Word

Locator table_cell теперь содержит native_text_identity: SHA-256, длину исходного текста прямых параграфов ячейки, scope=XML_CELL_NATIVE_TEXT_BEFORE_ANNOTATIONS и layout_verified=false. Хеш вычисляется до метаданных объединений, изображений/OLE и добавленного текста вложенных таблиц. Пустое продолжение объединения остаётся пустым: значение верхней ячейки не подставляется. Вложенные ячейки имеют отдельный существующий inventory; новый native hash не обещает их физическую разметку.

Обычный вывод текста и ограничения reader сохранены. Office parser identity включает SHA office.py: старые extraction/comparison receipts не переносятся на изменённый reader автоматически.

## Проверенный текущий комплект

В четырёх реальных DOCX независимое lxml/ZIP чтение сопоставлено с production reader/assets:14940native cells,82OMML element trees,1090media/embedded payloads. Среди ячеек6972содержат цифровые фрагменты; это не число независимо проверенных инженерных параметров. Пропусков и несовпадений в названных областях не найдено. Проверка OMML включает расширенные имена элементов, атрибуты, текст и порядок детей; root tail не относится к формуле. Это не проверка внешнего вида, математической корректности, OCR изображений или OLE-содержимого.

Актуальные квитанции, точные locators/проверочные входы и исходные данные сохранены приватно в `.engineer-os/v1-completion/document-qualification/qualified-payloads-33b6cd70f29647309c1e6ef1073fabb0`. Старые experiments с прежней parser identity являются историей. Проектная инженерная приёмка и весь этап2 остаются открыты.
