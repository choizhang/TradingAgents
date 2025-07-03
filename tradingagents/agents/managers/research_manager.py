import time
import json


def create_research_manager(llm, memory):
    def research_manager_node(state) -> dict:
        history = state["investment_debate_state"].get("history", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        investment_debate_state = state["investment_debate_state"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        # Truncate curr_situation to avoid exceeding embedding model's payload limit
        max_payload_size = 1000  # Limit to 1000 characters
        if len(curr_situation) > max_payload_size:
            curr_situation = curr_situation[:max_payload_size] + "..."
        past_memories = memory.get_memories(curr_situation, n_matches=1)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""作为投资组合经理和辩论协调员，你的职责是批判性地评估本轮辩论，并做出明确的决定：支持看跌分析师、看涨分析师，或者仅在有充分理由的情况下选择持有。

简洁地总结双方的关键点，重点关注最有说服力的证据或推理。你的建议——买入、卖出或持有——必须清晰且可操作。避免仅仅因为双方都有有效观点就默认选择持有；根据辩论中最有力的论据做出明确的立场。

此外，为交易员制定详细的投资计划。这应包括：

你的建议：一个由最有说服力的论据支持的果断立场。
理由：解释为什么这些论据导致你的结论。
战略行动：实施建议的具体步骤。
请考虑你在类似情况下的过往错误。利用这些见解来完善你的决策，并确保你正在学习和改进。请用中文以对话形式呈现你的分析，就像自然对话一样，无需特殊格式。

Here are your past reflections on mistakes:
\"{past_memory_str}\"

Here is the debate:
Debate History:
{history}"""
        response = llm.invoke(prompt)

        new_investment_debate_state = {
            "judge_decision": response.content,
            "history": investment_debate_state.get("history", ""),
            "bear_history": investment_debate_state.get("bear_history", ""),
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": response.content,
            "count": investment_debate_state["count"],
        }

        return {
            "investment_debate_state": new_investment_debate_state,
            "investment_plan": response.content,
        }

    return research_manager_node
