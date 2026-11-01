# MES 部署

服务器需要 Linux x86-64、Docker 和 Docker Compose 插件，并能够访问 GitHub 和 GitHub Container Registry。首次部署前，请确认 GitHub Actions 的镜像构建已成功，且三个镜像包允许服务器拉取（匿名拉取需要将包设为 Public）。

部署：

```sh
curl -fsSL https://raw.githubusercontent.com/zxgad3wdasaq1e-ai/free-mes/v1.0.0/deploy/mes.sh | sh -s -- deploy
```

更新：

```sh
curl -fsSL https://raw.githubusercontent.com/zxgad3wdasaq1e-ai/free-mes/v1.0.0/deploy/mes.sh | sh -s -- update
```

部署完成后访问 `http://服务器IP:1111`。首次初始化需要几分钟。默认租户为 `MES`，管理员用户名为 `admin`，初始密码为 `111111`；登录后请立即修改密码。确保服务器防火墙和云服务商安全组放行 1111 端口。

部署文件位于 `/opt/free-mes`，数据库、Redis 和上传文件存放在 Docker 卷中。更新会保留这些数据，不会重新导入初始化数据库；更新前请先备份数据。更新时原默认端口 8080 会自动改为 1111，其他自定义端口保持不变。首次部署时可执行 `export MES_PORT=端口号` 指定其他端口。

查看服务状态和日志：

```sh
cd /opt/free-mes && docker compose ps
cd /opt/free-mes && docker compose logs -f --tail=100
```

首次安装会生成数据库密码并保存在 `/opt/free-mes/.env`。请妥善保管该文件。项目许可证见 [LICENSE](LICENSE)。
