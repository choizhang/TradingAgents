from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json


def create_fundamentals_analyst(llm, toolkit):
    def fundamentals_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        # Determine if the current symbol is a cryptocurrency
        is_crypto = "/" in ticker or ticker.upper() in ["BTC", "ETH", "XRP", "LTC", "BCH"]

        if toolkit.config["online_tools"]:
            tools = [
                toolkit.get_crypto_ohlcv_data_window, # For basic price data, can be used for some "fundamental" context
                toolkit.get_blockchain_data, # Placeholder for actual blockchain data
                toolkit.summarize_text,
            ]
        else:
            if is_crypto:
                tools = [
                    toolkit.get_crypto_ohlcv_data_window, # For basic price data, can be used for some "fundamental" context
                    toolkit.get_blockchain_data, # Placeholder for actual blockchain data
                    toolkit.summarize_text,
                ]
            else: # Fallback for traditional stocks if online_tools is False, but we are migrating to crypto
                tools = [
                    toolkit.get_crypto_ohlcv_data_window, # For basic price data, can be used for some "fundamental" context
                    toolkit.get_blockchain_data, # Placeholder for actual blockchain data
                    toolkit.summarize_text,
                ]

        if is_crypto:
            system_message = (
                "你是一名研究员，负责分析过去一周内一个加密货币项目的基本面信息。请撰写一份关于加密货币项目基本面信息的综合报告，包括项目白皮书、路线图、开发活动、链上数据、代币经济学、监管环境和社区情绪，以全面了解项目的基本面信息，从而为交易者提供参考。请务必包含尽可能多的细节。不要简单地说明趋势是混合的，提供详细和细致的分析和见解，以帮助交易者做出决策。"
                + " 确保在报告末尾附加一个 Markdown 表格，以组织报告中的关键点，使其有条理且易于阅读。**所有输出内容必须严格使用简体中文。**"
                + " 请注意：在获取加密货币数据时，请优先使用 'kraken' 交易所，而不是 'binance'。",
            )
        else:
            system_message = (
                "你是一名研究员，负责分析过去一周内一家公司的基本面信息。请撰写一份关于公司基本面信息的综合报告，包括财务文件、公司简介、基本公司财务数据、公司财务历史、内部人情绪和内部人交易，以全面了解公司的基本面信息，从而为交易者提供参考。请务必包含尽可能多的细节。不要简单地说明趋势是混合的，提供详细和细致的分析和见解，以帮助交易者做出决策。"
                + " 确保在报告末尾附加一个 Markdown 表格，以组织报告中的关键点，使其有条理且易于阅读。**所有输出内容必须严格使用简体中文。**",
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
            "fundamentals_report": summarized_report,
        }

    return fundamentals_analyst_node
