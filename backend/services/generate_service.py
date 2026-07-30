"""文章与题目生成服务"""
import json

from services.llm_service import chat_completion


ARTICLE_SYSTEM_PROMPT = """你是一位英语教学专家，擅长编写英语阅读理解文章。
请根据用户提供的单词列表，生成一篇英文短文。

要求：
1. 文章长度 200-300 词
2. 自然融入所有给定单词，使用 **加粗** 标注这些单词
3. 文章难度匹配目标考试水平
4. 主题贴近考试常见话题（社会、科技、教育、环境、经济等）
5. 文章结构完整，有引入、展开、总结
6. 在文章末尾列出所有加粗单词的中文释义

请只输出文章内容，不要输出其他解释。"""

QUESTIONS_SYSTEM_PROMPT = """你是一位英语考试出题专家。
请根据给定的英文文章，生成阅读理解题目。

要求：
1. 生成 3 道选择题（每题 4 个选项 A/B/C/D）和 1 道简答题
2. 题目考察对文章主旨、细节、词汇含义的理解
3. 选择题需标注正确答案
4. 简答题需提供参考答案
5. 每道题附带简短解析

请严格按以下 JSON 格式输出（不要输出其他内容）：
```json
[
  {
    "type": "choice",
    "question": "题目内容",
    "options": {"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"},
    "answer": "A",
    "explanation": "解析"
  },
  {
    "type": "short_answer",
    "question": "题目内容",
    "answer": "参考答案",
    "explanation": "解析"
  }
]
```"""


async def generate_article(words: list[dict], target: str) -> str:
    """
    生成包含指定单词的英文文章

    Args:
        words: 单词列表 [{"word": "abandon", "meaning": "v. 放弃"}]
        target: 目标考试 (考研/四六级)

    Returns:
        生成的文章文本
    """
    word_list_str = "\n".join(
        f"- {w['word']}: {w['meaning']}" for w in words
    )

    user_message = f"""目标考试: {target}

请融入以下单词生成文章：
{word_list_str}"""

    messages = [
        {"role": "system", "content": ARTICLE_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    return await chat_completion(messages, temperature=0.8)


async def generate_questions(article: str, target: str) -> list[dict]:
    """
    基于文章生成阅读理解题目

    Args:
        article: 英文文章内容
        target: 目标考试

    Returns:
        题目列表
    """
    user_message = f"""目标考试: {target}

文章内容：
{article}

请根据以上文章生成题目。"""

    messages = [
        {"role": "system", "content": QUESTIONS_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    response = await chat_completion(messages, temperature=0.5)

    # 解析 JSON 响应
    try:
        # 尝试提取 JSON 块
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()
        else:
            json_str = response.strip()
        return json.loads(json_str)
    except (json.JSONDecodeError, IndexError):
        # 解析失败时返回原始文本作为单题
        return [{"type": "raw", "question": response, "answer": "", "explanation": ""}]
