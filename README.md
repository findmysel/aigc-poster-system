# 基于用户画像的个性化AIGC海报生成系统

## 项目简介

这是一个基于用户画像的个性化AIGC（人工智能生成内容）海报生成系统，采用Django后端 + HTML/CSS/Bootstrap前端架构。

### 系统架构

```
用户登录/注册 → 输入/更新个人信息 → 构建/更新用户画像 → 用户请求生成海报
                                                          ↓
下载海报 ← 保存/下载海报 ← 是 ← 用户是否满意? ← 预览与编辑 ← 海报合成与布局优化
                                        ↓ 否
                                        反馈调整参数 ← GPT-4o-mini生成文案
                                                              ↑
                                                Stable Diffusion XL生成图像
```

## 技术栈

- **后端**: Django 4.2+
- **前端**: HTML5, CSS3, Bootstrap 5
- **数据库**: MySQL 5.7+ / MariaDB 10.3+
- **AI集成**: 
  - Stable Diffusion XL（图像生成）
  - GPT-4o-mini（文案生成）

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

# OpenAI API密钥（用于GPT-4o-mini）
OPENAI_API_KEY=your-openai-api-key

# Stable Diffusion API地址
SD_API_URL=http://localhost:7860/sdapi/v1/txt2img

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

### Stable Diffusion XL

系统默认使用模拟图像生成器，如需连接真实的SD服务：

1. 部署本地或云端Stable Diffusion服务
2. 在 `.env` 中配置 `SD_API_URL`
3. 修改 `poster_generator/utils/image_generator.py` 使用真实API

### GPT-4o-mini

1. 在 [OpenAI](https://openai.com/) 注册账号并获取API密钥
2. 在 `.env` 中配置 `OPENAI_API_KEY`
3. 文案生成功式将自动调用API

## 开发计划

- [ ] 接入真实Stable Diffusion API
- [ ] 接入真实GPT-4o-mini API
- [ ] 添加更多海报模板
- [ ] 实现批量生成功能
- [ ] 添加海报分享功能
- [ ] 实现用户画像智能学习

