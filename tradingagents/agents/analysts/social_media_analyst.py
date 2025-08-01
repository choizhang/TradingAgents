from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json


def create_social_media_analyst(llm, toolkit):
    def social_media_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        if toolkit.config["online_tools"]:
            tools = [toolkit.get_stock_news_llm, toolkit.summarize_text] # Add summarize_text tool
        else:
            tools = [
                toolkit.get_reddit_stock_info,
                toolkit.summarize_text, # Add summarize_text tool
            ]

        system_message = (
            "你是一名社交媒体和公司特定新闻研究员/分析师，负责分析过去一周内特定公司的社交媒体帖子、最新公司新闻和公众情绪。你将获得一家公司的名称，你的目标是撰写一份全面的长篇报告，详细说明你对该公司当前状况的分析、见解以及对交易者和投资者的影响，这些分析基于对社交媒体、人们对该公司的看法、情绪数据以及最新公司新闻的考察。尝试查看所有可能的来源，从社交媒体到情绪到新闻。不要简单地说明趋势是混合的，提供详细和细致的分析和见解，以帮助交易者做出决策。"
            + """ 确保在报告末尾附加一个 Markdown 表格，以组织报告中的关键点，使其有条理且易于阅读。请用中文输出所有报告内容。""",
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
                    "供你参考，当前日期是 {current_date}。我们想要分析的公司是 {ticker}",
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
            "sentiment_report": summarized_report,
        }

        return {
            "messages": [result],
            "sentiment_report": report,
        }

    return social_media_analyst_node
