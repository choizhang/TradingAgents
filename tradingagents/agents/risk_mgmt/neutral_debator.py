import time
import json


def create_neutral_debator(llm):
    def neutral_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        neutral_history = risk_debate_state.get("neutral_history", "")

        current_risky_response = risk_debate_state.get("current_risky_response", "")
        current_safe_response = risk_debate_state.get("current_safe_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        trader_decision = state["trader_investment_plan"]

        prompt = f"""作为中立风险分析师，你的职责是提供一个平衡的视角，权衡交易员决策或计划的潜在收益和风险。你优先考虑全面方法，评估利弊，同时考虑更广泛的市场趋势、潜在的经济变化和多元化策略。以下是交易员的决定：

{trader_decision}

你的任务是挑战激进和保守分析师，指出每个观点可能过于乐观或过于谨慎的地方。使用以下数据来源的见解来支持一种温和、可持续的策略，以调整交易员的决策：

市场研究报告：{market_research_report}
社交媒体情绪报告：{sentiment_report}
最新世界事务报告：{news_report}
公司基本面报告：{fundamentals_report}
这是当前的对话历史：{history} 这是激进分析师的最新回应：{current_risky_response} 这是保守分析师的最新回应：{current_safe_response}。如果没有来自其他观点的回应，不要凭空捏造，只提出你的观点。

通过批判性地分析双方，解决激进和保守论点中的弱点，积极参与，以倡导更平衡的方法。挑战他们的每一个观点，以说明为什么中等风险策略可能提供两全其美的最佳选择，在提供增长潜力的同时防范极端波动。专注于辩论而不是简单地呈现数据，旨在表明平衡的观点可以带来最可靠的结果。请用中文以对话形式输出，无需任何特殊格式。"""

        response = llm.invoke(prompt)

        argument = f"Neutral Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "risky_history": risk_debate_state.get("risky_history", ""),
            "safe_history": risk_debate_state.get("safe_history", ""),
            "neutral_history": neutral_history + "\n" + argument,
            "latest_speaker": "Neutral",
            "current_risky_response": risk_debate_state.get(
                "current_risky_response", ""
            ),
            "current_safe_response": risk_debate_state.get("current_safe_response", ""),
            "current_neutral_response": argument,
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return neutral_node
