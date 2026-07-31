# EngLearn 项目详解（初学者版）

本文档详细解释项目的每一个文件、每一层架构的工作原理。适合没有 Web 开发经验的同学阅读。

---

## 一、整体架构：前后端分离

```
┌─────────────────────────────────────────────────────┐
│  你的浏览器                                          │
│  ┌───────────────────────────────────────────────┐  │
│  │  前端 (Vue 3)                                  │  │
│  │  - 负责：页面长什么样、按钮点了干什么            │  │
│  │  - 端口：5173                                  │  │
│  └───────────────────────┬───────────────────────┘  │
└──────────────────────────┼──────────────────────────┘
                           │ HTTP 请求 (JSON 数据)
                           ▼
┌──────────────────────────────────────────────────────┐
│  后端 (FastAPI / Python)                              │
│  - 负责：业务逻辑、存取数据、调用 AI                   │
│  - 端口：8001                                        │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐  │
│  │  SQLite DB │  │  词表 JSON │  │  DeepSeek AI │  │
│  └────────────┘  └────────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────┘
```

**通俗理解**：
- **前端** = 餐厅的服务员和菜单（顾客看到和交互的部分）
- **后端** = 厨房（处理订单、做菜、管理食材）
- **数据库** = 冰箱（存储食材/数据）
- **AI (DeepSeek)** = 外请的大厨（帮忙做特色菜/生成文章）

---

## 二、后端文件详解

### 目录结构

```
backend/
├── main.py              ← 程序入口，启动整个后端
├── config.py            ← 读取配置
├── config.yaml          ← 配置文件（AI密钥、学习参数）
├── database.py          ← 数据库连接
├── models.py            ← 数据表定义
├── routers/             ← API 接口（接收前端请求）
│   ├── words.py         ← 词表相关接口
│   ├── study.py         ← 学习进度接口
│   └── generate.py      ← AI生成接口
├── services/            ← 业务逻辑（真正干活的代码）
│   ├── llm_service.py   ← 调用 AI 的封装
│   ├── word_service.py  ← 单词管理逻辑
│   └── generate_service.py ← 文章/题目生成逻辑
└── data/                ← 词表数据文件
    ├── kaoyan.json
    ├── vocabulary.json
    ├── cet4.json
    └── cet6.json
```

---

### 2.1 `main.py` — 程序入口

```python
# 这是整个后端的"总开关"
# 运行 uvicorn main:app 时，Python 会加载这个文件
```

**它做了三件事：**

1. **创建 FastAPI 应用**：相当于开一家店
2. **注册路由**：告诉系统"什么请求由谁处理"
3. **启动时初始化**：开店前先装修（建数据库表、导入词表）

**关键概念 — 什么是 API？**

API (Application Programming Interface) 就是"约定好的网址"。比如：
- 访问 `http://127.0.0.1:8001/api/wordlists` → 返回所有词表
- 访问 `http://127.0.0.1:8001/api/study/today?word_list_id=1&count=10` → 返回10个单词

前端通过访问这些网址来获取数据，就像你在浏览器输入网址访问网页一样。

**关键概念 — 什么是 CORS？**

浏览器有安全限制：`localhost:5173`（前端）不能直接请求 `localhost:8001`（后端），因为端口不同算"跨域"。CORS 配置就是告诉浏览器："允许 5173 来访问我"。

---

### 2.2 `config.py` + `config.yaml` — 配置管理

`config.yaml` 是给你（用户）看的配置文件：

```yaml
llm:
  provider: custom          # 用哪种AI服务
  model: deepseek-v4-pro    # 模型名称
  api_key: null             # 密钥（通过环境变量设置，不写在这里）
  base_url: https://api.deepseek.com
```

`config.py` 是程序读取配置的代码。它的优先级逻辑：

```
环境变量 > config.yaml > 代码默认值
```

**为什么这样设计？**
- 密钥等敏感信息放环境变量（不会提交到 GitHub）
- 不敏感的配置放 yaml（方便修改）
- 代码里有默认值（即使什么都没配也能跑）

---

### 2.3 `database.py` — 数据库连接

```python
engine = create_async_engine(settings.database_url)  # 创建数据库引擎
async_session = async_sessionmaker(engine)            # 创建会话工厂
```

**通俗理解**：
- `engine` = 通往数据库的"管道"
- `session` = 一次"对话"，通过它来查询/保存数据
- 用的是 SQLite（一个文件就是整个数据库，不需要安装数据库软件）

**关键概念 — 什么是 async（异步）？**

普通代码：做A → 等A完成 → 做B（串行，慢）
异步代码：做A → 不等，先做B → A好了再处理（并行，快）

Web 服务器需要同时处理很多请求，异步能让它在等待数据库/AI响应时去服务其他用户。

---

### 2.4 `models.py` — 数据表定义

这个文件定义了数据库里有哪些"表格"：

| 表名 | 作用 | 关键字段 |
|------|------|----------|
| `WordList` | 词表 | name, word_count, target |
| `Word` | 单词 | word, phonetic, meaning, example |
| `StudyRecord` | 学习记录 | study_date, word_ids, status |
| `WordProgress` | 单词进度 | familiarity(0-5), next_review_date |
| `GeneratedContent` | AI生成内容 | article, questions |

**通俗理解**：就像 Excel 表格一样，每个表有列（字段）和行（记录）。

**关键概念 — ORM 是什么？**

ORM (Object-Relational Mapping) 让你用 Python 类来操作数据库，而不用写 SQL：

```python
# 不用 ORM（写原始SQL）：
# SELECT * FROM words WHERE word_list_id = 1

# 用 ORM（写Python）：
result = await db.execute(select(Word).where(Word.word_list_id == 1))
```

---

### 2.5 `routers/` — API 接口层

路由 = "前台接待"，负责：
1. 接收前端的 HTTP 请求
2. 验证参数是否合法
3. 调用 service 层干活
4. 把结果返回给前端

#### `routers/words.py`

| 接口 | 方法 | 作用 |
|------|------|------|
| `/api/wordlists` | GET | 获取所有词表列表 |
| `/api/wordlists/{name}/words` | GET | 分页获取某个词表的单词 |

#### `routers/study.py`

| 接口 | 方法 | 作用 |
|------|------|------|
| `/api/study/today?word_list_id=1&count=10` | GET | 获取学习单词（count=0仅查询） |
| `/api/study/mark` | POST | 标记单词认识/不认识 |
| `/api/study/complete` | POST | 完成本轮学习 |
| `/api/study/history` | GET | 查看学习历史 |

#### `routers/generate.py`

| 接口 | 方法 | 作用 |
|------|------|------|
| `/api/generate/article` | POST | AI生成文章 |
| `/api/generate/questions` | POST | AI生成题目 |
| `/api/generate/content/{id}` | GET | 获取已生成的内容 |

**关键概念 — GET vs POST**

- **GET**：获取数据（像查看菜单）→ 参数放在网址里
- **POST**：提交数据（像下单）→ 参数放在请求体里

---

### 2.6 `services/` — 业务逻辑层

这是"真正干活"的代码。Router 只是接单，Service 才是做菜。

#### `services/word_service.py`

核心函数：

```python
async def init_word_lists(db):
    """启动时：扫描 data/ 目录，把所有 JSON 文件导入数据库"""
    # 自动发现 → 你往 data/ 丢一个新 JSON，重启就能用

async def get_today_study_words(db, word_list_id, count):
    """创建学习会话：挑选单词"""
    # 1. 先选需要复习的（之前标记不认识的）
    # 2. 再补新单词（按顺序从未学过的里取）
    # 3. 凑够 count 个

async def mark_word_progress(db, word_id, word_list_id, known):
    """标记单词：更新熟悉度，计算下次复习时间"""
    # 认识 → 熟悉度+1 → 下次间隔更长
    # 不认识 → 熟悉度-1 → 下次间隔更短
```

**间隔复习算法**：

```
熟悉度 0 → 1天后复习
熟悉度 1 → 3天后
熟悉度 2 → 7天后
熟悉度 3 → 14天后
熟悉度 4 → 30天后
熟悉度 5 → 不再推送（毕业了）
```

#### `services/llm_service.py`

```python
async def chat_completion(messages, temperature, max_tokens):
    """统一的 AI 调用接口"""
    # 用 LiteLLM 库，一套代码兼容 OpenAI/DeepSeek/Ollama
    # 你只需要改 config.yaml 就能换 AI 提供商
```

**关键概念 — 什么是 LiteLLM？**

不同 AI 公司的接口格式略有不同。LiteLLM 是一个"翻译器"，让你用统一的代码调用任何 AI：

```python
# 不管底层是 DeepSeek 还是 OpenAI，代码都一样：
response = await litellm.acompletion(model="...", messages=[...])
```

#### `services/generate_service.py`

```python
async def generate_article(words, target):
    """生成文章：把单词列表 + 目标考试 拼成 Prompt 发给 AI"""

async def generate_questions(article, target):
    """生成题目：把文章发给 AI，要求返回 JSON 格式的题目"""
```

**关键概念 — 什么是 Prompt？**

Prompt 就是你给 AI 的"指令"。这个项目里：

```
System Prompt（角色设定）:
  "你是英语教学专家，请生成200-300词短文，融入以下单词..."

User Message（具体任务）:
  "目标考试: 考研\n单词: abandon, abstract, accommodate..."
```

AI 收到后会按照指令生成文章。Prompt 写得好不好，直接决定生成质量。

---

### 2.7 `data/` — 词表数据

JSON 格式，每个单词一条记录：

```json
{
  "word": "abandon",
  "phonetic": "/əˈbændən/",
  "meaning": "v. 放弃，抛弃",
  "example": "He abandoned his plan."
}
```

**如何添加新词表？**
1. 在 `data/` 下创建 `mywords.json`
2. 按上面的格式填入单词
3. 重启后端 → 自动识别并加载

---

## 三、前端文件详解

### 目录结构

```
frontend/
├── index.html           ← HTML 入口（浏览器加载的第一个文件）
├── package.json         ← 依赖清单（相当于 Python 的 requirements.txt）
├── vite.config.js       ← 开发服务器配置（端口、代理）
├── tailwind.config.js   ← CSS 框架配置
├── postcss.config.js    ← CSS 处理配置
└── src/
    ├── main.js          ← JS 入口（创建 Vue 应用）
    ├── App.vue          ← 根组件（导航栏 + 页面容器）
    ├── style.css        ← 全局样式
    ├── router/index.js  ← 页面路由（URL → 组件的映射）
    ├── api/index.js     ← API 请求封装
    └── views/           ← 四个页面
        ├── WordListView.vue   ← 词表选择页
        ├── StudyView.vue      ← 背单词页
        ├── ArticleView.vue    ← 文章+题目页
        └── HistoryView.vue    ← 学习历史页
```

---

### 3.1 `vite.config.js` — 开发服务器

```javascript
server: {
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8001',  // 转发到后端
    },
  },
}
```

**关键概念 — 什么是代理（Proxy）？**

前端在 5173 端口，后端在 8001 端口。浏览器有跨域限制。
代理的作用：前端请求 `/api/xxx` → Vite 自动转发到 `127.0.0.1:8001/api/xxx`。
对浏览器来说，请求始终发给 5173，不存在跨域。

---

### 3.2 `src/router/index.js` — 页面路由

```javascript
'/'              → WordListView.vue   (词表选择)
'/study/:id'     → StudyView.vue      (背单词)
'/article/:id'   → ArticleView.vue    (文章题目)
'/history/:id'   → HistoryView.vue    (学习历史)
```

**通俗理解**：就像网站的"导航地图"，决定输入什么网址显示什么页面。
`:id` 是动态参数，比如 `/study/4` 表示学习 id=4 的词表。

---

### 3.3 `src/api/index.js` — 请求封装

```javascript
export const getTodayWords = (wordListId, count = 0) =>
  api.get('/study/today', { params: { word_list_id: wordListId, count } })
```

把"发 HTTP 请求"封装成简单的函数调用。页面里只需要：

```javascript
const res = await getTodayWords(4, 10)  // 获取词表4的10个单词
console.log(res.data.words)              // 拿到数据
```

---

### 3.4 `.vue` 文件 — Vue 组件

每个 `.vue` 文件由三部分组成：

```vue
<template>
  <!-- HTML：页面长什么样 -->
</template>

<script setup>
// JavaScript：页面怎么动（逻辑）
</script>

<style>
/* CSS：页面怎么好看（样式）—— 本项目用 TailwindCSS 代替 */
</style>
```

#### `StudyView.vue`（最核心的页面）

**交互流程**：

```
进入页面 → 显示"本次学多少个？"
    ↓ 用户输入数量，点击"开始学习"
调用 API 获取单词 → 显示第一个单词卡片
    ↓ 用户点击卡片
翻转显示释义 → 用户点"认识"或"不认识"
    ↓ 调用 API 记录结果
显示下一个单词... 循环
    ↓ 全部完成
显示"本轮学习完成！" → 可选"生成文章"或"继续学习"
```

**关键概念 — ref（响应式变量）**：

```javascript
const flipped = ref(false)  // 卡片是否翻转

// 当 flipped 的值改变时，页面会自动更新
flipped.value = true  // 页面立刻显示释义
```

Vue 的核心思想：**数据变了 → 页面自动跟着变**，你不用手动操作 DOM。

---

## 四、完整数据流教程

### 场景：用户背完单词后生成文章

```
第1步 [前端] 用户点击"生成阅读文章"按钮
       ↓
第2步 [前端] ArticleView.vue 调用 generateArticle(recordId)
       ↓
第3步 [网络] 发送 POST 请求到 /api/generate/article
       请求体: {"study_record_id": 1}
       ↓
第4步 [后端] routers/generate.py 接收请求
       - 从数据库查出学习记录（包含哪些单词）
       - 查出词表的目标考试（考研/四六级）
       ↓
第5步 [后端] services/generate_service.py 构造 Prompt
       System: "你是英语教学专家..."
       User: "请融入以下单词: abandon, abstract..."
       ↓
第6步 [后端] services/llm_service.py 调用 DeepSeek API
       发送请求到 https://api.deepseek.com
       ↓
第7步 [AI]   DeepSeek 生成文章，返回文本
       ↓
第8步 [后端] 把文章存入数据库（generated_contents 表）
       返回 JSON: {"article": "In modern society..."}
       ↓
第9步 [前端] 收到响应，把文章渲染到页面上
       **加粗** 的单词会被高亮显示
```

---

## 五、如何修改和扩展

### 想改每日默认学习数量？

编辑 `backend/config.yaml`：
```yaml
study:
  daily_word_count: 30  # 改成30
```

### 想添加新词表？

在 `backend/data/` 下新建 `ielts.json`：
```json
[
  {"word": "environment", "phonetic": "/ɪnˈvaɪrənmənt/", "meaning": "n. 环境", "example": "..."}
]
```
重启后端即可。

### 想改 AI 生成的文章风格？

编辑 `backend/services/generate_service.py` 里的 `ARTICLE_SYSTEM_PROMPT`。
这就是 Prompt 工程——改指令就能改 AI 的输出。

### 想换 AI 模型？

编辑 `backend/config.yaml`：
```yaml
llm:
  provider: ollama
  model: qwen2
  base_url: http://localhost:11434
```

---

## 六、技术名词速查表

| 名词 | 解释 |
|------|------|
| FastAPI | Python 的 Web 框架，用来写 API |
| Vue 3 | JavaScript 的前端框架，用来做网页 |
| Vite | 前端开发工具，提供热更新 |
| TailwindCSS | CSS 工具类框架，用 class 名直接写样式 |
| SQLite | 轻量数据库，一个文件就是整个库 |
| SQLAlchemy | Python ORM，用代码操作数据库 |
| LiteLLM | AI 调用统一接口库 |
| axios | 前端发 HTTP 请求的库 |
| JSON | 数据交换格式，前后端通信的"语言" |
| HTTP | 网络协议，浏览器和服务器之间的通信规则 |
| REST API | 一种 API 设计风格：用 URL 表示资源，用方法表示操作 |
| Prompt | 给 AI 的指令文本 |
| CORS | 浏览器的跨域安全策略 |
| npm | JavaScript 的包管理器（类似 pip） |
| uvicorn | Python 的 ASGI 服务器（运行 FastAPI 用的） |

---

## 七、本地运行命令

```bash
# 后端
cd backend
pip install -r requirements.txt
# 设置环境变量（Windows PowerShell）
$env:LLM_API_KEY = 'sk-你的key'
# 启动
python -m uvicorn main:app --host 127.0.0.1 --port 8001

# 前端（新开一个终端）
cd frontend
npm install
npm run dev
```

打开浏览器访问 `http://localhost:5173` 即可使用。
