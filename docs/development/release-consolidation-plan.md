# №10 — единый release candidate

Основание: актуальная карта разделы 47–50, пользователь поручил продолжать локально, Windows последней. Исходный Stage9 commit 87fccbafbf6a944443e2f503acddf48f33e3b17e. Рабочая ветка integration/release-candidate-v1. Main не изменять, старые PR не закрывать до утверждённой интеграции.

1. Проверить ancestry всех PR38–68, отдельно боковой PR60 и актуальный main security baseline. Сохранить перечень heads и результат в QA.
2. Интегрировать PR60 Chromium gate и main security docs в кандидат. Не удалять старые runtime paths без доказательств ненужности. Добавить safety rules, architecture guard и release checklist. Обновить устаревший указатель/план.
3. Проверить baseline/full Python, Node, actual HTTP/jsdom, настоящий Chromium, security/architecture guards, compile, чистое воспроизводимое checkout. Один независимый review конечного diff; обязательные находки — один fixpass с regression tests.
4. Опубликовать integration candidate draft PR относительно main, дождаться CI на exact head; синхронизировать карту и Library с optimistic version guard.

Границы: это подготовка единого кандидата, не завершённый релиз/merge. №6, Windows9, production completeness13 и ACCEPTED14 остаются открыты. Windows не запускается здесь. Synthetic Chromium flows не являются живой моделью или инженерным принятием.

Ledger:
- Preflight: Stage9 includes hardening87fccba; main separately includes security docs a2a7b2d. PR60 отсутствует в Stage9 tree и требует отдельной интеграции. Core CI push filter ещё не включает integration/**.
- Task1 complete: PR38–59 и61–67 heads — ancestors Stage9. PR68 squash head имеет точно то же tree3b46cded, что Stage9; ancestry false не означает потерю hardening. PR60 включён merge35c442b. Current main включён mergeb1fc362; required core-tests file сохранён, security docs взяты из current main.
- Task2 complete: Playwright1.55.0 dev dependency теперь locked; CI Chromium и PowerShell обе сохранены; integration push filter включён. Guard boundaries RED→GREEN6tests. Rules/checklist/master plan добавлены; runtime paths не удалялись.
- Task3 local verification: baseline474PythonPASS; после guard480PythonPASS,4NodePASS,HTTP/jsdom app+DrivePASS,actual ChromiumPASS (controlled model),compile/diffPASS. CDN первый archive download оказался неполным; штатный mirror скачал Chromium/FFmpeg/headless успешно. Это загрузка dependency, не ошибка приложения.
- Final review: один read-only reviewer, Critical0/Important0/Minor3 documentation consistency. Все3 исправлены в рамках явно заданной актуализации инструкций №10: historical6/Windowsbaseline labels и redundant install. Это обратимые docs-only edits; отдельные tests, зеркалящие текст, не добавлялись. Новых deferred minors нет. Review не повторялся.
- Ruling: PR68 hardening включён squash; API tree b5a2ed9 и localStage9tree одинаковы3b46cded, ancestry false допустим. Цена ошибки — потерянное hardening; точное равенство tree исключает различие файлов этой версии. Reviewer не имел локального объекта68, parent предоставил свежую API-проверку.
- Clean checkout576059c: отдельная Python3.12venv, pinnedPyMuPDF1.26.6/Pillow12.3.0, pipcheckPASS, npmciPASS;480Python39.715sPASS, HTTPjsdom app+DrivePASS, actualChromiumPASS. После этого изменялись только docs/README/QA; production code/workflow/package lock не менялись. №10 частично выполнен; merge/main, closure stackedPR и RELEASE AUDIT ещё открыты.
