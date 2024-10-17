#!/usr/bin/env bash

export PROJECT_NAME="pneumatic-frontend"
case "$MCS_RUN_ENV" in
'prod')
    export BRANCH_NAME=master
    export SERVER=app.pneumatic.app
    ;;
'staging')
    export BRANCH_NAME=dev
    export SERVER=dev.pneumatic.app
    # запускаем тесты, в случае неудачного выполнения выходим из скрипта
    bash ./tests/.run_tests.sh || exit 1
    ;;
esac

ssh -t ${SERVER} <<EOF
    cd ${PROJECT_NAME} && exec bash -l
    git fetch origin ${BRANCH_NAME}
    git reset --hard origin/${BRANCH_NAME}
    export MCS_RUN_ENV=${MCS_RUN_ENV}
    bash .build.sh
    exit
EOF
