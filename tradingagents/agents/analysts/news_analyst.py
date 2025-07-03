from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json


def create_news_analyst(llm, toolkit):
    def news_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        if toolkit.config["online_tools"]:
            tools = [toolkit.get_google_news, toolkit.get_reddit_news, toolkit.summarize_text]
        else:
            # Assuming offline tools would still use the local data fetching mechanisms
            tools = [
                toolkit.get_google_news,
                toolkit.get_reddit_news,
                toolkit.summarize_text,
            ]

        system_message = (
            "你是一名新闻研究员，负责分析过去一周的最新新闻和趋势。请撰写一份关于当前世界状况的综合报告，该报告应与交易和宏观经济相关。请查阅 EODHD 和 Finnhub 的新闻，以确保报告的全面性。不要简单地说明趋势是混合的，提供详细和细致的分析和见解，以帮助交易者做出决策。"
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
                    "供你参考，当前日期是 {current_date}。我们正在查看的公司是 {ticker}",
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
            "news_report": summarized_report,
        }

    return news_analyst_node
