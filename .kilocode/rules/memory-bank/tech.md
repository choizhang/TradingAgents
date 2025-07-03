# TradingAgents 技术栈

**核心技术与框架：**
*   **编程语言：** Python (要求 >=3.10)
*   **LLM 编排框架：** LangGraph
*   **大型语言模型 (LLM) 集成：**
    *   OpenAI (通过 `langchain-openai`)
    *   Google Gemini (通过 `langchain-google-genai`)
    *   Anthropic (通过 `langchain-anthropic`)
*   **向量数据库：** ChromaDB (用于金融情景记忆)
*   **HTTP 客户端：** httpx (用于代理配置)

**主要依赖库 (来自 `pyproject.toml`)：**
*   `akshare`：金融数据接口
*   `backtrader`：回测框架
*   `chainlit`：CLI 界面和交互
*   `chromadb`：向量数据库
*   `eodhd`：金融数据接口
*   `feedparser`：RSS/Atom feed 解析
*   `langchain-anthropic`：Anthropic LLM 集成
*   `langchain-experimental`：LangChain 实验性模块
*   `langchain-google-genai`：Google Gemini LLM 集成
*   `langchain-openai`：OpenAI LLM 集成
*   `langgraph`：LLM 编排框架
*   `pandas`：数据处理和分析
*   `parsel`：HTML/XML 解析
*   `praw`：Reddit API 封装
*   `pytz`：时区处理
*   `questionary`：交互式命令行提示
*   `redis`：内存数据结构存储
*   `requests`：HTTP 请求库
*   `rich`：富文本和终端美化
*   `setuptools`：Python 包安装
*   `stockstats`：股票统计数据计算
*   `tqdm`：进度条
*   `tushare`：金融数据接口
*   `typing-extensions`：类型提示扩展
*   `ccxt`：加密货币交易平台集成

**开发设置与工具：**
*   **虚拟环境：** 推荐使用 `conda` 或其他虚拟环境管理器。
*   **API 密钥：** 需要配置 `OPENAI_API_KEY` 和 `GOOGLE_API_KEY` 环境变量。
*   **CLI 工具：** 通过 `python -m cli.main` 运行。

**技术约束与注意事项：**
*   推荐使用 Python 3.11，因为 3.13 版本可能存在库兼容性问题。
*   LLM 模型选择：实验推荐使用 `o1-preview` 和 `gpt-4o` 进行深度思考和快速思考，测试推荐使用 `o4-mini` 和 `gpt-4.1-mini` 以节省成本。
*   嵌入模型：`FinancialSituationMemory` 类中根据 LLM 提供商选择不同的嵌入模型（`gemini-embedding-exp-03-07` 或 `text-embedding-3-small`/`nomic-embed-text`）。
*   上下文窗口管理：在多空激变等数据量过大时，可能需要对大内容进行总结以避免上下文溢出。
*   市场分析配置：`system_prompt` 中 `start_day` 设置为 1 个月，新闻查找前 3 天，相关度召回从 2 改为 1。