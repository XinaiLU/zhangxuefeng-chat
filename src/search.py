from duckduckgo_search import DDGS


def web_search(query: str, max_results: int = 5) -> str:
    """检索公开网页，供张雪峰式「先看数据再开口」使用。"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
    except Exception as exc:
        return f"检索失败: {exc}"

    if not results:
        return "未找到相关检索结果。"

    lines: list[str] = []
    for idx, item in enumerate(results, start=1):
        title = item.get("title", "")
        body = item.get("body", "")
        href = item.get("href", "")
        lines.append(f"{idx}. **{title}**\n   {body}\n   来源: {href}")
    return "\n\n".join(lines)
