#!/bin/sh
set -eu

mode=${1:-deploy}
case "$mode" in deploy|update) ;; *) echo "用法: sh mes.sh deploy|update" >&2; exit 1;; esac
for tool in docker curl od tr; do
  command -v "$tool" >/dev/null 2>&1 || { echo "请先安装 $tool。" >&2; exit 1; }
done
docker compose version >/dev/null 2>&1 || { echo "请先安装 Docker Compose 插件。" >&2; exit 1; }
docker info >/dev/null 2>&1 || { echo "无法访问 Docker，请启动 Docker 并使用有权限的账号运行。" >&2; exit 1; }

install_dir=${MES_DIR:-/opt/free-mes}
base_url=https://raw.githubusercontent.com/zxgad3wdasaq1e-ai/free-mes/v1.0.0/deploy
if [ "$mode" = update ] && [ ! -f "$install_dir/.env" ]; then
  echo "未找到已有部署，请先运行部署命令。" >&2; exit 1
fi
mkdir -p "$install_dir"
cd "$install_dir"
umask 077
if [ ! -f .env ]; then
  db_password=$(od -An -N24 -tx1 /dev/urandom | tr -d ' \n')
  printf 'DB_PASSWORD=%s\nMES_PORT=%s\n' "$db_password" "${MES_PORT:-1111}" > .env
elif grep -qx 'MES_PORT=8080' .env; then
  # Migrate the previous default while keeping explicitly customized ports.
  sed 's/^MES_PORT=8080$/MES_PORT=1111/' .env > .env.new
  mv .env.new .env
fi
curl -fsSL "$base_url/compose.yml" -o compose.yml.new
mv compose.yml.new compose.yml
docker compose pull
docker compose up -d --remove-orphans
printf '\n服务已启动。访问服务器的 %s 端口；首次初始化可能需要几分钟。\n' "$(sed -n 's/^MES_PORT=//p' .env)"
echo "数据保存在 Docker 卷中。查看状态：docker compose -f $install_dir/compose.yml --env-file $install_dir/.env ps"
