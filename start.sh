#!/usr/bin/env bash
# start.sh

export FLASK_ENV=development #production
export FLASK_APP=app #manage
export APP_CONFIG=config.DevelopmentConfig
export FLASK_RUN_PORT=8080
flask run -h 0.0.0.0
