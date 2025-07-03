# TradingAgents 加密货币迁移计划

## 目标

将 TradingAgents 系统从以美股为主的交易框架，全面迁移为以虚拟货币（特别是比特币）为主的交易框架。这包括修改数据获取、市场情绪、技术指标等数据源，并调整代理逻辑以适应加密货币市场的特性，同时将现有示例修改为 BTC。

## 详细计划

### 1. 数据源替换与新增

*   **移除/禁用股票相关数据源：**
    *   `tradingagents/dataflows/finnhub_utils.py`：移除或禁用所有 Finnhub 相关的股票新闻、内部人情绪和交易数据获取功能。
    *   `tradingagents/dataflows/yfin_utils.py`：移除或禁用所有 Yahoo Finance 相关的股票数据获取功能。
    *   `tradingagents/dataflows/stockstats_utils.py`：评估其技术指标是否适用于加密货币。如果不支持，则移除或禁用，并寻找加密货币专用的技术分析库或在新的 `crypto_utils.py` 中实现。
    *   `tradingagents/dataflows/interface.py`：修改或移除所有调用上述股票相关工具的函数。

*   **引入加密货币数据源 (使用 CCXT)：**
    *   **安装 CCXT 库：** 确保 `pyproject.toml` 或 `requirements.txt` 中包含 `ccxt` 依赖。
    *   **创建 `tradingagents/dataflows/crypto_utils.py` 文件：**
        *   实现基于 CCXT 的加密货币价格、交易量、订单簿等数据获取功能。
        *   支持选择主流交易所（例如 Binance, Coinbase Pro, Kraken 等），并提供配置选项。
        *   实现获取历史 K 线数据 (OHLCV) 的函数。
        *   实现获取实时价格（如果需要，考虑 WebSocket 集成）。
        *   考虑集成链上数据（如 BlockCypher 或 Blockchain.com API）以获取活跃地址、交易笔数等基本链上指标。
    *   **更新 `tradingagents/dataflows/interface.py`：**
        *   引入新的加密货币数据获取函数，例如 `get_crypto_ohlcv_data`, `get_crypto_price`, `get_blockchain_data` 等。
        *   确保这些新函数与现有数据流接口兼容，或根据需要调整接口设计。
    *   **更新 `tradingagents/dataflows/config.py` 和 `tradingagents/default_config.py`：**
        *   添加加密货币交易所 API 密钥配置（如果需要）。
        *   添加默认的加密货币符号（例如 "BTC"）。

*   **调整现有通用数据源：**
    *   `tradingagents/dataflows/googlenews_utils.py`：修改其查询逻辑，使其能够搜索与加密货币相关的新闻（例如，添加 "Bitcoin", "cryptocurrency", "blockchain" 等关键词）。
    *   `tradingagents/dataflows/reddit_utils.py`：修改其查询逻辑，使其能够搜索与加密货币相关的 Reddit 讨论（例如，指定加密货币相关的 subreddit）。

### 2. 代理逻辑修改

*   **基本面分析师 (`tradingagents/agents/analysts/fundamentals_analyst.py`)：**
    *   **彻底修改其逻辑：** 不再依赖传统财务报表（资产负债表、损益表、现金流）。
    *   **引入加密货币“基本面”分析：**
        *   **项目白皮书和路线图分析：** 评估项目的愿景、技术、发展方向。
        *   **开发活动：** 分析 GitHub 提交频率、开发者数量、代码库活跃度。
        *   **链上数据：** 分析活跃地址、交易笔数、交易量、矿工收入、质押率、销毁率等。
        *   **代币经济学：** 分析代币供应量、通胀/通缩模型、代币分配、锁仓情况。
        *   **监管环境和法律新闻：** 评估潜在的监管风险和机遇。
        *   **竞争格局：** 分析与同类项目的比较优势和劣势。
    *   **修改系统提示 (`system_message`)：** 以反映这些新的分析重点，指导 LLM 进行加密货币特有的基本面分析。

*   **市场分析师 (`tradingagents/agents/analysts/market_analyst.py`)：**
    *   **调整技术指标分析：** 确保使用的技术指标（如 SMA, EMA, MACD, RSI, Bollinger Bands, ATR, MFI）适用于加密货币市场。如果 `stockstats_utils.py` 不支持，则在 `crypto_utils.py` 中实现基于 CCXT 数据的技术指标计算。
    *   考虑加密货币市场特有的技术分析模式（例如，高波动性、24/7 交易）。

*   **新闻分析师 (`tradingagents/agents/analysts/news_analyst.py`) 和社交媒体分析师 (`tradingagents/agents/analysts/social_media_analyst.py`)：**
    *   确保他们能够有效地从加密货币新闻源（如 CoinDesk, Cointelegraph）和加密货币社交媒体平台（如 Twitter/X, Telegram, Discord）获取和分析信息。
    *   可能需要调整情绪分析模型，以适应加密货币社区特有的语言和情绪表达（例如，对“FOMO”, “FUD”, “HODL”等术语的理解）。

*   **交易员 (`tradingagents/agents/trader/trader.py`) 和风险管理团队 (`tradingagents/agents/risk_mgmt/`)：**
    *   **调整交易策略：** 适应加密货币市场的高波动性、24/7 交易、滑点、流动性问题以及不同的交易费用结构。
    *   **引入新的风险指标：** 考虑清算风险、智能合约风险、交易所风险、监管风险等。
    *   调整风险管理模型，以适应加密货币的独特风险敞口。

### 3. CLI 和结果输出修改

*   **`cli/main.py`：**
    *   修改 `get_ticker()` 函数的默认值和提示，使其更适合加密货币（例如，默认值改为 "BTC"，提示改为“Enter the cryptocurrency symbol to analyze”）。
    *   修改 `results_dir` 的路径生成逻辑，确保结果目录以加密货币符号命名，例如 `results/BTC/2025-07-03/`。
    *   更新 `display_complete_report` 中的报告标题和内容，以反映加密货币相关的分析（例如，将“Fundamentals Analyst Report”改为“Crypto Fundamentals Report”）。

*   **`results/` 目录：**
    *   删除现有的股票示例目录（AAPL, GOOG, NVDA, SPY）。
    *   确保新的分析结果以 BTC 等加密货币符号命名。

## 系统修改示意图

```mermaid
graph TD
    subgraph 现有数据流 (待移除/修改)
        A[Finnhub News/Insider] --> B(数据流接口);
        C[SimFin Financials] --> B;
        D[Yahoo Finance Data] --> B;
        E[Stockstats Indicators] --> B;
    end

    subgraph 目标数据流
        F[CCXT (Binance, Coinbase Pro等)] --> G(新的 crypto_utils.py);
        H[Google News] -- 调整查询 --> G;
        I[Reddit News] -- 调整查询 --> G;
        J[加密新闻源: CoinDesk, Cointelegraph] --> G;
        K[区块链数据: BlockCypher/Blockchain.com] --> G;
        G --> B;
    end

    subgraph 现有代理层 (待修改)
        L[基本面分析师: 依赖财务报表] --> M(代理逻辑);
        N[市场分析师: 依赖股票技术指标] --> M;
        O[新闻分析师: 依赖通用新闻] --> M;
        P[社交媒体分析师: 依赖通用社交媒体] --> M;
    end

    subgraph 目标代理层
        Q[基本面分析师: 依赖链上数据, 项目健康度] --> R(调整后的代理逻辑);
        S[市场分析师: 依赖加密货币技术指标] --> R;
        T[新闻分析师: 依赖加密新闻] --> R;
        U[社交媒体分析师: 依赖加密社区情绪] --> R;
        R --> M;
    end

    B --> M;
    M --> V[交易图 (LangGraph)];
    V --> W[模拟交易所];
    X[CLI/配置] -- 更新股票符号为BTC --> Y[系统运行];

    style A fill:#f9f,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
    style C fill:#f9f,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
    style D fill:#f9f,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
    style E fill:#f9f,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
    style L fill:#f9f,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
    style N fill:#f9f,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
    style O fill:#f9f,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
    style P fill:#f9f,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5

    style F fill:#9f9,stroke:#333,stroke-width:2px
    style H fill:#9f9,stroke:#333,stroke-width:2px
    style I fill:#9f9,stroke:#333,stroke-width:2px
    style J fill:#9f9,stroke:#333,stroke-width:2px
    style K fill:#9f9,stroke:#333,stroke-width:2px
    style Q fill:#9cf,stroke:#333,stroke-width:2px
    style S fill:#9cf,stroke:#333,stroke-width:2px
    style T fill:#9cf,stroke:#333,stroke-width:2px
    style U fill:#9cf,stroke:#333,stroke-width:2px
    style Y fill:#9cf,stroke:#333,stroke-width:2px