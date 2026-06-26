# 张雪峰 Streamlit 前端

把 [XinaiLU/zhangxuefeng-skill](https://github.com/XinaiLU/zhangxuefeng-skill) 部署成可对话的 Web 界面。

## 快速开始

```bash
cd touch-the-fish
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

浏览器打开终端显示的本地地址（通常是 `http://localhost:8501`）。

## 配置

在 Streamlit 左侧边栏填写：

| 项 | 说明 |
|---|---|
| API Key | OpenAI 或兼容接口密钥 |
| Base URL | 可选，如 DeepSeek `https://api.deepseek.com/v1` |
| 模型 | 如 `gpt-4o-mini`、`deepseek-chat` |
| 联网检索 | 涉及专业/就业类问题时先用 DuckDuckGo 搜公开信息 |

也可复制 `.env.example` 为 `.env` 本地保存（当前版本以侧边栏输入为主）。

## 项目结构

```
├── app.py                          # Streamlit 主入口
├── src/
│   ├── prompt.py                   # 加载 SKILL.md 构建 system prompt
│   ├── llm.py                      # OpenAI 兼容 API 调用
│   └── search.py                   # 可选联网检索
└── skills/zhangxuefeng-skill/      # 张雪峰 skill 仓库
    └── SKILL.md
```

## 部署到 Streamlit Cloud（免费公网访问）

### 第一步：推到 GitHub

```bash
cd ~/Desktop/touch-the-fish

# 去掉 skill 子目录里的 .git，否则文件不会进主仓库
rm -rf skills/zhangxuefeng-skill/.git

git init
git add app.py src/ skills/ requirements.txt .streamlit/config.toml .gitignore README.md .env.example
git commit -m "Add Zhang Xuefeng Streamlit app"
```

在 GitHub 新建仓库（如 `zhangxuefeng-chat`），然后：

```bash
git remote add origin https://github.com/你的用户名/zhangxuefeng-chat.git
git branch -M main
git push -u origin main
```

### 第二步：连接 Streamlit Cloud

1. 打开 [share.streamlit.io](https://share.streamlit.io/)，用 GitHub 登录
2. 点击 **New app** → 选你的仓库
3. 配置：
   - **Main file path**: `app.py`
   - **Python version**: 3.9 或更高
4. 展开 **Advanced settings** → **Secrets**，粘贴：

```toml
[qwen]
api_key = "sk-ws-你的百炼APIKey"
workspace_id = "ws-你的WorkspaceID"
model = "qwen-plus"
```

5. 点击 **Deploy**，等 1–3 分钟

部署成功后会得到公网地址，形如：`https://zhangxuefeng-chat.streamlit.app`

### 本地用 Secrets 测试（可选）

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# 编辑 secrets.toml 填入真实 Key
streamlit run app.py
```

## 说明

- 本应用为 **角色扮演 + 思维框架** 演示，回答基于 skill 文档与公开检索，**不代表张雪峰本人观点**。
- 具体院校分数线、就业率等请以官方与权威渠道为准。
- **不要把 API Key 提交到 GitHub**，只用 Streamlit Secrets 或本地 `secrets.toml`（已在 `.gitignore` 中忽略）。
