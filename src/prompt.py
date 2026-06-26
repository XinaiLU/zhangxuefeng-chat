from __future__ import annotations

from pathlib import Path
from typing import Optional

SKILL_PATH = Path(__file__).resolve().parent.parent / "skills" / "zhangxuefeng-skill" / "SKILL.md"

APP_PREFIX = """\
你正在一个 Streamlit 网页里与用户对话。请严格遵循下方 SKILL 文档中的角色、工作流与表达风格。

额外约束：
- 回答使用 Markdown，段落清晰，适合网页阅读
- 首次对话开头用一句话说明：这是基于公开言论的角色扮演，非张雪峰本人
- 涉及具体院校/专业/就业数据时，若下方提供了「联网检索摘要」则优先引用；没有则基于 SKILL 内框架回答，并说明建议用户自行核实最新数据
"""


def load_skill_content() -> str:
    if not SKILL_PATH.exists():
        raise FileNotFoundError(f"找不到 SKILL 文件: {SKILL_PATH}")
    return SKILL_PATH.read_text(encoding="utf-8")


def build_system_prompt(search_context: Optional[str] = None) -> str:
    skill = load_skill_content()
    parts = [APP_PREFIX, skill]
    if search_context:
        parts.append("\n\n## 联网检索摘要（供 Step 2 参考）\n\n" + search_context)
    return "\n\n---\n\n".join(parts)
