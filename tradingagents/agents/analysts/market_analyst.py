from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json


def create_market_analyst(llm, toolkit):

    def market_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        # Standardize ticker to a trading pair if it's a common crypto symbol
        # Ensure ticker is in trading pair format for crypto
        if "/" not in ticker:
            # Assume USDT as default quote currency if not specified
            ticker = f"{ticker.upper()}/USDT"
        # Add more crypto symbols as needed

        is_crypto = "/" in ticker # Now, only check for '/' to determine if it's a pair

        # Always include crypto technical indicators and summarization
        tools = [
            toolkit.get_crypto_technical_indicators,
            toolkit.summarize_text,
        ]

        # Add crypto OHLCV data if it's a crypto symbol
        if is_crypto:
            tools.insert(0, toolkit.get_crypto_ohlcv_data_window)

        # Add news and social media tools, which are now crypto-aware
        tools.append(toolkit.get_google_news)
        tools.append(toolkit.get_reddit_company_news)
        tools.append(toolkit.get_reddit_news)


        system_message = (
            """你是一名交易助手，负责分析金融市场。你的职责是从以下列表中选择与给定市场状况或交易策略最相关的指标。目标是选择最多 **8 个指标**，这些指标应提供互补的见解，避免冗余。类别和每个类别的指标如下：
请注意：在获取加密货币数据时，请优先使用 'kraken' 交易所，而不是 'binance'。

移动平均线：
- close_50_sma: 50 简单移动平均线 (SMA)：中期趋势指标。用途：识别趋势方向并作为动态支撑/阻力。提示：它滞后于价格；与更快的指标结合使用以获得及时信号。
- close_200_sma: 200 简单移动平均线 (SMA)：长期趋势基准。用途：确认整体市场趋势并识别金叉/死叉设置。提示：它反应缓慢；最适合战略性趋势确认，而不是频繁的交易入场。
- close_10_ema: 10 指数移动平均线 (EMA)：响应式短期平均线。用途：捕捉动量的快速变化和潜在的入场点。提示：在震荡市场中容易出现噪音；与较长期的平均线一起使用以过滤虚假信号。

MACD 相关：
- macd: MACD：通过 EMA 差异计算动量。用途：寻找交叉和背离作为趋势变化的信号。提示：在低波动性或横盘市场中与其他指标确认。
- macds: MACD 信号线：MACD 线的 EMA 平滑。用途：与 MACD 线交叉时触发交易。提示：应作为更广泛策略的一部分，以避免虚假信号。
- macdh: MACD 柱状图：显示 MACD 线与其信号线之间的差距。用途：可视化动量强度并及早发现背离。提示：可能波动较大；在快速变化的市场中补充额外的过滤器。

动量指标：
- rsi: RSI：衡量动量以标记超买/超卖状况。用途：应用 70/30 阈值并观察背离以发出反转信号。提示：在强劲趋势中，RSI 可能保持极端；始终与趋势分析交叉检查。

波动率指标：
- boll: 布林带中轨：作为布林带基础的 20 简单移动平均线 (SMA)。用途：作为价格波动的动态基准。提示：与上轨和下轨结合使用，有效发现突破或反转。
- boll_ub: 布林带上轨：通常比中轨高 2 个标准差。用途：发出潜在超买状况和突破区域的信号。提示：与其他工具确认信号；在强劲趋势中价格可能沿着布林带运行。
- boll_lb: 布林带下轨：通常比中轨低 2 个标准差。用途：指示潜在超卖状况。提示：使用额外分析以避免虚假反转信号。
- atr: ATR：平均真实波动范围，衡量波动率。用途：根据当前市场波动率设置止损水平并调整头寸大小。提示：它是一种反应性指标，因此应作为更广泛风险管理策略的一部分使用。

成交量指标：
- vwma: VWMA：按成交量加权的移动平均线。用途：通过将价格行为与成交量数据相结合来确认趋势。提示：注意成交量飙升导致的偏差结果；与其他成交量分析结合使用。

- 选择提供多样化和互补信息的指标。避免冗余（例如，不要同时选择 rsi 和 stochrsi）。并简要解释它们为何适合给定的市场环境。请撰写一份非常详细和细致的趋势报告。不要简单地说明趋势是混合的，提供详细和细致的分析和见解，以帮助交易者做出决策。确保你请求的是从当前日期起过去 1 个月的市场价格数据。"""
            + """ 确保在报告末尾附加一个 Markdown 表格，以组织报告中的关键点，使其有条理且易于阅读。请用中文输出所有报告内容。"""
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是一个乐于助人的AI助手，与其他助手协作。"
                    " 使用提供的工具来回答问题。"
                    " 如果你无法完全回答，没关系；另一个拥有不同工具的助手将从你离开的地方继续。"
                    " 执行你能做的，以取得进展。"
                    " 如果你或任何其他助手有最终交易提案：**买入/持有/卖出** 或可交付成果，"
                    " 请在你的回复前加上“最终交易提案：**买入/持有/卖出**”，以便团队知道停止。"
                    " 你可以使用以下工具：{tool_names}。\n{system_message}"
                    "供你参考，当前日期是 {current_date}。我们想要查看的公司是 {ticker}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            if isinstance(result.content, list):
                report = "\n".join(result.content)
            else:
                report = result.content
       
        # Summarize the report before returning
        summarized_report = toolkit.summarize_text(report) # Summarize to 1500 characters

        return {
            "messages": [result],
            "market_report": summarized_report,
        }

    return market_analyst_node
