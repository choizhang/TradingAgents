# TradingAgents 系统架构

TradingAgents 框架采用模块化和代理驱动的架构，旨在模拟真实世界的金融交易团队。其核心设计基于 LangGraph，以确保高度的灵活性和可扩展性。

## 核心组件

### 1. 代理层 (Agents)
该层包含多个 LLM 驱动的代理，每个代理负责特定的金融分析和决策任务。
*   **分析师团队 (`tradingagents/agents/analysts/`)：**
    *   `fundamentals_analyst.py`：基本面分析。
    *   `market_analyst.py`：市场分析。
    *   `news_analyst.py`：新闻分析。
    *   `social_media_analyst.py`：社交媒体情绪分析。
*   **研究员团队 (`tradingagents/agents/researchers/`)：**
    *   `bull_researcher.py`：看涨研究。
    *   `bear_researcher.py`：看跌研究。
    *   通过结构化辩论评估分析师报告。
*   **交易员代理 (`tradingagents/agents/trader/trader.py`)：**
    *   整合分析师和研究员的洞察，制定交易决策。
*   **风险管理团队 (`tradingagents/agents/risk_mgmt/`)：**
    *   `aggresive_debator.py`, `conservative_debator.py`, `neutral_debator.py`：评估投资组合风险，调整交易策略。
*   **投资组合经理 (`tradingagents/agents/managers/research_manager.py`, `tradingagents/agents/managers/risk_manager.py`)：**
    *   批准或拒绝交易提案，并发送订单到模拟交易所。
*   **通用工具 (`tradingagents/agents/utils/`)：**
    *   `memory.py`：使用 ChromaDB 存储金融情景记忆，支持 LLM 嵌入（OpenAI/Google）。

### 2. 数据流层 (Dataflows)
该层负责从各种金融数据源收集、处理和管理数据。
*   `tradingagents/dataflows/config.py`：数据流配置。
*   `tradingagents/dataflows/finnhub_utils.py`：Finnhub 数据接口。
*   `tradingagents/dataflows/googlenews_utils.py`：Google News 数据接口。
*   `tradingagents/dataflows/reddit_utils.py`：Reddit 数据接口。
*   `tradingagents/dataflows/stockstats_utils.py`：股票统计数据处理。
*   `tradingagents/dataflows/yfin_utils.py`：Yahoo Finance 数据接口。
*   `tradingagents/dataflows/interface.py`：数据流接口。

### 3. 图处理层 (Graph)
该层利用 LangGraph 构建代理之间的协作和决策流程。
*   `tradingagents/graph/trading_graph.py`：定义核心交易图。
*   `tradingagents/graph/conditional_logic.py`：条件逻辑处理。
*   `tradingagents/graph/propagation.py`：信息传播机制。
*   `tradingagents/graph/reflection.py`：代理反思机制。
*   `tradingagents/graph/setup.py`：图设置。
*   `tradingagents/graph/signal_processing.py`：信号处理。

## 关键技术决策
*   **LangGraph：** 作为核心编排框架，实现复杂的代理协作和工作流。
*   **LLM 驱动：** 利用 OpenAI 和 Google Gemini 等 LLM 进行智能分析和决策。
*   **ChromaDB：** 作为向量数据库，用于存储和检索金融情景记忆，支持上下文感知。
*   **模块化设计：** 各个代理和数据流模块独立，易于扩展和维护。

## 组件关系图

```mermaid
graph TD
    A[数据源] --> B[数据流层];
    B --> C[代理层];
    C --> D[图处理层 (LangGraph)];
    D -- 交易决策 --> E[模拟交易所];
    C -- 记忆存储/检索 --> F[ChromaDB];
    D -- 报告/洞察 --> G[用户/CLI];

    subgraph 代理层
        C1[分析师团队]
        C2[研究员团队]
        C3[交易员代理]
        C4[风险管理团队]
        C5[投资组合经理]
    end

    C1 --> C2;
    C2 --> C3;
    C3 --> C4;
    C4 --> C5;
    C5 --> D;
    C1 & C2 & C3 & C4 & C5 --> F;