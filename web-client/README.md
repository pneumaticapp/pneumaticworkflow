# Pneumatic frontend

##### Для запуска:
* `npm ci`
* `npm local`

##### Для запуска prod версии любой из 3 вариантов:
* `npm ci && npm start:prod`
* `pm2 start pm2.json`
* `bash .build.sh` (через докер)

##### Запуск тестов:
* `npm t`

##### Config:
* Конфиг разделен на `common.json`, `dev.json` и `prod.json`
* `dev` и `prod` используются для окружений `staging` и `prod`
* всё, что определено в `dev` и `prod` переопределяет конфиг `common`, который используется для локальной разработки
