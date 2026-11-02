#!/bin/bash
# Codespaces / 在线演示一键启动：迁移 -> 种子数据 -> 启动服务（8000 端口）
# 本地演示同样可用：bash scripts/run_codespace.sh
set -e
cd "$(dirname "$0")/.."

export DB_ENGINE=django.db.backends.sqlite3
export DB_NAME="$PWD/.demo-data/demo.db"
export SECRET_KEY="${SECRET_KEY:-demo-key}"
export ALLOWED_HOSTS='*'
export IMAGE_BACKEND="${IMAGE_BACKEND:-zhipu}"
# Codespaces 转发域名为 https://*.app.github.dev，需声明 CSRF 可信来源
if [ -n "$CODESPACE_NAME" ]; then
  export CSRF_TRUSTED_ORIGINS="https://${CODESPACE_NAME}-8000.app.github.dev"
fi

mkdir -p .demo-data logs
python manage.py migrate --run-syncdb -v 0
python scripts/seed_demo.py
echo "演示账号：demo / Demo@12345"
exec python manage.py runserver 0.0.0.0:8000
