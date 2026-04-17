# 腾讯云轻量应用服务器 Docker 部署指南

## 前提条件

- 腾讯云轻量应用服务器（已安装 Docker）
- 代码已推送到 GitHub（推荐）或本地已准备好代码

## 部署步骤

### 方式一：从 GitHub 拉取部署（推荐）

1. **SSH 连接到服务器**
   ```bash
   ssh root@你的服务器IP
   ```

2. **安装 Docker Compose（如果没有）**
   ```bash
   apt-get update
   apt-get install -y docker-compose
   ```

3. **拉取代码**
   ```bash
   cd /root
   git clone https://github.com/你的用户名/htsh-ai.git
   cd htsh-ai
   ```

4. **构建并启动容器**
   ```bash
   docker-compose up -d --build
   ```

5. **验证部署**
   ```bash
   curl http://localhost:9999/health
   ```

6. **查看容器状态**
   ```bash
   docker-compose ps
   docker-compose logs -f
   ```

### 方式二：本地构建后上传

1. **在本地打包**
   ```bash
   # 在项目根目录执行
   tar --exclude='.git' --exclude='.venv' --exclude='__pycache__' \
       -czvf contract-audit.tar.gz .
   ```

2. **上传到服务器**
   ```bash
   scp contract-audit.tar.gz root@你的服务器IP:/root/
   ```

3. **在服务器解压并启动**
   ```bash
   ssh root@你的服务器IP
   cd /root
   tar -xzvf contract-audit.tar.gz
   docker-compose up -d --build
   ```

## 配置域名访问（可选）

1. **在腾讯云控制台开放端口**
   - 登录腾讯云控制台
   - 轻量应用服务器 → 防火墙
   - 添加规则：9999 端口，协议 TCP

2. **使用 Nginx 反向代理（可选）**
   ```bash
   apt-get install -y nginx
   ```

   创建 Nginx 配置 `/etc/nginx/sites-available/contract-audit`:
   ```nginx
   server {
       listen 80;
       server_name 你的域名或IP;

       location / {
           proxy_pass http://127.0.0.1:9999;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

   ```bash
   ln -s /etc/nginx/sites-available/contract-audit /etc/nginx/sites-enabled/
   nginx -t
   systemctl reload nginx
   ```

## 常用命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 重新构建
docker-compose up -d --build
```

## 注意事项

1. 数据库文件会存储在容器内，重启后会重置。如需持久化，修改 `docker-compose.yml` 添加 volume
2. 记得在腾讯云防火墙开放 9999 端口
3. 建议使用 `docker-compose` 而不是直接 `docker run`，方便管理
