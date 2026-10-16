import pandas as pd

INCOME_COLUMNS = ["Source", "Expected PKR", "Actual PKR"]

EXPENSE_COLUMNS = [
    "Category",
    "Description",
    "Budget PKR",
    "Actual PKR",
]

BANK_COLUMNS = [
    "Bank / account name",
    "Opening balance PKR",
    "Current balance PKR",
    "Monthly deposits PKR",
    "Monthly withdrawals PKR",
]

BUDGET_COLUMNS = ["Goal", "Monthly target PKR"]


def starter_income():
    return pd.DataFrame(
        [
            {"Source": "Salary", "Expected PKR": 0, "Actual PKR": 0},
            {"Source": "", "Expected PKR": 0, "Actual PKR": 0},
        ],
        columns=INCOME_COLUMNS,
    )


def starter_expenses():
    categories = [
        "Rent / mortgage",
        "Groceries",
        "Electricity",
        "Gas",
        "Water",
        "Internet / phone",
        "School fees",
        "Transport / fuel",
        "Healthcare / medicines",
        "Household supplies",
        "Dining out",
        "Clothing",
        "Childcare",
        "Domestic help",
        "Maintenance",
        "Subscriptions",
        "Family support",
        "Personal care",
        "Savings / investments",
        "Other",
    ]
    return pd.DataFrame(
        [
            {
                "Category": category,
                "Description": "",
                "Budget PKR": 0,
                "Actual PKR": 0,
            }
            for category in categories
        ],
        columns=EXPENSE_COLUMNS,
    )


def starter_banks():
    return pd.DataFrame(
        [
            {
                "Bank / account name": "Account 1",
                "Opening balance PKR": 0,
                "Current balance PKR": 0,
                "Monthly deposits PKR": 0,
                "Monthly withdrawals PKR": 0,
            },
            {
                "Bank / account name": "Account 2",
                "Opening balance PKR": 0,
                "Current balance PKR": 0,
                "Monthly deposits PKR": 0,
                "Monthly withdrawals PKR": 0,
            },
        ],
        columns=BANK_COLUMNS,
    )


def starter_budget():
    return pd.DataFrame(
        [
            {"Goal": "Emergency fund", "Monthly target PKR": 0},
            {"Goal": "Education", "Monthly target PKR": 0},
            {"Goal": "Home / major purchase", "Monthly target PKR": 0},
        ],
        columns=BUDGET_COLUMNS,
    )


def numeric_total(frame, column):
    if frame is None or column not in frame.columns:
        return 0.0

    values = pd.to_numeric(frame[column], errors="coerce").fillna(0)
    return float(values.sum())


def clean_frame(frame, columns, limit=None):
    """Keep expected columns, convert money columns to numbers, and enforce row limit."""
    if frame is None or not isinstance(frame, pd.DataFrame):
        frame = pd.DataFrame(columns=columns)

    result = frame.copy()

    for column in columns:
        if column not in result.columns:
            result[column] = 0 if "PKR" in column else ""

    result = result[columns]

    for column in columns:
        if "PKR" in column:
            result[column] = pd.to_numeric(
                result[column], errors="coerce"
            ).fillna(0)

    if limit is not None:
        result = result.head(limit)

    return result.reset_index(drop=True)


def make_projection(starting_balance, monthly_saving, annual_return, years=5):
    """Create a monthly savings estimate, assuming fixed contributions and return."""
    balance = float(starting_balance)
    monthly_saving = float(monthly_saving)
    monthly_rate = float(annual_return) / 100 / 12
    rows = []

    for month in range(1, years * 12 + 1):
        balance = balance * (1 + monthly_rate) + monthly_saving

        if month % 12 == 0:
            rows.append(
                {
                    "Year": month // 12,
                    "Projected balance PKR": round(balance),
                    "Contributions added PKR": round(monthly_saving * month),
                }
            )

    return pd.DataFrame(rows)
