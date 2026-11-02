# 基于用户画像的个性化AIGC海报生成系统

## 项目简介

这是一个基于用户画像的个性化AIGC（人工智能生成内容）海报生成系统，采用Django后端 + HTML/CSS/Bootstrap前端架构。

### 系统架构

```
用户登录/注册 → 输入/更新个人信息 → 构建/更新用户画像 → 用户请求生成海报
                                                          ↓
下载海报 ← 保存/下载海报 ← 是 ← 用户是否满意? ← 预览与编辑 ← 海报合成与布局优化
                                        ↓ 否
                                        反馈调整参数 ← GLM-4-Flash生成文案（免费）
                                                              ↑
                                                CogView-3-Flash / Stable Diffusion生成图像
```

## 技术栈

- **后端**: Django 4.2+
- **前端**: HTML5, CSS3, Bootstrap 5
- **数据库**: MySQL 5.7+ / MariaDB 10.3+
- **AI集成（均为免费方案，不使用收费的 GPT API）**: 
  - 智谱 GLM-4-Flash（文案生成，免费模型）
  - 智谱 CogView-3-Flash（图像生成，免费模型，默认后端）
  - 本地 Stable Diffusion WebUI（图像生成，可切换后端，本地部署免费无 Key）

## 功能模块

1. **用户管理模块**
   - 用户注册/登录
   - 个人信息管理

2. **用户画像模块**
   - 画像信息录入（年龄、性别、职业）
   - 设计偏好设置（风格、色彩、内容类型）
   - 快速画像设置
   - 画像分析报告

3. **海报生成模块**
   - 个性化提示词生成
   - AI图像生成
   - 智能文案生成
   - 海报合成与布局优化
   - 预览与编辑
   - 反馈与重新生成

4. **反馈模块**
   - 用户反馈提交
   - 系统公告

## 安装与运行

### 1. 克隆项目

```bash
cd aigc_poster_system
```

### 2. 创建虚拟环境

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置MySQL数据库

#### 4.1 安装MySQL
确保系统中已安装MySQL 5.7+ 或 MariaDB 10.3+

#### 4.2 创建数据库

```sql
CREATE DATABASE aigc_poster_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 4.3 创建数据库用户（可选）

```sql
CREATE USER 'aigc_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON aigc_poster_db.* TO 'aigc_user'@'localhost';
FLUSH PRIVILEGES;
```

### 5. 配置环境变量

复制 `.env.example` 为 `.env`，并根据实际情况配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下关键参数：

```ini
# Django密钥
SECRET_KEY=your-secret-key-here

# MySQL数据库配置
DB_NAME=aigc_poster_db
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306

# 智谱 AI API Key（免费，从 https://bigmodel.cn/ 注册获取）
ZHIPUAI_API_KEY=<redacted>

# 图像后端：zhipu（智谱免费API，默认）/ sd（本地 Stable Diffusion）
IMAGE_BACKEND=zhipu

# 本地 Stable Diffusion WebUI API地址（IMAGE_BACKEND=sd 时使用）
SD_API_URL=http://127.0.0.1:7860/sdapi/v1/txt2img

### 6. 数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. 创建超级用户

```bash
python manage.py createsuperuser
```

### 8. 收集静态文件

```bash
python manage.py collectstatic
```

### 9. 运行开发服务器

```bash
python manage.py runserver
```

访问 http://127.0.0.1:8000/ 即可使用系统。

## 使用说明

### 首次使用

1. 注册账号并登录
2. 进入"用户画像"页面，完成画像设置（或使用快速设置）
3. 点击"生成海报"，输入海报需求
4. 等待AI生成海报
5. 预览、编辑或下载海报

### 用户画像设置

- **基础信息**: 年龄、性别、职业
- **设计偏好**: 设计风格、色彩方案、内容类型
- **高级偏好**: 字体偏好、布局偏好

### 海报生成

1. 输入海报标题和描述
2. 选择内容类型和风格（可选）
3. 使用自定义提示词或让系统自动生成
4. 选择是否使用自定义文案
5. 点击"开始生成"

### 反馈机制

生成后可以对海报进行满意度评分：
- ⭐⭐⭐⭐⭐ 非常满意：保存并下载
- ⭐⭐⭐ 或以下：选择需要调整的方面，系统自动重新生成

## 项目结构

```
aigc_poster_system/
├── aigc_poster_system/     # 项目配置
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── users/                  # 用户管理应用
├── user_profile/           # 用户画像应用
├── poster_generator/       # 海报生成应用
│   └── utils/              # 工具模块
│       ├── prompt_generator.py    # 提示词生成器
│       ├── image_generator.py     # 图像生成器
│       ├── copy_generator.py      # 文案生成器
│       └── poster_composer.py     # 海报合成器
├── feedback/               # 反馈应用
├── templates/              # HTML模板
├── static/                 # 静态文件
├── media/                  # 上传文件
├── requirements.txt        # 依赖列表
└── manage.py
```

## API配置说明

系统只使用免费模型/免费方案，不使用收费的 GPT API。

### 文案生成：智谱 GLM-4-Flash（免费）

1. 在 [智谱开放平台](https://bigmodel.cn/) 注册账号并获取 API Key
2. 在 `.env` 中配置 `ZHIPUAI_API_KEY`
3. 未配置 Key 时自动使用本地模板文案降级，系统仍可演示

### 图像生成：双后端可切换

通过 `.env` 的 `IMAGE_BACKEND` 切换：

- `zhipu`（默认）：智谱 CogView-3-Flash 免费云端 API，联网即可用
- `sd`：本地 Stable Diffusion WebUI。本地启动 SD WebUI 时加 `--api` 参数，
  默认接口 `http://127.0.0.1:7860/sdapi/v1/txt2img`，可在 `.env` 的 `SD_API_URL` 修改

任一后端不可用（无 Key、服务未启动、下载失败）时，系统自动降级为
渐变占位图并提示“已使用备用结果”，不会导致生成失败。

## 系统链路（导师版总体思路）

```
用户行为数据（生成/浏览/下载/收藏/编辑/反馈落库）
  → 用户画像构建（手动偏好 + 行为聚合：生成次数、常用标签）
  → 个性化提示词生成（画像偏好 + 本次风格/色彩/语气/尺寸参数）
  → 海报生成（GLM-4-Flash 文案 + CogView / Stable Diffusion 图像 + Pillow 合成）
  → 海报质量评估（清晰度/对比度/色彩丰富度/饱和度/亮度适中度，综合分 0-100）
  → 可视化展示（画像分析图表、质量趋势、海报墙、质量明细）
```

同一主题（如“校园音乐节海报”）对不同画像用户生成不同海报：
极简/冷色/科技感用户与插画/暖色/活泼用户得到的提示词、配色和成图风格明显不同。

## 开发计划

- [x] 接入智谱 GLM-4-Flash 免费文案 API
- [x] 接入智谱 CogView-3-Flash 免费图像 API
- [x] 接入本地 Stable Diffusion WebUI（双后端切换）
- [x] 用户行为数据采集与画像动态构建
- [x] 海报质量评估与可视化展示
- [ ] 添加更多海报模板
- [ ] 实现批量生成功能
- [ ] 添加海报分享功能

