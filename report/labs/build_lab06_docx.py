from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "report"
OUTPUT_DOCX = REPORT_DIR / "Отчет_ЛР6.docx"

STUDENT_NAME = "Исаева Зарина Исмайилбековна"
GROUP_NAME = "НКНбд–01–23"
CITY_YEAR = "Москва, 2026"
DISCIPLINE = "Разработка информационно-аналитических систем"
TITLE = "Feature Engineering и хранилища признаков (Feature Store)"


def set_run_font(run, name: str = "Times New Roman", size: float = 14, bold: bool = False, italic: bool = False) -> None:
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic


def set_paragraph_format(paragraph, align=WD_ALIGN_PARAGRAPH.JUSTIFY, first_line_cm: float = 1.25) -> None:
    paragraph.alignment = align
    fmt = paragraph.paragraph_format
    fmt.first_line_indent = Cm(first_line_cm) if first_line_cm else None
    fmt.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    fmt.space_after = Pt(0)
    fmt.space_before = Pt(0)


def set_document_styles(document: Document) -> None:
    section = document.sections[0]
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(3)
    section.right_margin = Cm(1.5)

    normal = document.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal.font.size = Pt(14)


def add_paragraph(document: Document, text: str, *, bold: bool = False, italic: bool = False, align=WD_ALIGN_PARAGRAPH.JUSTIFY, first_line_cm: float = 1.25, size: float = 14) -> None:
    paragraph = document.add_paragraph()
    set_paragraph_format(paragraph, align=align, first_line_cm=first_line_cm)
    run = paragraph.add_run(text)
    set_run_font(run, size=size, bold=bold, italic=italic)


def add_heading(document: Document, text: str, level: int = 1) -> None:
    paragraph = document.add_paragraph()
    set_paragraph_format(paragraph, align=WD_ALIGN_PARAGRAPH.LEFT, first_line_cm=0)
    run = paragraph.add_run(text)
    set_run_font(run, size=16 if level == 1 else 14, bold=True)


def add_code(document: Document, code: str) -> None:
    paragraph = document.add_paragraph()
    set_paragraph_format(paragraph, align=WD_ALIGN_PARAGRAPH.LEFT, first_line_cm=0)
    for line in code.strip("\n").splitlines():
        run = paragraph.add_run(line)
        set_run_font(run, name="Courier New", size=9.5)
        run.add_break()


def add_table(document: Document, headers: list[str], rows: list[list[str]]) -> None:
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for idx, header in enumerate(headers):
        cell = table.rows[0].cells[idx]
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(header)
        set_run_font(r, size=11, bold=True)
    for row in rows:
        cells = table.add_row().cells
        for idx, value in enumerate(row):
            cells[idx].text = ""
            p = cells[idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(value)
            set_run_font(r, size=10)
    document.add_paragraph()


def add_title_page(document: Document) -> None:
    lines = [
        "МИНИСТЕРСТВО НАУКИ И ВЫСШЕГО ОБРАЗОВАНИЯ",
        "РОССИЙСКОЙ ФЕДЕРАЦИИ",
        "Федеральное государственное автономное",
        "образовательное учреждение высшего образования",
        "«РОССИЙСКИЙ УНИВЕРСИТЕТ ДРУЖБЫ НАРОДОВ»",
        "Факультет физико-математических и естественных наук",
        "Кафедра математического моделирования и искусственного интеллекта",
    ]
    for line in lines:
        add_paragraph(document, line, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_cm=0, size=13)

    for _ in range(6):
        document.add_paragraph()

    add_paragraph(document, "ОТЧЁТ", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_cm=0, size=16)
    add_paragraph(document, "по лабораторной работе №6", align=WD_ALIGN_PARAGRAPH.CENTER, first_line_cm=0)
    add_paragraph(document, f"«{TITLE}»", align=WD_ALIGN_PARAGRAPH.CENTER, first_line_cm=0)
    add_paragraph(document, f"по дисциплине «{DISCIPLINE}»", align=WD_ALIGN_PARAGRAPH.CENTER, first_line_cm=0)

    for _ in range(8):
        document.add_paragraph()

    add_paragraph(
        document,
        f"Выполнила: {STUDENT_NAME}\nГруппа: {GROUP_NAME}",
        align=WD_ALIGN_PARAGRAPH.RIGHT,
        first_line_cm=0,
    )

    for _ in range(6):
        document.add_paragraph()

    add_paragraph(document, CITY_YEAR, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_cm=0)
    document.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def add_contents(document: Document) -> None:
    add_heading(document, "Содержание", 1)
    items = [
        "1. Цель работы",
        "2. Теоретические сведения",
        "3. Ход выполнения работы",
        "4. Ответы на контрольные вопросы",
        "5. Вывод",
        "6. Список литературы",
    ]
    for item in items:
        add_paragraph(document, item, first_line_cm=0)
    document.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def build_document() -> Document:
    document = Document()
    set_document_styles(document)
    add_title_page(document)
    add_contents(document)

    add_heading(document, "1. Цель работы", 1)
    add_paragraph(
        document,
        "Изучить основные подходы к инженерии признаков, освоить базовые возможности хранилища признаков Feast и показать, как признаки определяются, регистрируются, материализуются и затем используются и в обучении модели, и в онлайн-инференсе.",
    )

    add_heading(document, "2. Теоретические сведения", 1)
    add_paragraph(
        document,
        "Feature Engineering представляет собой процесс преобразования сырых данных в более информативные признаки. На практике он включает создание новых производных характеристик, нормализацию числовых полей, кодирование категориальных значений, обработку пропусков, устранение выбросов и выбор наиболее полезных признаков для конкретной модели.",
    )
    add_paragraph(
        document,
        "Feature Store нужен для того, чтобы одни и те же признаки использовались одинаково в разных сценариях. Он хранит определения признаков, связывает их с источниками данных, обеспечивает повторное использование и уменьшает риск ситуации, когда обучение модели и боевой инференс используют несовместимые расчёты.",
    )
    add_paragraph(
        document,
        "В работе используется Feast. Для корректного вызова historical retrieval в отчёте в набор данных добавлена колонка event_timestamp. Это небольшое уточнение делает пример технически согласованным: в реальном Feast исторические признаки обычно извлекаются именно по данным с временной меткой.",
    )

    add_heading(document, "3. Ход выполнения работы", 1)

    add_heading(document, "3.1. Подготовка окружения", 2)
    add_paragraph(
        document,
        "Для выполнения лабораторной работы требуется установить Feast и библиотеки для подготовки данных, обучения модели и публикации простого API.",
    )
    add_code(
        document,
        """
pip install feast pandas numpy scikit-learn fastapi uvicorn
mkdir lab06_feature_store
cd lab06_feature_store
        """,
    )
    add_paragraph(
        document,
        "Далее создаётся каталог с входными CSV-файлами и инициализируется репозиторий Feast. В документе ниже показан один из возможных рабочих вариантов структуры проекта.",
    )

    add_heading(document, "3.2. Подготовка данных", 2)
    add_paragraph(
        document,
        "В качестве исходных данных используется учебный датасет кредитного скоринга. Дополнительно заранее вычисляются два engineered-признака: debt_to_income_ratio и credit_score_per_age. Такой подход допустим в самой формулировке задания и снижает зависимость от различий API On-Demand Feature View в разных версиях Feast.",
    )
    add_code(
        document,
        """
import pandas as pd

data = pd.DataFrame({
    "customer_id": [1, 2, 3, 4, 5],
    "event_timestamp": pd.to_datetime([
        "2026-04-20", "2026-04-21", "2026-04-22", "2026-04-23", "2026-04-24"
    ]),
    "age": [25, 45, 35, 50, 23],
    "income": [50000, 100000, 75000, 120000, 40000],
    "credit_score": [650, 720, 680, 700, 620],
    "loan_amount": [10000, 20000, 15000, 25000, 5000],
    "default": [0, 0, 1, 0, 1],
})

data["debt_to_income_ratio"] = data["loan_amount"] / data["income"]
data["credit_score_per_age"] = data["credit_score"] / data["age"]
data.to_csv("data.csv", index=False)

data_v2 = data.copy()
data_v2["income_k"] = data_v2["income"] / 1000
data_v2.to_csv("data_v2.csv", index=False)
        """,
    )
    add_paragraph(document, "Фрагмент подготовленного набора данных приведён в таблице 1.")
    add_table(
        document,
        headers=[
            "customer_id",
            "age",
            "income",
            "credit_score",
            "loan_amount",
            "default",
            "debt_to_income_ratio",
            "credit_score_per_age",
        ],
        rows=[
            ["1", "25", "50000", "650", "10000", "0", "0.2000", "26.00"],
            ["2", "45", "100000", "720", "20000", "0", "0.2000", "16.00"],
            ["3", "35", "75000", "680", "15000", "1", "0.2000", "19.43"],
            ["4", "50", "120000", "700", "25000", "0", "0.2083", "14.00"],
            ["5", "23", "40000", "620", "5000", "1", "0.1250", "26.96"],
        ],
    )

    add_heading(document, "3.3. Инициализация репозитория Feast", 2)
    add_paragraph(
        document,
        "После подготовки данных создаётся feature repository. Внутри него хранятся файл конфигурации, онлайн-хранилище и Python-описания сущностей, источников и feature views.",
    )
    add_code(
        document,
        """
feast init feature_repo
cd feature_repo
        """,
    )
    add_paragraph(
        document,
        "Файл example.py из шаблона очищается и заменяется собственными определениями. В отчёте используется современный стиль Feast с объектами Field. Если установлена старая версия, их может потребоваться заменить на Feature, но логика описания признаков остаётся той же.",
    )

    add_heading(document, "3.4. Определение сущности, источников и Feature View", 2)
    add_code(
        document,
        """
from datetime import timedelta
from feast import Entity, FeatureView, Field, FileSource
from feast.types import Float32, Int64

customer_source = FileSource(
    name="customer_source",
    path="../data.csv",
    event_timestamp_column="event_timestamp",
)

customer_source_v2 = FileSource(
    name="customer_source_v2",
    path="../data_v2.csv",
    event_timestamp_column="event_timestamp",
)

customer_id = Entity(
    name="customer_id",
    join_keys=["customer_id"],
    description="Идентификатор клиента",
)

customer_features = FeatureView(
    name="customer_features",
    entities=[customer_id],
    ttl=timedelta(days=3650),
    schema=[
        Field(name="age", dtype=Int64),
        Field(name="income", dtype=Int64),
        Field(name="credit_score", dtype=Int64),
        Field(name="loan_amount", dtype=Int64),
        Field(name="debt_to_income_ratio", dtype=Float32),
        Field(name="credit_score_per_age", dtype=Float32),
    ],
    online=True,
    source=customer_source,
)

customer_features_v2 = FeatureView(
    name="customer_features_v2",
    entities=[customer_id],
    ttl=timedelta(days=3650),
    schema=[
        Field(name="age", dtype=Int64),
        Field(name="income_k", dtype=Float32),
        Field(name="credit_score", dtype=Int64),
        Field(name="loan_amount", dtype=Int64),
        Field(name="debt_to_income_ratio", dtype=Float32),
        Field(name="credit_score_per_age", dtype=Float32),
    ],
    online=True,
    source=customer_source_v2,
)
        """,
    )
    add_paragraph(
        document,
        "В первой версии хранятся исходные признаки и два вычисленных признака. Во второй версии показан простой сценарий версионирования: доход масштабируется в тысячи рублей и публикуется в отдельной feature view с суффиксом _v2.",
    )

    add_heading(document, "3.5. Регистрация определений и materialization", 2)
    add_paragraph(
        document,
        "После описания сущностей и feature views они регистрируются в репозитории. Затем признаки материализуются в онлайн-хранилище. В отчёте используется абсолютная дата 2026-04-27.",
    )
    add_code(
        document,
        """
feast apply
feast materialize-incremental 2026-04-27
        """,
    )
    add_paragraph(
        document,
        "Команда apply создаёт или обновляет метаданные признаков, а materialize-incremental переносит значения признаков в онлайн-хранилище. После этого они доступны для быстрых запросов в режиме инференса.",
    )

    add_heading(document, "3.6. Извлечение исторических признаков и обучение модели", 2)
    add_paragraph(
        document,
        "Исторические признаки извлекаются для задач обучения. В entity dataframe сохраняются ключ сущности, timestamp и целевая переменная default. Далее полученный набор признаков подаётся на простую модель логистической регрессии.",
    )
    add_code(
        document,
        """
import pandas as pd
from feast import FeatureStore
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

store = FeatureStore(repo_path=".")

entity_df = pd.read_csv("../data.csv", parse_dates=["event_timestamp"])[
    ["customer_id", "event_timestamp", "default"]
]

training_df = store.get_historical_features(
    entity_df=entity_df,
    features=[
        "customer_features:age",
        "customer_features:income",
        "customer_features:credit_score",
        "customer_features:debt_to_income_ratio",
        "customer_features:credit_score_per_age",
    ],
).to_df()

X = training_df[
    ["age", "income", "credit_score", "debt_to_income_ratio", "credit_score_per_age"]
]
y = training_df["default"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))
        """,
    )
    add_paragraph(
        document,
        "На миниатюрном наборе из пяти строк метрика accuracy носит исключительно демонстрационный характер. Для осмысленного качества модели желательно использовать расширенный синтетический или реальный датасет, но сам рабочий процесс получения признаков для обучения показан корректно.",
    )

    add_heading(document, "3.7. Получение онлайн-признаков и интеграция с FastAPI", 2)
    add_paragraph(
        document,
        "Онлайн-запрос получает материализованные признаки по customer_id. Ниже приведены пример вызова через Feast и минимальный FastAPI endpoint, который может быть использован в сервисе скоринга.",
    )
    add_code(
        document,
        """
from feast import FeatureStore

store = FeatureStore(repo_path=".")

online_features = store.get_online_features(
    features=[
        "customer_features:age",
        "customer_features:income",
        "customer_features:credit_score",
        "customer_features:debt_to_income_ratio",
        "customer_features:credit_score_per_age",
    ],
    entity_rows=[{"customer_id": 2}],
).to_dict()

print(online_features)
        """,
    )
    add_paragraph(
        document,
        "Для клиента с идентификатором 2 ожидаемый словарь содержит возраст 45 лет, доход 100000, кредитный рейтинг 720, отношение кредита к доходу 0.2 и признак credit_score_per_age, равный 16.0.",
    )
    add_code(
        document,
        """
from fastapi import FastAPI, HTTPException
from feast import FeatureStore

app = FastAPI(title="Feature Store API")
store = FeatureStore(repo_path="feature_repo")

FEATURES_V1 = [
    "customer_features:age",
    "customer_features:income",
    "customer_features:credit_score",
    "customer_features:debt_to_income_ratio",
    "customer_features:credit_score_per_age",
]

FEATURES_V2 = [
    "customer_features_v2:age",
    "customer_features_v2:income_k",
    "customer_features_v2:credit_score",
    "customer_features_v2:debt_to_income_ratio",
    "customer_features_v2:credit_score_per_age",
]

@app.get("/features/{customer_id}")
def get_features(customer_id: int, version: str = "v1"):
    if version == "v1":
        features = FEATURES_V1
    elif version == "v2":
        features = FEATURES_V2
    else:
        raise HTTPException(status_code=400, detail="Unknown feature version")

    result = store.get_online_features(
        features=features,
        entity_rows=[{"customer_id": customer_id}],
    ).to_dict()

    return {"customer_id": customer_id, "version": version, "features": result}
        """,
    )

    add_heading(document, "3.8. Версионирование признаков", 2)
    add_paragraph(
        document,
        "Версионирование в Feast обычно организуется через новые feature views, иные схемы или новые источники данных. В данной работе создана customer_features_v2, где поле income представлено как income_k, то есть в тысячах рублей. Такой подход позволяет хранить рядом старую и новую логику расчёта и не ломать существующие модели.",
    )
    add_paragraph(
        document,
        "Проверка доступности обеих версий сводится к выполнению apply и последующему запросу признаков как из customer_features, так и из customer_features_v2. В результате одна и та же сущность customer_id может обслуживаться двумя наборами признаков одновременно.",
    )

    add_heading(document, "3.9. Использование другого источника данных", 2)
    add_paragraph(
        document,
        "Для более реалистичного эксперимента удобно сгенерировать увеличенный синтетический набор, например на 10000 клиентов. Он может использоваться и для тренировки модели, и для сравнения времени извлечения признаков.",
    )
    add_code(
        document,
        """
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
n = 10000

large = pd.DataFrame({
    "customer_id": np.arange(1, n + 1),
    "event_timestamp": pd.Timestamp("2026-04-27"),
    "age": rng.integers(21, 66, size=n),
    "income": rng.integers(35000, 200001, size=n),
    "credit_score": rng.integers(550, 851, size=n),
    "loan_amount": rng.integers(2000, 60001, size=n),
})

large["debt_to_income_ratio"] = large["loan_amount"] / large["income"]
large["credit_score_per_age"] = large["credit_score"] / large["age"]
large["default"] = (
    (large["debt_to_income_ratio"] > 0.45) | (large["credit_score"] < 620)
).astype(int)

large.to_csv("bank_customers_large.csv", index=False)
        """,
    )
    add_paragraph(
        document,
        "Этот файл можно подключить через отдельный FileSource и отдельный FeatureView. В учебной работе такой синтетический источник предпочтительнее случайной загрузки внешнего набора, потому что он полностью воспроизводим и не зависит от доступа к сторонним сайтам.",
    )

    add_heading(document, "3.10. Сравнение производительности", 2)
    add_paragraph(
        document,
        "Сравнение времени извлечения признаков для 1000 клиентов выполняется двумя способами: через get_online_features и через прямое чтение CSV. Код измерения приведён ниже.",
    )
    add_code(
        document,
        """
import time
import pandas as pd
from feast import FeatureStore

store = FeatureStore(repo_path="feature_repo")
ids = [{"customer_id": i} for i in range(1, 1001)]

start = time.perf_counter()
store.get_online_features(
    features=[
        "customer_features:age",
        "customer_features:income",
        "customer_features:credit_score",
        "customer_features:debt_to_income_ratio",
        "customer_features:credit_score_per_age",
    ],
    entity_rows=ids,
).to_dict()
feast_time = time.perf_counter() - start

start = time.perf_counter()
csv_df = pd.read_csv("../bank_customers_large.csv")
csv_result = csv_df[csv_df["customer_id"].isin(range(1, 1001))]
csv_time = time.perf_counter() - start

print("Feast online:", feast_time)
print("Direct CSV:", csv_time)
        """,
    )
    add_paragraph(
        document,
        "Численные значения зависят от оборудования, объёма данных, способа прогрева кэша и версии Feast, поэтому в отчёте принципиальнее не абсолютные миллисекунды, а интерпретация результата. В типичном сервисном сценарии online store выигрывает на повторяющихся запросах, так как работает с уже материализованными значениями по ключу сущности и не тратит время на повторный разбор всего CSV-файла.",
    )
    add_table(
        document,
        headers=["Подход", "Особенность", "Практический вывод"],
        rows=[
            [
                "get_online_features",
                "Обращение к онлайн-хранилищу по ключу",
                "Подходит для инференса и сервисов с низкой задержкой",
            ],
            [
                "Прямое чтение CSV",
                "Требует чтения файла и парсинга данных",
                "Удобно для офлайн-анализа, но хуже как production endpoint",
            ],
            [
                "CSV в памяти",
                "Может быть быстрым на игрушечных примерах",
                "Не решает задачи согласованности и версионирования признаков",
            ],
        ],
    )

    add_heading(document, "4. Ответы на контрольные вопросы", 1)
    add_heading(document, "4.1. Что такое feature store и какие проблемы он решает?", 2)
    add_paragraph(
        document,
        "Feature store — это централизованный слой управления признаками, который хранит определения признаков, их источники, схемы и способы извлечения. Он решает проблемы дублирования логики, расхождения между обучением и инференсом, слабой воспроизводимости экспериментов и сложности повторного использования признаков в нескольких моделях.",
    )
    add_heading(document, "4.2. В чём разница между материализованными и on-demand признаками?", 2)
    add_paragraph(
        document,
        "Материализованные признаки вычисляются заранее и сохраняются в офлайн- или онлайн-хранилище. On-demand признаки вычисляются в момент запроса из уже известных признаков или входных параметров запроса. Первые обычно быстрее на инференсе, вторые удобны при частой смене формулы и при желании не хранить производный признак физически.",
    )
    add_heading(document, "4.3. Как обеспечивается согласованность признаков между обучением и инференсом?", 2)
    add_paragraph(
        document,
        "Согласованность достигается тем, что и обучение, и онлайн-сервис обращаются к одному и тому же определению признаков в feature repository. Логика извлечения, типы полей, ключи сущностей и названия признаков описываются централизованно, поэтому риск случайно переопределить расчёт в production-коде заметно снижается.",
    )
    add_heading(document, "4.4. Какие преимущества даёт feature store при работе с большим количеством моделей?", 2)
    add_paragraph(
        document,
        "При большом количестве моделей feature store даёт повторное использование уже подготовленных признаков, экономит время на поддержке конвейеров, облегчает аудит изменений и упрощает внедрение новых моделей. Команды получают единый каталог признаков и могут быстрее находить готовые компоненты, а не пересчитывать одни и те же характеристики заново.",
    )
    add_heading(document, "4.5. Как можно организовать версионирование признаков в Feast?", 2)
    add_paragraph(
        document,
        "Версионирование обычно организуют через создание новых feature views или новых источников с изменённой схемой, например customer_features_v2. Дополнительно можно использовать теги, отдельные имена полей и явные версии в коде моделей. Такой подход позволяет постепенно переводить сервисы на новую схему без разрушения старой.",
    )

    add_heading(document, "5. Вывод", 1)
    add_paragraph(
        document,
        "В лабораторной работе рассмотрены базовые элементы инженерии признаков и показано, как концепция feature store упорядочивает работу с признаками в ML-проекте. На примере Feast были описаны источники данных, сущность клиента, две версии feature views, этап materialization, извлечение исторических признаков для обучения и получение онлайн-признаков для инференса.",
    )
    add_paragraph(
        document,
        "Ключевой практический результат состоит в том, что признаки становятся не разрозненным кодом внутри отдельных ноутбуков, а управляемым артефактом с единым определением, что особенно важно при росте числа моделей, сервисов и команд разработки.",
    )

    add_heading(document, "6. Список литературы", 1)
    add_paragraph(document, "1. Feast Documentation. URL: https://docs.feast.dev", first_line_cm=0)
    add_paragraph(document, "2. Eugene Yan et al. Feature Stores for Machine Learning. O’Reilly Media.", first_line_cm=0)
    add_paragraph(document, "3. Scikit-learn Documentation. URL: https://scikit-learn.org", first_line_cm=0)
    add_paragraph(document, "4. Burkov A. Machine Learning Engineering.", first_line_cm=0)

    return document


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    document = build_document()
    document.save(OUTPUT_DOCX)


if __name__ == "__main__":
    main()
