# EngLearn - 背单词 Agent

## 为什么做这个东西

本人正在备战考研，背单词是绕不过去的一关。

市面上大多数背单词 App 的逻辑是「看单词 → 记释义 → 重复」，本质上还是死记硬背。我个人的体会是：**真正记住一个单词，靠的是在语境中遇到它、理解它、用它做题。** 你在一篇阅读里见过 `accumulate`，比盯着它念十遍"积累、积累、积累"有效得多。

所以我的想法是：

1. 每天正常背一批单词（卡片式，快速过）
2. 背完之后，让 AI **用今天这些单词生成一篇阅读文章**
3. 再基于文章**出几道阅读理解题**，做完对答案

这样单词不是孤立地记，而是通过「背 → 读 → 做题 → 反馈」的闭环来巩固。相当于每天给自己出一套 mini 阅读练习，素材恰好就是今天要记的词。

> 这个项目基本是 vibe coding 的产物，功能还在完善中，后续会持续更新。

---

## 功能概览

- **词表选择**：内置考研核心词汇（173 词）、CET-4、CET-6 词表
- **每日背诵**：每天推送 20 个单词，卡片翻转交互，标记认识/不认识
- **间隔复习**：不熟悉的单词自动进入复习队列
- **AI 生成文章**：基于当日单词，生成 200-300 词英文短文（目标词加粗标注）
- **AI 生成题目**：3 道选择题 + 1 道简答题，附标准答案与解析
- **学习历史**：查看每日学习记录

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python / FastAPI / SQLite / SQLAlchemy |
| 前端 | Vue 3 / Vite / TailwindCSS |
| AI | LiteLLM（支持 OpenAI / DeepSeek / Ollama 等） |

---

## 使用步骤

### 环境要求

- Python 3.10+
- Node.js 18+
- 一个 LLM API（DeepSeek / OpenAI / 本地 Ollama 均可）

### 1. 克隆项目

```bash
git clone https://github.com/你的用户名/EngLearnProj.git
cd EngLearnProj
```

### 2. 启动后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置 LLM（重要！）
# 编辑 config.yaml，填入你的 API 信息（见下方配置说明）

# 启动服务
uvicorn main:app --host 127.0.0.1 --port 8001
```

看到 `Uvicorn running on http://127.0.0.1:8001` 即表示后端启动成功。

### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

看到 `Local: http://localhost:5173/` 即表示前端启动成功。

### 4. 打开浏览器

访问 **http://localhost:5173**，你会看到词表选择页面。

### 5. 开始使用

1. **选择词表** → 点击「考研核心词汇」（或其他词表）
2. **背单词** → 看单词，回忆释义，点击卡片翻转验证，标记「认识」或「不认识」
3. **完成背诵** → 20 个词过完后，页面提示学习完成
4. **生成文章** → 点击「生成阅读文章」，等待 AI 生成（约 10-30 秒）
5. **生成题目** → 文章出来后，点击「生成题目」
6. **做题对答案** → 选择/填写答案，点击「查看答案解析」

---

## LLM 配置说明

编辑 `backend/config.yaml`：

### 方式一：DeepSeek（推荐，便宜好用）

```yaml
llm:
  provider: custom
  model: deepseek-chat
  api_key: sk-你的key
  base_url: https://api.deepseek.com
```

### 方式二：OpenAI

```yaml
llm:
  provider: openai
  model: gpt-4o-mini
  api_key: sk-你的key
```

### 方式三：Ollama 本地模型（免费，无需联网）

```yaml
llm:
  provider: ollama
  model: qwen2
  base_url: http://localhost:11434
```

> 也可以通过环境变量配置：`LLM_PROVIDER`、`LLM_MODEL`、`LLM_API_KEY`、`LLM_BASE_URL`

---

## 项目结构

```
EngLearnProj/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置加载
│   ├── config.yaml          # LLM 和学习参数配置
│   ├── database.py          # 数据库
│   ├── models.py            # 数据模型
│   ├── routers/             # API 路由
│   ├── services/            # 业务逻辑（LLM调用、词表管理、文章生成）
│   └── data/                # 内置词表 JSON
├── frontend/
│   └── src/
│       ├── views/           # 页面（词表选择、背单词、文章阅读、历史）
│       ├── api/             # 接口封装
│       └── router/          # 前端路由
└── README.md
```

---

## 后续计划

- [ ] 扩充词表（完整考研 5500 词）
- [ ] 更智能的复习算法（SM-2）
- [ ] 文章难度自适应
- [ ] 生词本导出
- [ ] 移动端适配
