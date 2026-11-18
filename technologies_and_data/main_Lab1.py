import sys
import numpy as np
import pandas as pd


path = sys.argv[1] if len(sys.argv) > 1 else "sales__U (1).csv"

# Налаштування відображення pandas, щоб таблиці зручніше читалися у консолі.
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)
pd.set_option("display.float_format", lambda x: f"{x:,.2f}")

# Зчитуємо CSV-файл.
df = pd.read_csv(path, sep=";", encoding="cp1251")

# Відповідність українських скорочень назв місяців їх числовим значенням.
# Це потрібно для відновлення чисел, які Excel помилково перетворив на дати.
ua_month = {
    "Січ": 1, "Лют": 2, "Бер": 3, "Кві": 4, "Тра": 5, "Чер": 6,
    "Лип": 7, "Сер": 8, "Вер": 9, "Жов": 10, "Лис": 11, "Гру": 12
}

# Функція для перетворення значення у число.
# Спочатку пробуємо звичайне перетворення у float.
# Якщо значення має вигляд "29.Вер" або "Лют.49",
# відновлюємо його як десяткове число.
def parse_number(value):
    if pd.isna(value):
        return np.nan

    s = str(value).strip()

    try:
        return float(s)
    except ValueError:
        pass

    parts = s.split(".")
    if len(parts) != 2:
        return np.nan

    left, right = parts

    # Приклад: "29.Вер" -> 29.9
    if right in ua_month:
        return float(f"{int(float(left))}.{ua_month[right]}")

    # Приклад: "Лют.49" -> 2.49
    if left in ua_month:
        return float(f"{ua_month[left]}.{right}")

    return np.nan


# Колонки, які повинні містити числові значення.
numeric_text_columns = [
    "price",
    "value",
    "discount_amount",
    "total",
    "Discount_Percent"
]

# Очищуємо числові колонки та приводимо їх до типу float.
for column in numeric_text_columns:
    df[column] = df[column].map(parse_number)

# Перетворюємо текстове поле місяця у тип datetime.
df["Order_Date"] = pd.to_datetime(df["month"], format="%b-%Y")

# Створюємо окрему колонку формату "рік-місяць" для групування по місяцях.
df["Month"] = df["Order_Date"].dt.to_period("M")

# Окремо зберігаємо початкову вартість товарів до застосування знижки.
df["Gross_Revenue"] = df["value"]

# Розраховуємо фактичну виручку після врахування знижки.
df["Revenue"] = df["value"] - df["discount_amount"]

# Розраховуємо фактичний відсоток знижки.
# Якщо value дорівнює нулю, записуємо 0, щоб уникнути ділення на нуль.
df["Discount_Rate"] = np.where(
    df["value"] > 0,
    df["discount_amount"] / df["value"] * 100,
    0
)

# -----------------------------
# Дослідження параметрів даних
# -----------------------------

print("PARAMETERS")

# Кількість рядків і колонок.
print("Shape:", df.shape)

# Назви всіх колонок.
print("Columns:", df.columns.tolist())

# Типи даних у кожній колонці.
print("\nData types:")
print(df.dtypes)

# Кількість пропущених значень.
print("\nMissing values:")
print(df.isna().sum())

# Кількість повністю однакових рядків.
# Ми їх не видаляємо, оскільки у наборі немає унікального Order_ID.
print("\nExact duplicate rows:", df.duplicated().sum())

# Кількість унікальних категорій, штатів, регіонів та місяців.
print("\nCategories:", df["category"].nunique())
print("States:", df["State"].nunique())
print("Regions:", df["Region"].nunique())
print("Months:", df["Month"].nunique())

# -----------------------------
# 1. Загальні показники продажів
# -----------------------------

q1 = pd.Series({
    "Records": len(df),
    "Quantity": df["qty_ordered"].sum(),
    "Gross_Revenue": df["Gross_Revenue"].sum(),
    "Discount": df["discount_amount"].sum(),
    "Revenue": df["Revenue"].sum(),
    "Average_Revenue_per_Record": df["Revenue"].mean(),
    "Discount_Rate_%": df["discount_amount"].sum() / df["Gross_Revenue"].sum() * 100
})

print("\n1. TOTAL SALES")
print(q1)

# -----------------------------
# 2. Продажі по роках
# -----------------------------

# Групуємо дані за роком і рахуємо основні агреговані показники.
q2 = (
    df.groupby(df["Order_Date"].dt.year)
    .agg(
        Revenue=("Revenue", "sum"),
        Gross_Revenue=("Gross_Revenue", "sum"),
        Discount=("discount_amount", "sum"),
        Quantity=("qty_ordered", "sum"),
        Records=("Revenue", "size")
    )
    .reset_index(names="Year")
)

# Додатково визначаємо частку знижки та середню виручку на один запис.
q2["Discount_Rate_%"] = q2["Discount"] / q2["Gross_Revenue"] * 100
q2["Avg_Revenue_per_Record"] = q2["Revenue"] / q2["Records"]

print("\n2. SALES BY YEAR")
print(q2)

# -----------------------------
# 3. Продажі по місяцях
# -----------------------------

# Групуємо дані за місяцем.
q3 = (
    df.groupby("Month", as_index=False)
    .agg(
        Revenue=("Revenue", "sum"),
        Gross_Revenue=("Gross_Revenue", "sum"),
        Discount=("discount_amount", "sum"),
        Quantity=("qty_ordered", "sum"),
        Records=("Revenue", "size")
    )
)

# Рахуємо частку знижки.
q3["Discount_Rate_%"] = q3["Discount"] / q3["Gross_Revenue"] * 100

# Рахуємо зміну виручки відносно попереднього місяця у відсотках.
q3["MoM_%"] = q3["Revenue"].pct_change() * 100

print("\n3. SALES BY MONTH")
print(q3)

# Виводимо місяць з найбільшою виручкою.
print("\nBest month:")
print(q3.nlargest(1, "Revenue"))

# -----------------------------
# 4. Продажі по регіонах
# -----------------------------

q4 = (
    df.groupby("Region", as_index=False)
    .agg(
        Revenue=("Revenue", "sum"),
        Gross_Revenue=("Gross_Revenue", "sum"),
        Discount=("discount_amount", "sum"),
        Quantity=("qty_ordered", "sum"),
        Records=("Revenue", "size")
    )
)

# Визначаємо частку кожного регіону у загальній виручці.
q4["Share_%"] = q4["Revenue"] / df["Revenue"].sum() * 100

# Визначаємо середню частку знижки у регіоні.
q4["Discount_Rate_%"] = q4["Discount"] / q4["Gross_Revenue"] * 100

# Сортуємо регіони від найбільшої виручки до найменшої.
q4 = q4.sort_values("Revenue", ascending=False)

print("\n4. SALES BY REGION")
print(q4)

# -----------------------------
# 5. Продажі по категоріях
# -----------------------------

q5 = (
    df.groupby("category", as_index=False)
    .agg(
        Revenue=("Revenue", "sum"),
        Gross_Revenue=("Gross_Revenue", "sum"),
        Discount=("discount_amount", "sum"),
        Quantity=("qty_ordered", "sum"),
        Records=("Revenue", "size")
    )
)

# Частка категорії у загальній виручці.
q5["Share_%"] = q5["Revenue"] / df["Revenue"].sum() * 100

# Частка знижок у межах категорії.
q5["Discount_Rate_%"] = q5["Discount"] / q5["Gross_Revenue"] * 100

# Сортуємо категорії за виручкою.
q5 = q5.sort_values("Revenue", ascending=False)

print("\n5. TOP CATEGORIES")
print(q5.head(5))

# -----------------------------
# 6. TOP-3 категорії у кожному регіоні
# -----------------------------

# Спочатку групуємо одночасно за регіоном та категорією.
q6 = (
    df.groupby(["Region", "category"], as_index=False)
    .agg(
        Revenue=("Revenue", "sum"),
        Gross_Revenue=("Gross_Revenue", "sum"),
        Discount=("discount_amount", "sum"),
        Quantity=("qty_ordered", "sum"),
        Records=("Revenue", "size")
    )
)

q6["Discount_Rate_%"] = q6["Discount"] / q6["Gross_Revenue"] * 100

# У кожному регіоні залишаємо три категорії з найбільшою виручкою.
q6 = (
    q6.sort_values(["Region", "Revenue"], ascending=[True, False])
    .groupby("Region", group_keys=False)
    .head(3)
    .reset_index(drop=True)
)

print("\n6. TOP-3 CATEGORIES IN EACH REGION")
print(q6)

# -----------------------------
# 7. Аналіз продажів зі знижкою та без знижки
# -----------------------------

# Створюємо категоріальну ознаку, яка показує,
# чи застосовувалася до продажу знижка.
df["Has_Discount"] = np.where(
    df["discount_amount"] > 0,
    "With discount",
    "Without discount"
)

q7 = (
    df.groupby("Has_Discount", as_index=False)
    .agg(
        Revenue=("Revenue", "sum"),
        Gross_Revenue=("Gross_Revenue", "sum"),
        Discount=("discount_amount", "sum"),
        Quantity=("qty_ordered", "sum"),
        Records=("Revenue", "size"),
        Avg_Revenue=("Revenue", "mean"),
        Avg_Quantity=("qty_ordered", "mean")
    )
)

# Частка виручки кожної групи.
q7["Revenue_Share_%"] = q7["Revenue"] / df["Revenue"].sum() * 100

# Фактичний середній відсоток знижки.
q7["Discount_Rate_%"] = q7["Discount"] / q7["Gross_Revenue"] * 100

print("\n7. DISCOUNT ANALYSIS")
print(q7)

# -----------------------------
# 8. Аналіз продажів за віковими групами
# -----------------------------

# Межі вікових груп.
bins = [17, 24, 34, 44, 54, 64, 200]

# Назви вікових груп.
labels = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]

# Розбиваємо покупців на вікові категорії.
df["Age_Group"] = pd.cut(df["age"], bins=bins, labels=labels)

q8 = (
    df.groupby("Age_Group", observed=True, as_index=False)
    .agg(
        Revenue=("Revenue", "sum"),
        Quantity=("qty_ordered", "sum"),
        Records=("Revenue", "size"),
        Avg_Revenue=("Revenue", "mean"),
        Avg_Discount=("Discount_Rate", "mean")
    )
)

# Частка кожної вікової групи у загальній виручці.
q8["Share_%"] = q8["Revenue"] / df["Revenue"].sum() * 100

# Сортуємо за виручкою.
q8 = q8.sort_values("Revenue", ascending=False)

print("\n8. SALES BY AGE GROUP")
print(q8)

# -----------------------------
# 9. Найкращі комбінації регіон + категорія
# за останні 6 місяців
# -----------------------------

# Знаходимо початкову дату для періоду останніх шести місяців.
start_date = df["Order_Date"].max() - pd.DateOffset(months=5)

# Залишаємо тільки записи за останні шість місяців,
# після чого групуємо їх за регіоном і категорією.
q9 = (
    df.loc[df["Order_Date"] >= start_date]
    .groupby(["Region", "category"], as_index=False)
    .agg(
        Revenue=("Revenue", "sum"),
        Gross_Revenue=("Gross_Revenue", "sum"),
        Discount=("discount_amount", "sum"),
        Quantity=("qty_ordered", "sum"),
        Records=("Revenue", "size"),
        Avg_Revenue=("Revenue", "mean")
    )
)

q9["Discount_Rate_%"] = q9["Discount"] / q9["Gross_Revenue"] * 100

# Залишаємо десять комбінацій з найбільшою виручкою.
q9 = q9.sort_values("Revenue", ascending=False).head(10)

print("\n9. TOP REGION/CATEGORY COMBINATIONS FOR LAST 6 MONTHS")
print("Period:", start_date.strftime("%Y-%m"), "-", df["Order_Date"].max().strftime("%Y-%m"))
print(q9)

# -----------------------------
# 10. Зведена таблиця: місяць x регіон
# -----------------------------

# Створюємо pivot table:
# рядки — місяці,
# колонки — регіони,
# значення — сума Revenue.
q10 = pd.pivot_table(
    df,
    index="Month",
    columns="Region",
    values="Revenue",
    aggfunc="sum",
    fill_value=0
)

# Загальна виручка за кожен місяць.
q10["Total"] = q10.sum(axis=1)

# Зміна виручки відносно попереднього місяця.
q10["MoM_%"] = q10["Total"].pct_change() * 100

print("\n10. MONTH X REGION PIVOT TABLE")
print(q10)


# Profit порахувати неможливо, тому що у наборі даних
# немає собівартості товарів (Cost або COGS).
print("\nPROFIT")
print("Profit cannot be calculated correctly because the dataset contains no Cost/COGS column.")
