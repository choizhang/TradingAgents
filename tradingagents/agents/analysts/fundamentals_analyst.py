from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json


def create_fundamentals_analyst(llm, toolkit):
    def fundamentals_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        if toolkit.config["online_tools"]:
            tools = [toolkit.get_fundamentals_llm, toolkit.summarize_text] # Add summarize_text tool
        else:
            tools = [
                toolkit.get_finnhub_company_insider_sentiment,
                toolkit.get_finnhub_company_insider_transactions,
                toolkit.get_simfin_balance_sheet,
                toolkit.get_simfin_cashflow,
                toolkit.get_simfin_income_stmt,
                toolkit.summarize_text, # Add summarize_text tool
            ]

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
