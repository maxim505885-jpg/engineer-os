# Проход по19 пунктам — 09.10.2026

Основание: объединённое дерево31ec638bbb7359a373cb92b786bc9b7f2a706bdc. Рабочая ветка feat/master-plan-completion-20261009. Статусы master-plan.md обновлены по программному объёму; история сохранена.

## Изменения

- Покрытие источника в черновике: пересчёт из полного журнала страниц/частей, пропуски/ошибки/ограничения, digest и отказ устаревшего экспорта.
- Три шаблона, до3 иллюстраций из исходной страницы; та же PNG в DOCX/PDF, captions на странице изображения, лимиты1600px/1MiB на изображение/2MiB суммарно. Экспорт повторно проверяет оригинал, выбранную страницу и asset. Только черновик.
- Подтверждённая память: текущий принятый signed audit, точные основания, HMAC scope/origin существующим issuer key, версии/отзыв/удаление/export/backup, mandatory re-verification.1000 продвижений/3000 метаданных; повреждённый источник не мешает другому проекту.
- DXF: оригинал/инвентаризация/locator/отдельная аннотация/diff/export/backup. Независимая проверка ресурсов/semantic headers/geometry и полного канонического содержимого добавленной аннотации. DWG сохранён, конвертер отсутствует — BLOCK. Реального пользовательского CAD файла нет.
- Shared model gateway: parsed hostname, запрет redirect, bounded reply, незавершённые ответы отклоняются; legacy absent finish_reason поддерживается явно, не доказательство полноценного provider receipt.
- Windows smoke: точное имя модели, STARTUP_ONLY/observed_platform; inference_verified=false,physical_windows_verified=false.
- DB/SQLite sidecars/lock/settings/key/migration: symlink/hardlink/broken/nonregular внутренние файлы отклоняются. Lock no-follow/inode checks. Arbitrary owner-selected directory aliases работают. Конкурентная подмена файлов владельцем не объявлена устранённой.
- HTTP и UI: текущий session/token, изоляция, memory acceptance gate, CAD locator/annotation/export, шаблон/иллюстрация; один локальный бесплатный DXF dependency установлен общим launcher requirements.

## Проверки локального замороженного кода

- `ENGINEER_OS_ATTACHMENT_PARSER=native ENGINEER_OS_TESSDATA_DIR=... python3 -m unittest discover -s tests -p test_*.py`:726 тестов,0 failed,0 skipped,104.283s.
- Node dashboard:4 PASS; HTTP/DOM app+Drive:2 сценария PASS.
- Real Chromium: основной кабинет/recovery; document intake; черновик/template/illustration/DOCX/PDF; CAD locator/annotation download/мобильный экран/session isolation/blocked memory —4 сценария PASS. Последний CAD мобильный сценарий отдельно повторён после окончательного verifier fix; без acceptance.
- Architecture/repository guards,compileall,JavaScript syntax,diff-check,pip check:PASS.
- Независимое ревью: три Important исправлены. Свежий итоговый focused прогон45 PASS, normal CAD PASS/altered Z BLOCK. Оставшихся подтверждённых Critical/Important в рассмотренном коде нет.
- Исторические промежуточные прогоны с4 OCR skips/HTTP timeout/устаревшим DWG-exclusion assertion не заменяют этот итог. OCR rus+eng были включены; HTTP regression отдельно воспроизведён и прошёл с native parser. DWG сохранение теперь явный поддержанный intake с BLOCK чтения.

## Реальные источники — только чтение копий

На копии V4 SHA256 b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916 обработаны534/534 native-страницы,0 missing,0 failed,534 BLOCK;40 страниц без native текста,491 страница с изображениями,534 с vector paths. Два нормативных PDF:82/82 и20/20 страниц обработаны, также BLOCK. Это полный журнал наблюдений извлечения, не доказательство полноты таблиц/графики. Исходные файлы/БД не изменялись и не помещались в Git.

## Границы и оставшиеся критерии

6 программных критериев выполнены,10 частично готовы,3 открыты (13,14,19). №15/17 переведены в частичный программный маршрут, реальный положительный сценарий открыт. №16 принятый выпуск открыт. Solver/актуальные нормы, физический Windows, реальное ACCEPTED принятие и release/main/tag отсутствуют.

CodeQL на прежнем31ec638:27 high (26 path-injection из authenticated recovery owner-selected absolute paths,1 cleartext sink settings.json). Уточнённый flow последнего ведёт из legacy non_secret_config в allowlisted settings, а не из issuer key. Реальные внутренние leaf-link баги воспроизведены/исправлены. Открытые alert статусы не подавлены/не dismissed; свежий CI/scan и точная оценка публикуемой версии добавляются после push. До этого main/официальный кандидат не объявлены обновлёнными.

## Final remote result on published head90263af

**Свежий remote CI на head90263af:** Core push37865047057 и PR37865050847 SUCCESS; Security push37865047088 и PR37865050930 SUCCESS. CodeQL dynamic workflow37865047455 SUCCESS означает успешное выполнение анализа; итоговый CodeQL check113609776255 FAILURE:29 открытых high alerts (28 py/path-injection,1 py/clear-text-storage-sensitive-data). Ref refs/pull/91/head, все29 most_recent_instance.commit_sha совпадают с90263af. Предупреждения не подавлены и не dismissed; clean security не заявляется. PR91 ready/open,не merged; перенос в кандидат остаётся открыт до документированного security triage.

Follow-up security review:34 focused tests PASS and real HTTP missing-token/bad-Host/bad-Origin/cross-site POSTs403 without archive creation. Alerts34/35 are lstat/resolve protections over intentional owner paths; blanket all29 dismissal is not justified without per-flow triage. Pre-open TOCTOU/Windows ACL remain outside the proven guarantee. Release remains blocked.
