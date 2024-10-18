# Pneumatic frontend

##### To run:

* `npm ci`
* `npm local`

##### The production version can be run with any of the following three commands:

* `npm ci && npm start:prod`
* `pm2 start pm2.json`
* `bash .build.sh` (using docker)

##### Running tests:

* `npm t`


##### Config:

* Configuration is in three files `common.json`, `dev.json` and `prod.json`
* `dev` and `prod` are used for the `staging` and `prod`environments
* Everything defined in`dev` and `prod` redefines the`common`config, which is used for local development
