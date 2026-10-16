from groq import Groq

MODEL_NAME = "openai/gpt-oss-20b"


def create_budget_review(
    api_key,
    question,
    monthly_income,
    monthly_expenses,
    planned_savings,
    bank_balance,
):
    client = Groq(api_key=api_key)

    prompt = f"""
User question: {question}

Household monthly figures in Pakistani rupees:
- Actual income: PKR {monthly_income:,.0f}
- Actual expenses: PKR {monthly_expenses:,.0f}
- Planned savings: PKR {planned_savings:,.0f}
- Current bank balances: PKR {bank_balance:,.0f}
"""

    result = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0.4,
        max_tokens=650,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a practical, nonjudgmental household budgeting "
                    "assistant for Rawalpindi and Islamabad. Use Pakistani "
                    "rupees. Give general budgeting observations, not "
                    "personalized investment advice. Do not guarantee outcomes."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )

    return result.choices[0].message.content
