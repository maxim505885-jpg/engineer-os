# Импорт оригиналов Drive в локальный кабинет

В панели «Google Drive» указать ссылку на файл или его ID. Необязательный
ожидаемый SHA256 позволяет сверить конкретный оригинал. Импортированный файл
сохраняется в текущий диалог и выбирается для последующего CORE_PLAN/CORE_RUN.
Ручная загрузка продолжает работать без Google.

## Настройка и доверие

Локальный сервер читает GOOGLE_DRIVE_CLIENT_ID и GOOGLE_DRIVE_REFRESH_TOKEN
из окружения при запуске; GOOGLE_DRIVE_CLIENT_SECRET необязателен. Используется
существующий GoogleDriveTokenProvider/GoogleDriveClient. OAuth должен заранее
дать read-only доступ к нужному файлу. Интерактивное подключение аккаунта,
выдача consent и получение refresh token этим изменением не реализованы.
Секреты не вводятся в веб-форму и не сохраняются в SQLite, provenance или UI.
Не коммитить значения переменных в репозиторий.

Наличие конфигурации не подтверждает соединение: статус всегда сообщает
connection_verified=false, реальный доступ проверяется только при импорте.
Нельзя обещать доступ ко всем файлам аккаунта. Файлы, которым нужен отдельный
resource key, пока могут потребовать ручной загрузки.

## Контракт

- Только оригиналы PDF/TXT/MD, 1 байт–100 MiB, не Google-native документы,
  папки или рекурсивная синхронизация. До 200 файлов в диалоге, две загрузки
  одновременно. API защищён существующими loopback Host/Origin/token checks.
- Принимаются raw ID и HTTPS drive.google.com/file/d/ID/view или /open?id=ID.
  Пользовательский URL не загружается. Транспорт обращается только к фиксированным
  HTTPS OAuth/Drive endpoints; redirects и environment proxy отключены.
  Ответ OAuth/metadata ограничен 1 MiB, оригинал скачивается потоково с лимитом.
- До, во время и после скачивания сверяются ID/name/mime/size/MD5/modifiedTime;
  нужны явные boolean canDownload=true и trashed=false. Несовпадение снимков,
  MD5, размера или ожидаемого SHA256 прекращает импорт без регистрации файла.
- После успешной очистки временного каталога оригинал передаётся существующему
  preserve_file. Ошибка parser сохраняет исходные байты с недоступным извлечением,
  как при ручной загрузке. Повторные импорты создают отдельные локальные записи.
- В provenance: Drive ID, имя, MIME, modifiedTime, MD5, recomputed SHA256,
  ожидаемый SHA256 и время импорта. Scope SOURCE_IDENTITY_ONLY. Сохранённая копия
  не обновляется автоматически при изменении облачного файла.

Проверка checksum относится к идентичности байтов. Исходники остаются UNVERIFIED,
NOT_EVIDENCE, acceptance=false; смысл, полнота, инженерное принятие и FINAL AUDIT
этим импортом не проверяются. Модель не получает OAuth или инструмент импорта.

Официальный контракт Google: [скачивание оригиналов](https://developers.google.com/workspace/drive/api/guides/manage-downloads)
и [метаданные Files](https://developers.google.com/workspace/drive/api/reference/rest/v3/files).
Google Docs требуют отдельного export workflow; он сейчас отсутствует.

## Проверка

Unit и actual loopback HTTP используют существующий GoogleDriveClient с
синтетическим opener: сохранность байтов/restart, source change, MD5/SHA mismatch,
неверные права/типы/форматы/размер, session isolation, token, shared upload limit,
legacy SQLite migration и cleanup failure. Последние две ошибки воспроизведены
RED→GREEN. e2e/local_drive_dom_smoke.cjs проверяет реальную локальную HTTP-службу
через jsdom: submit, selected file, provenance reload, draft/session isolation,
checksum failure без ложного файла. Тестовый транспорт находится только в тесте.

Live Google OAuth/Drive, реальный браузер layout/CSP, Windows и настоящая qwen3
NOT_RUN. Windows остаётся последним этапом по указанию пользователя.
