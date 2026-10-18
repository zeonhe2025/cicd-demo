# cicd-demo — Python + Docker Hub 的 GitHub Actions CI/CD 实验项目

一个极简 Flask 后端，配套一个在 **push 到 `main` 分支时自动触发** 的 GitHub Actions 工作流，完整演示 CI（构建/打包/推送镜像/导出 tar/上传 artifact/打印版本）与 CD（DEV、PROD 两个环境各自用 `suffix` 变量重打标签并列出镜像）。

> 说明：整条流水线运行在 GitHub 托管的 `ubuntu-latest` runner 上（已预装 Docker 与 Python），**本地无需安装 git/docker/python 也能跑通**。本地只在"把文件送进 GitHub 仓库"时需要 git（也可用网页上传，零安装）。

## 目录结构

```
cicd-demo/
├── .github/
│   └── workflows/
│       └── ci-cd.yml        # 核心工作流（CI + CD-DEV + CD-PROD）
├── app/
│   ├── __init__.py
│   └── main.py              # Flask 应用（/ 与 /health 两个接口）
├── requirements.txt         # 运行依赖：flask, gunicorn
├── pyproject.toml           # 打包配置（python -m build 产出 wheel + sdist）
├── Dockerfile               # 基于 python:3.12-slim，用 gunicorn 启动
├── .dockerignore
├── .gitignore
└── README.md
```

## 流水线做了什么（需求对照）

### CI 阶段（job: `ci`）
1. 打印当前所有环境变量（`env | sort`）。
2. 安装依赖（`pip install -r requirements.txt`）。
3. 编译（`python -m compileall`，Python 的字节码编译）。
4. 打包（`python -m build`，产出 `dist/*.whl` 与 `dist/*.tar.gz`）。
5. 用根目录 `Dockerfile` 构建镜像。
6. 以时间戳 `YYYYmmddHHMMSS` 作为 tag（`date +'%Y%m%d%H%M%S'`）。
7. 登录 Docker Hub：用户名取自 **Repository Variables** 的 `DOCKER_USERNAME`，密码取自 **Repository Secrets** 的 `DOCKER_PASSWORD`。
8. 推送镜像到 Docker Hub。
9. `docker save` 导出为 `image.tar`。
10. 用 `actions/upload-artifact` 上传 `image.tar`（artifact 名 `app-image`）。
11. 在 run 页面打印最终镜像版本（写入 `$GITHUB_STEP_SUMMARY`）。

### CD 阶段（job: `cd-dev` / `cd-prod`）
两个独立环境 **DEV** 与 **PROD**，各自配置一个名为 `suffix` 的环境变量。
1. 用 `actions/download-artifact` 下载上一步上传的 tar。
2. `docker load` 恢复镜像。
3. 重打标签：在原 tag 后追加该环境的 `suffix`（`...:<时间戳>-<suffix>`）。
4. `docker images` 列出并打印当前执行环境中的所有本地镜像。

## 一、前置准备

### 1. Docker Hub 账号与 Access Token
1. 打开 https://hub.docker.com/ 注册/登录（用户名必须为**小写**）。
2. 右上角头像 → **Account Settings** → **Security** → **New Access Token**。
3. 描述随意（如 `github-actions`），权限选 **Read & Write**，生成后**立即复制保存**（只显示一次）。这个 token 就是后面要用的"密码"。

### 2. GitHub 账号
确保有一个可用的 GitHub 账号，能创建仓库。

## 二、在 GitHub 上配置 Variables / Secrets / Environments

进入你的仓库页面：

### 1. Repository Variable：`DOCKER_USERNAME`
- 路径：仓库 **Settings** → **Secrets and variables** → **Actions** → 顶部切到 **Variables** 标签 → **New repository variable**
- Name: `DOCKER_USERNAME`
- Value: 你的 Docker Hub 用户名（小写）

### 2. Repository Secret：`DOCKER_PASSWORD`
- 同一页面切到 **Secrets** 标签 → **New repository secret**
- Name: `DOCKER_PASSWORD`
- Value: 上面生成的 Docker Hub Access Token

### 3. Environments：`DEV` 与 `PROD`（各带一个 `suffix` 变量）
- 路径：仓库 **Settings** → 左侧 **Environments** → **New environment**
- 新建 `DEV` → 进入后在 **Environment variables** 里 **Add variable**：Name `suffix`，Value `dev` → 保存
- 再新建 `PROD` → 同样添加变量：Name `suffix`，Value `prod` → 保存

> 环境名必须与工作流里的 `environment: name: DEV` / `PROD` **完全一致**（区分大小写）。

## 三、把项目送进 GitHub（二选一）

### 方式 A：使用 Git（推荐，标准做法）
需要先安装 [Git for Windows](https://git-scm.com/download/win)。然后在 `cicd-demo/` 目录里执行（PowerShell）：

```powershell
# 首次使用先设置身份（仅当前仓库）
git init
git config user.name  "你的名字"
git config user.email "你的邮箱"

git add .
git commit -m "init: Python CI/CD demo with GitHub Actions"

git branch -M main
# 先在 GitHub 上创建一个空仓库，再把下面 URL 换成你的仓库地址
git remote add origin https://github.com/<你的用户名>/cicd-demo.git
git push -u origin main
```

### 方式 B：GitHub 网页上传（零安装）
1. 在 GitHub 新建一个仓库（勾选 Add a README 或先建空仓）。
2. 进入仓库 → **Add file** → **Upload files**。
3. 把 `cicd-demo/` 里的所有文件拖进去。注意保留目录结构：
   - 工作流文件要放到 `.github/workflows/ci-cd.yml`。网页上传时，把文件拖入后可以在文件名前手动输入路径 `.github/workflows/`（用 `/` 会自动建目录）。
4. 提交到 `main` 分支。

> 用网页上传时，隐藏文件（`.github`、`.gitignore`、`.dockerignore`）也要一并上传，别漏掉 `.github/workflows/ci-cd.yml`，否则工作流不会触发。

## 四、触发与验证

1. 向 `main` 分支推送代码后，打开仓库的 **Actions** 标签页，应能看到一次名为 `CI-CD Pipeline` 的运行。
2. 点进这次 run，检查：
   - **CI** job：能看到打印的环境变量、依赖安装、`compileall`、`build` 产物、时间戳 tag、`docker push` 成功、生成 `image.tar`、artifact 上传，以及 Summary 里的"Final Image Version"表格。
   - run 页面下方 **Artifacts** 区能下载到 `app-image`。
   - **CD - DEV** / **CD - PROD** job：下载 artifact、`docker load`、重打标签为 `...:<时间戳>-dev` 与 `...:<时间戳>-prod`，`docker images` 列表可见。
3. 到 Docker Hub 你的仓库里，应能看到以时间戳为 tag 的镜像。

## 五、本地运行（可选，需已安装 Docker）

```powershell
docker build -t cicd-demo:local .
docker run --rm -p 8000:8000 -e APP_ENV=local cicd-demo:local
# 另开浏览器访问 http://localhost:8000/ 和 /health
```

## 六、常见问题排查

- **`denied: requested access to the resource is denied`（push 失败）**
  - 检查 `DOCKER_USERNAME` 是否为小写、是否与你 Docker Hub 用户名一致；
  - 检查 `DOCKER_PASSWORD` 用的是 **Access Token** 而不是登录密码，且 token 有 Read & Write 权限；
  - 确认镜像名里的命名空间就是你自己（`docker.io/<你的用户名>/cicd-demo`）。
- **工作流没触发**：确认文件路径是 `.github/workflows/ci-cd.yml`，且推送的分支是 `main`。
- **CD 里 `vars.suffix` 为空**：确认在 Settings → Environments 里给 `DEV`/`PROD` 各自加了名为 `suffix` 的变量，且环境名大小写一致。
- **`python -m build` 报错找不到 README**：确认仓库根目录存在 `README.md`（本文件）。
