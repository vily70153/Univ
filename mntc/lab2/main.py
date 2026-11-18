
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import ipywidgets as widgets
from IPython.display import display

url = "https://raw.githubusercontent.com/plotly/datasets/master/gapminderDataFiveYear.csv"
df_raw = pd.read_csv(url)

#     загальний огляд отриманої інформації      #
print("рядків і колонок:", df_raw.shape)
display(df_raw.head())

#            огляд отриманого датафрейма, визначення типів           #
df_raw.info()
display(df_raw.describe().T)
print("пропуски:")
print(df_raw.isna().sum())
print("повні дублікати:", df_raw.duplicated().sum())
print("країн:", df_raw["country"].nunique())
print("континенти:", df_raw["continent"].unique())
print("роки:", sorted(df_raw["year"].unique()))

# %%
df = df_raw.copy()
rows_before = len(df)   # для перевірки скіоки рядків залишилось після очищення

# очистка тексту у текстових полях на пробіли чи пусті значення
for column in ["country", "continent"]:
    df[column] = df[column].str.strip()
    df[column] = df[column].replace("", pd.NA)

# перетворення текстових полів на числовв
for column in ["year", "pop", "lifeExp", "gdpPercap"]:
    df[column] = pd.to_numeric(df[column], errors="coerce")


# і повна очистка рядків де є хоча б 1 пропуск у полі
df = df.dropna()
df = df.drop_duplicates()

# фінальна очистка від зайвих результатів. очистка проводиться за умовами типу населення не може бути 
# відʼємнимм і тд
df = df[
    (df["pop"] > 0)
    & (df["pop"] % 1 == 0)
    & (df["year"] % 1 == 0)
    & (df["gdpPercap"] > 0)
    & df["lifeExp"].between(0, 120, inclusive="neither")
    & df["continent"].isin(["Africa", "Americas", "Asia", "Europe", "Oceania"])
].copy()

# різні записи однієї країни за один рік потребують окремого розгляду.
if df.duplicated(["country", "year"]).any():
    raise ValueError("є суперечливі записи країна-рік")

print("рядків до очищення:", rows_before)
print("рядків після очищення:", len(df))
print("пропусків залишилось:", df.isna().sum().sum())

# перетворення даних у потрібні типи для подальшої роботи. датафрейм буде використовуватись для побудови графіків та таблиць.
df["year"] = df["year"].astype(int)
df["pop"] = df["pop"].astype(int)
df["date"] = pd.to_datetime(df["year"].astype(str), format="%Y")



# допоміжний добуток для зваженого середнього.

df["gdp_total"] = df["gdpPercap"] * df["pop"] # загальний ввп країни
df["life_weighted_sum"] = df["lifeExp"] * df["pop"] # зважена тривалість життя країни
df = df.sort_values(["year", "continent", "country"])
display(df.head())

# таблиця для аналізу даних за роками. зважені середні по населенню та медіани по країнах.
by_year = df.groupby("year").agg(
    population=("pop", "sum"),
    gdp_total=("gdp_total", "sum"),
    life_sum=("life_weighted_sum", "sum"),
    country_count=("country", "nunique"),
    life_median=("lifeExp", "median")
).reset_index()

by_year["life_weighted"] = by_year["life_sum"] / by_year["population"]
by_year["gdp_per_capita_weighted"] = by_year["gdp_total"] / by_year["population"]
by_year = by_year.drop(columns="life_sum")
display(by_year.round(2))

# таблиця для аналізу даних за роками та континентами. зважені середні по населенню та медіани по країнах.
by_continent_year = df.groupby(["year", "continent"]).agg(
    population=("pop", "sum"),
    gdp_total=("gdp_total", "sum"),
    life_sum=("life_weighted_sum", "sum"),
    country_count=("country", "nunique"),
    life_median=("lifeExp", "median")
).reset_index()

by_continent_year["life_weighted"] = by_continent_year["life_sum"] / by_continent_year["population"]
by_continent_year["gdp_per_capita_weighted"] = by_continent_year["gdp_total"] / by_continent_year["population"]
by_continent_year = by_continent_year.drop(columns="life_sum")
display(by_continent_year[by_continent_year["year"] == 2007].round(2))


by_country = df[df["year"] == 2007].copy()
by_country["population_share_pct"] = by_country["pop"] / by_country["pop"].sum() * 100

top_countries = by_country.sort_values("gdpPercap", ascending=False)
display(top_countries[["country", "continent", "pop", "lifeExp", "gdpPercap", "population_share_pct"]].head(10).round(2))


matrix = by_continent_year.pivot(
    index="continent",
    columns="year",
    values="life_weighted"
)
display(matrix.round(2))


selected = by_country
history_table = by_continent_year


fig = px.line(
    history_table, x="year", y="life_weighted",
    color="continent", markers=True,
    title="динаміка зваженої тривалості життя",
    labels={"year": "рік", "life_weighted": "тривалість життя, років", "continent": "континент"}
)
fig.show(renderer="colab")


fig = px.scatter(
    selected, x="gdpPercap", y="lifeExp",
    color="continent", size="pop", hover_name="country",
    log_x=True, size_max=55,
    title="ввп на особу та тривалість життя",
    labels={"gdpPercap": "ввп на особу, дол. сша", "lifeExp": "тривалість життя, років"}
)
fig.show(renderer="colab")


fig = px.treemap(
    selected, path=["continent", "country"],
    values="pop", color="lifeExp",
    color_continuous_scale="Teal", range_color=[20, 85],
    title="структура населення"
)
fig.show(renderer="colab")


matrix = history_table.pivot(index="continent", columns="year", values="life_weighted")
fig = px.imshow(
    matrix, aspect="auto", color_continuous_scale="Teal",
    zmin=20, zmax=85,
    labels={"x": "рік", "y": "континент", "color": "років"},
    title="тривалість життя за роками й континентами"
)
fig.show(renderer="colab")


fig = px.box(
    selected, x="continent", y="gdpPercap",
    color="continent", points="all", hover_name="country",
    log_y=True, title="розподіл ввп на особу",
    labels={"continent": "континент", "gdpPercap": "ввп на особу, дол. сша"}
)
fig.show(renderer="colab")


def dashboard(year=2007, continent="усі"):
    data = df.copy()
    if continent != "усі":
        data = data[data["continent"] == continent]

    selected = data[data["year"] == year]
    population = selected["pop"].sum()
    life = selected["life_weighted_sum"].sum() / population
    gdp = selected["gdp_total"].sum() / population

    # чотири картки з основними показниками.
    cards = go.Figure()
    cards.add_trace(go.Indicator(mode="number", value=len(selected), title={"text": "країн"}, domain={"x": [0, 0.22], "y": [0, 1]}))
    cards.add_trace(go.Indicator(mode="number", value=population / 1e9, number={"valueformat": ".3f"}, title={"text": "населення, млрд"}, domain={"x": [0.26, 0.48], "y": [0, 1]}))
    cards.add_trace(go.Indicator(mode="number", value=life, number={"valueformat": ".2f"}, title={"text": "тривалість життя, років"}, domain={"x": [0.52, 0.74], "y": [0, 1]}))
    cards.add_trace(go.Indicator(mode="number", value=gdp, number={"valueformat": ".0f"}, title={"text": "ввп на особу, дол. сша"}, domain={"x": [0.78, 1], "y": [0, 1]}))
    cards.update_layout(height=220, margin={"l": 20, "r": 20, "t": 60, "b": 20})
    cards.show(renderer="colab")
    print("середні зважені населенням; показники стосуються обраних країн")

    history_table = data.groupby(["year", "continent"]).agg(
        population=("pop", "sum"),
        life_sum=("life_weighted_sum", "sum")
    ).reset_index()
    history_table["life_weighted"] = history_table["life_sum"] / history_table["population"]

    fig = px.line(
        history_table, x="year", y="life_weighted",
        color="continent", markers=True,
        title="динаміка зваженої тривалості життя",
        labels={"year": "рік", "life_weighted": "тривалість життя, років", "continent": "континент"}
    )
    fig.show(renderer="colab")

    fig = px.scatter(
        selected, x="gdpPercap", y="lifeExp",
        color="continent", size="pop", hover_name="country",
        log_x=True, size_max=55,
        title="ввп на особу та тривалість життя",
        labels={"gdpPercap": "ввп на особу, дол. сша", "lifeExp": "тривалість життя, років"}
    )
    fig.show(renderer="colab")

    fig = px.treemap(
        selected, path=["continent", "country"],
        values="pop", color="lifeExp",
        color_continuous_scale="Teal", range_color=[20, 85],
        title="структура населення"
    )
    fig.show(renderer="colab")

    matrix = history_table.pivot(index="continent", columns="year", values="life_weighted")
    fig = px.imshow(
        matrix, aspect="auto", color_continuous_scale="Teal",
        zmin=20, zmax=85,
        labels={"x": "рік", "y": "континент", "color": "років"},
        title="тривалість життя за роками й континентами"
    )
    fig.show(renderer="colab")

    fig = px.box(
        selected, x="continent", y="gdpPercap",
        color="continent", points="all", hover_name="country",
        log_y=True, title="розподіл ввп на особу",
        labels={"continent": "континент", "gdpPercap": "ввп на особу, дол. сша"}
    )
    fig.show(renderer="colab")

    display(selected[["country", "continent", "pop", "lifeExp", "gdpPercap"]].sort_values("gdpPercap", ascending=False).head(10).round(2))

widgets.interact(
    dashboard,
    year=sorted(df["year"].unique().tolist()),
    continent=["усі"] + sorted(df["continent"].unique().tolist())
);

annual = by_year.set_index('year')
regions = by_continent_year.query('year == 2007').set_index('continent')
latest = df.query('year == 2007')
findings = pd.Series({
    'тривалість життя у 1952': annual.loc[1952,'life_weighted'],
    'тривалість життя у 2007': annual.loc[2007,'life_weighted'],
    'зміна, років': annual.loc[2007,'life_weighted']-annual.loc[1952,'life_weighted'],
    'європа у 2007': regions.loc['Europe','life_weighted'],
    'африка у 2007': regions.loc['Africa','life_weighted'],
    'розрив європа-африка, років': regions.loc['Europe','life_weighted']-regions.loc['Africa','life_weighted'],
    'кореляція log10 ввп і тривалості життя': np.corrcoef(np.log10(latest.gdpPercap),latest.lifeExp)[0,1],
    'частка азії у населенні вибірки, %': regions.loc['Asia','population']/latest['pop'].sum()*100,
})
display(findings.round(3))


df.to_csv("gapminder_clean.csv", index=False)
by_year.to_csv("by_year.csv", index=False)
by_continent_year.to_csv("by_continent_year.csv", index=False)
by_country.to_csv("countries_2007.csv", index=False)
print("чотири csv-файли збережено")
