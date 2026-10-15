# Этап2 — продолжение: адресные проверки источников

База225ee83, локальная ветка codex/v1-completion-20261015. Рабочая программа в пользовательском checkout и server8765 не заменялись; этот пакет пока локален. Текущий проход не является FINAL_AUDIT объекта или выпуском.

## Реализовано

1. Новый bounded source/reference/parser-bound per-object comparator и CLI с exclusive output, snapshot SHA точных разобранных JSON, повторной проверкой источников и parser, отказом при stale/duplicate/foreign/missing objects.
2. Native-cell identity до служебных аннотаций в существующем Word reader, без изменения текста/merge semantics и без снятия ограничений.
3.20новых тестов, в том числе RED→GREEN для гонки JSON после разбора, знака/десятичной запятой/единиц и пустого merge continuation. Предварительные44и затем58focused tests PASS; architecture guard PASS. Общая регрессия новой окончательной версии записывается ниже отдельно.
4. Независимый reviewer: actionableP1/P2 не найдено.10pure comparator tests и2native-cell tests он выполнил;8file tests у reviewer заблокированы sandbox temp permissions и не объявлены независимым PASS.

## Реальные источники

Повторный пассивный census:29файлов,1056PDF pages,18176DOCX logical units; пять DOCX включают один Word owner file, исключённый из контента. Исходники совпали с предыдущим SHA manifest; source tree и originals unchanged. Это инвентаризация, не квалификация содержимого.

Четыре действительных DOCX прошли новый source→Store→production assets/reader→reference-comparison маршрут. В независимом lxml/ZIP reference и production outputs совпали:

| Объём | Проверено | Не подтверждено этой проверкой |
|---|---:|---|
| Прямые XML-ячейки |14940/14940;6972с цифровыми фрагментами|Физическое положение/объединение на странице и инженерная правильность значений|
| OMML element trees |82/82|Внешний вид, математическая корректность и формулы внутри OLE|
| Media/embedded bytes |1090/1090|Содержание картинок, EMF geometry, активация или корректность OLE|

Во всех трёх областях0missing/0mismatch, исходные SHA сохранены. В четырёх источниках XML-cell count совпал с поддержанными direct-cell locators: unaccounted XML cells0. Это не распространяется на весь иной контент DOCX. Текст модели не использовался для назначения PASS. Все данные остаются PROJECT/source observations; acceptance=false.

## ТЗ

Проверены оригинальные image5/image6 из текущего V4: сохранённые PNG совпали с ZIP bytes. Составлен приватный реестр49интерпретированных условий (строки1–6 отдельно как metadata).7позиций оставлены UNCERTAINTY: точные шифры/URL, пространственный диапазон, приборы, условия вскрытий, частично закрытая строка13.3. Два напечатанных14.4разделены по порядку строк. Полной дословной транскрипции и выполнения ТЗ не объявлено; нормы и ЭДО-подписи не квалифицированы. Фундаменты исключены управляющим ТЗ и не объявляются отсутствующим обследованием по умолчанию.

## Windows source renderer: выявленные границы

Собственные normal-control TXT/DOCX→PDF ранее PASS. В этом проходе подтверждены AppContainer token=1,capabilities=0,запрет чтения постороннего canary,успешная запись в собственный profile,отказ подключения к собственному доступному TCP listener (normal control CONNECTED). GLOBAL named pipe:ERROR_ACCESS_DENIED5; LOCAL pipe:OK. Исходники точного LibreOffice buildbf6ef266 подтверждают обычный OSL_PIPE namespace.

CLI .com и прямой .bin в AppContainer дали exit1/noPDF. Официальный встроенный LibreOfficeKit избегает межэкземплярного IPC через RequestHandler::Enable(false), но завершился77/noPDF при создании user installation. Отдельные проверки выявили: stat/copy presets доступны, canonical DOS path недоступен. Это согласуется с [подтверждённым ограничением Microsoft AppContainer](https://github.com/microsoft/STL/issues/6286), однако единственная причина ошибки LibreOfficeKit полностью не доказана. Подготовленный профиль и штатная папка AppContainer её не устранили. Vendor binaries не патчились; capabilities/защита не ослаблялись; реальные документы движком не открывались.

Одна попытка распространения metadata ACL прервана: только собственные дваPID остановлены, собственный профиль удалёнHRESULT0. Остальные профили и временные ancestor/engine grants также удалены; финальная проверка remaining own profiles0/parent+engine ACEs0. Это частная диагностика, не production sandbox. Установленных Windows Sandbox/Docker в проверенных путях/командах не обнаружено; WSL backend не получен. Компоненты ОС не включались, перезагрузка не выполнялась.

## Остаток этапа2

Защищённый Windows source-layout worker всё ещё не квалифицирован. Затем требуются source-bound визуальная сверка всех страниц/объектов, OCR и семантика изображений, merged-cell layout, MathType/OLE/формулы, полное точное ТЗ и привязка предметных выводов. Оставшиеся UNKNOWN/BLOCK не сняты количеством совпавших хешей. Новый comparator является исполняемым компонентом T04; интерфейс полного review и доверенный эталон он не заменяет.

## Финальная проверка программного пакета

`python -m unittest discover -s tests`:1275tests,380.576s,OK(skipped=34),exit0. Это финальная версия с native-cell identity; предварительный1273suite относился к версии до этих трёх строк.58focusedtestsPASS, architecture/repository guardsPASS, diff checkPASS. Профили и тестовые входы не устанавливались поверх пользовательского окружения.

В полном журнале остался прежний ConnectionAbortedError в позднем ответе тестового HTTP handler test_task_controls.py и Pillow deprecation; unittest завершилсяOK. Новый production defect этим выводом не установлен; вывод сохранён. Пропуски не засчитаны как выполненные обязательные функции. UI browser/CI/main/release в этом проходе не объявляются проверенными или обновлёнными.

После всех реальных чтений29/29файлов,828577307bytes,тот же file set и все SHA unchanged. Исходные конфиденциальные байты, реестр ТЗ и результаты хранятся только в private QA folder. Отпечатки четырёх изменённых code/test files — tested-code-sha256.json, общий журнал — regression-final.log.

Вывод: закрыта узкая проверка сохранности указанного native-содержимого четырёх DOCX на текущем reader, а не весь этап2. T03 source renderer/isolation и T04 визуальная/семантическая полнота и точное image-only ТЗ остаются открыты. От пользователя повторный путь к комплекту не требуется.
