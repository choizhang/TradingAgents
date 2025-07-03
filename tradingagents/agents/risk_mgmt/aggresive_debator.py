import time
import json


def create_risky_debator(llm):
    def risky_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        risky_history = risk_debate_state.get("risky_history", "")

        current_safe_response = risk_debate_state.get("current_safe_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        trader_decision = state["trader_investment_plan"]

        prompt = f"""作为激进风险分析师，你的职责是积极倡导高回报、高风险的机会，强调大胆的策略和竞争优势。在评估交易员的决策或计划时，要密切关注潜在的上涨空间、增长潜力和创新收益——即使这些伴随着更高的风险。使用提供的市场数据和情绪分析来加强你的论点并挑战对立观点。具体来说，直接回应保守和中立分析师提出的每一点，用数据驱动的反驳和有说服力的推理进行反击。强调他们的谨慎可能错失关键机会，或者他们的假设可能过于保守。以下是交易员的决定：

{trader_decision}

你的任务是质疑和批判保守和中立的立场，从而为交易员的决定创建一个令人信服的案例，以证明为什么你的高回报视角提供了最佳的前进道路。将以下来源的见解纳入你的论点：

市场研究报告：{market_research_report}
社交媒体情绪报告：{sentiment_report}
最新世界事务报告：{news_report}
公司基本面报告：{fundamentals_report}
这是当前的对话历史：{history} 这是保守分析师的最新论点：{current_safe_response} 这是中立分析师的最新论点：{current_neutral_response}。如果没有来自其他观点的回应，不要凭空捏造，只提出你的观点。

积极参与，解决提出的任何具体担忧，驳斥他们逻辑中的弱点，并主张冒险的好处，以超越市场规范。保持专注于辩论和说服，而不仅仅是呈现数据。挑战每一个反驳点，以强调为什么高风险方法是最佳选择。请用中文以对话形式输出，无需任何特殊格式。"""

        response = llm.invoke(prompt)

        argument = f"Risky Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "risky_history": risky_history + "\n" + argument,
            "safe_history": risk_debate_state.get("safe_history", ""),
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Risky",
            "current_risky_response": argument,
            "current_safe_response": risk_debate_state.get("current_safe_response", ""),
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return risky_node
