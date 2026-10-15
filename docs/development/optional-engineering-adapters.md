# Optional IFC, DXF comparison и контрольная балка

Все инструменты локальные, бесплатные, без AI API. Они не являются автоматическим
FINAL AUDIT. UI/Ollama и обязательный runtime не меняются. Установка после
подготовки может использовать локальный wheel cache; сами команды обработки
не обращаются к сети и не скачивают модели.

## Подготовка Windows

Создать отдельное окружение, не поверх работающего OCR/runtime:

```powershell
py -3.13 -m venv .venv-engineering
.\.venv-engineering\Scripts\python.exe -m pip install -r requirements-dev.txt -r requirements-bim.txt -r requirements-calculation.txt
.\.venv-engineering\Scripts\python.exe -m pip check
.\.venv-engineering\Scripts\python.exe -m unittest tests.test_ifc_adapter tests.test_control_beam tests.test_engineering_tools_cli tests.test_cad_roundtrip_comparison tests.test_docling_runtime_losses -v
```

Испытано: Windows / Python3.13 / IfcOpenShell0.8.5 / PyniteFEA3.2.0 / ezdxf1.4.4 /
PyMuPDF1.26.6. Linux CI добавлен, но его PASS надо проверять на точном PR head.
Переход на latest PyMuPDF не квалифицирован:1.28.2 добавляет stdout diagnostic,
который ломает старый JSON subprocess protocol. Использовать requirements проекта.

## IFC

```powershell
$source='C:\data\model.ifc'
$sha=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
.\.venv-engineering\Scripts\python.exe scripts/engineering_tools.py ifc $source --sha256 $sha
.\.venv-engineering\Scripts\python.exe scripts/engineering_tools.py ifc-diff $source 'C:\data\revision.ifc' --sha256 $sha
```

Scope: STEP IFC2X3/IFC4/поддерживаемые IFC4X3 схемы, до50MiB/100000 entities;
report collections до1000 entries с BLOCK при превышении. Вывод — объявленные
проектные данные: структура здания, этажи, балки/колонны/стены/плиты, материалы,
psets/quantities, единицы, container и `ifc:guid:` locator вместе с source SHA.
Размеры берутся из заявленных quantities, не вычисляются по геометрии.
Данные не регистрируются автоматически в Evidence. UNKNOWN материалы не
подменяются типовыми. GUID diff ограничен целевыми элементами, не геометрией
всей модели. IfcTester/IfcClash/IfcDiff, IDS/rule evaluation и расчётная модель
не заявляются реализованными. Синтетический fixture — `tests/fixtures/bim/reference.ifc`.

## DXF

```powershell
$sha=(Get-FileHash -LiteralPath 'C:\data\before.dxf' -Algorithm SHA256).Hash.ToLowerInvariant()
.\.venv-engineering\Scripts\python.exe scripts/engineering_tools.py dxf-diff 'C:\data\before.dxf' 'C:\data\after.dxf' --sha256 $sha
```

Read-only exact serialized comparison использует существующий лимит50000 block
entities. Лимит10000 для controlled edit не повышен. Handle changes считаются
изменением/потерей, даже если изображение выглядит похожим. PASS означает только
сохранение сравниваемых DXF данных. Не подтверждает исходный DWG, converter или
физическое соответствие конструкции. Исходники не записываются.

## Контрольная балка

Создать отдельный JSON вход, записав реальные source SHA и ссылки на основания:

```json
{
  "length_m": 6.0,
  "elastic_modulus_pa": 210000000000.0,
  "inertia_m4": 0.000008,
  "area_m2": 0.003,
  "load_n_m": 1000.0,
  "source_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "evidence_ids": ["synthetic-benchmark"],
  "units": "N_m_Pa"
}
```

Значения выше — синтетический эталон, не данные объекта.

```powershell
.\.venv-engineering\Scripts\python.exe scripts/engineering_tools.py beam 'C:\data\beam-input.json'
```

Scope: одна прямая шарнирная балка с постоянными E/Iz, линейная упругость, малые
перемещения, UDL вниз, без собственного веса и сдвиговой деформации. G/nu/Iy/J —
явно обозначенные неактивные численные auxiliaries для закреплённых направлений,
не фактические свойства конструкции. Проверяются реакции, вертикальное равновесие,
поперечная сила, модуль момента и прогиб по аналитическим формулам.
Результат CALCULATED; реальная истинность входов/оснований не проверяется.
Рамы/фермы/подбор сечений/ЛИРА/SCAD не запускаются этим адаптером.

Вывод CLI — JSON, код0 для ограниченного PASS/UNCERTAINTY, код2 для BLOCK.
Ненулевой exit не удаляет оригинал. Для сохранения отчёта выбрать новый отдельный
файл, не перенаправлять stdout поверх исходного IFC/DXF/JSON.
