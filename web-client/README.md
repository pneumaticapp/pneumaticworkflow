# Pneumatic frontend

##### Launch commands:
* `npm ci`
* `npm local`

##### The prod version can be launched by any one of the following three commands:
* `npm ci && npm start:prod`
* `pm2 start pm2.json`
* `bash .build.sh` (через докер)

##### The command to launc tests is as follows:
* `npm t`

##### Config:
* The configuration is divided into`common.json`, `dev.json` and `prod.json`
* `dev` and `prod` are used for the `staging` and `prod` environments
* everything defined in `dev` and `prod` redefines the `common` configuration that is used for local development
