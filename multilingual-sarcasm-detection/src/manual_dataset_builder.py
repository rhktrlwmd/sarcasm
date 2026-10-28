from __future__ import annotations

import itertools
import random
from pathlib import Path

import pandas as pd

from src.config import PROJECT_ROOT

MANUAL_DATASET_PATH = PROJECT_ROOT / "data" / "raw" / "real" / "manual_ru_conversational_reddit.csv"


def _deduplicate_candidates(candidates: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for candidate in candidates:
        normalized = " ".join(candidate.split())
        if normalized not in seen:
            seen.add(normalized)
            unique.append(normalized)
    return unique


def _build_sarcastic_candidates() -> list[str]:
    positive_openers = [
        "Ну конечно",
        "Прекрасно",
        "Замечательно",
        "Какое счастье",
        "Спасибо большое",
        "О да",
        "Вау",
        "Ага, отлично",
        "Просто великолепно",
        "Вот это сервис",
    ]
    annoying_events = [
        "снова завис компьютер",
        "опять не работает лифт",
        "интернет пропал во время звонка",
        "автобус уехал прямо передо мной",
        "мне поставили дедлайн на вечер пятницы",
        "принтер зажевал документ перед сдачей",
        "мне назначили ещё одно бесполезное совещание",
        "поезд отменили за десять минут до отправления",
        "телефон сел в самый нужный момент",
        "ответ на письмо пришёл через неделю",
        "таблица сломалась перед отчётом",
        "пропускная система зависла утром",
        "коллега опять прислал правки ночью",
        "доставка опоздала на три часа",
        "в очереди пришлось стоять полдня",
        "обновление сломало то, что раньше работало",
        "будильник не сработал в день экзамена",
        "начальник вспомнил о срочной задаче в 18:55",
        "мне снова дали задачу без вводных",
        "документ исчез прямо перед отправкой",
    ]
    end_clauses = [
        "именно этого мне сегодня и не хватало.",
        "это прям мечта, а не день.",
        "лучше уже просто не придумать.",
        "всё как я люблю.",
        "спасибо, без этого день был бы слишком спокойным.",
        "очень вовремя, просто идеально.",
        "я как раз на это и рассчитывал.",
        "без этого счастья мне было бы скучно.",
        "вот теперь день точно удался.",
        "ещё бы немного удобства, и было бы слишком хорошо.",
    ]
    sarcastic_gratitude_events = [
        "ответил только через неделю",
        "перенёс встречу за пять минут до начала",
        "сказал об изменениях в последний момент",
        "оставил меня разбираться с этим одному",
        "прислал пустой файл вместо финальной версии",
        "напомнил об этом уже после дедлайна",
        "сломал настройки и молча ушёл",
        "снова всё перепутал в таблице",
        "принёс правки ночью",
        "включил музыку, пока я был на звонке",
    ]
    sarcastic_gratitude_outcomes = [
        "я вообще никуда не торопился.",
        "мне как раз нечем было заняться.",
        "теперь всё стало только лучше.",
        "без этого я бы точно справился быстрее, а так интереснее.",
        "идеальный тайминг, конечно.",
        "вот именно такого сюрприза мне и хотелось.",
    ]
    praise_templates = [
        "Вау, ты ТАКОЙ {trait}, {ending}.",
        "Ну конечно, ты у нас ТАКОЙ {trait}, {ending}.",
        "Да-да, ты просто {trait}, {ending}.",
        "ОЧЕНЬ {trait}, особенно {ending}.",
    ]
    praise_traits = [
        "умный",
        "внимательный",
        "организованный",
        "пунктуальный",
        "полезный",
        "гениальный",
        "предусмотрительный",
        "аккуратный",
        "ответственный",
        "компетентный",
    ]
    praise_endings = [
        "сам бы я никогда не заметил очевидную ошибку",
        "после такого совета мы точно спасены",
        "нам всем остаётся только записывать за тобой",
        "ещё бы немного таланта, и мы бы не пережили",
        "теперь всё стало куда понятнее, конечно",
        "после этого решения вопросов точно не осталось",
        "я поражён глубиной этого подхода",
        "теперь команда точно знает, как не надо делать",
    ]
    caps_patterns = [
        "Это ТАК интересно, что хочется закрыть ноутбук и уйти.",
        "Я ТАК рада, что мне снова всё прислали без контекста.",
        "Это ОЧЕНЬ полезный совет, особенно сейчас.",
        "Мне ТАК нравится, когда планы меняют в последний момент.",
        "Я ПРОСТО в восторге от этой очереди на сорок минут.",
        "Как ЖЕ я люблю, когда звонят без предупреждения.",
        "Это ТАК удобно, когда пароль снова не подходит.",
        "ОЧЕНЬ вовремя отключили свет, спасибо.",
    ]

    candidates: list[str] = []
    for opener, event, clause in itertools.product(positive_openers, annoying_events, end_clauses):
        candidates.append(f"{opener}, {event}, {clause}")

    for event, outcome in itertools.product(sarcastic_gratitude_events, sarcastic_gratitude_outcomes):
        candidates.append(f"Спасибо, что {event}, {outcome}")

    for template, trait, ending in itertools.product(praise_templates, praise_traits, praise_endings):
        candidates.append(template.format(trait=trait, ending=ending))

    candidates.extend(caps_patterns)
    return _deduplicate_candidates(candidates)


def _build_non_sarcastic_candidates() -> list[str]:
    good_events = [
        "мы успели закончить проект вовремя",
        "ты приехал вовремя",
        "команда быстро закрыла задачу",
        "преподаватель подробно объяснил тему",
        "мне прислали все материалы заранее",
        "встреча оказалась короткой и полезной",
        "погода сегодня действительно хорошая",
        "поезд пришёл без задержек",
        "интернет наконец работает стабильно",
        "я спокойно дошёл домой без пробок",
    ]
    gratitude_actions = [
        "помог мне с презентацией",
        "быстро ответил на письмо",
        "заранее предупредил о переносе встречи",
        "скинул финальную версию файла",
        "разобрался с ошибкой до дедлайна",
        "забрал меня после работы",
        "нашёл время всё объяснить",
        "проверил отчёт перед отправкой",
        "настроил мне доступы",
        "поддержал меня перед защитой",
    ]
    interests = [
        "Мне правда было интересно тебя слушать.",
        "Мне это ОЧЕНЬ интересно, правда.",
        "Я ТАК рада, что мы смогли увидеться.",
        "Я ТАК рад, что мы успели всё закончить.",
        "Я ОЧЕНЬ люблю этот альбом.",
        "Мне действительно понравился этот фильм.",
        "Мне очень нравится, как ты оформил презентацию.",
        "Я правда рад за тебя.",
    ]
    calm_templates = [
        "Сегодня {event}.",
        "Мне нравится, когда {event}.",
        "Я рад, что {event}.",
        "Я благодарен, что {event}.",
    ]
    calm_events = [
        "всё идёт по плану",
        "у нас есть время спокойно всё обсудить",
        "документы уже готовы",
        "занятие прошло понятно и без спешки",
        "дорога заняла меньше времени, чем обычно",
        "вечером дома было тихо и спокойно",
        "мы успели закончить до шести",
        "никто не торопил меня с ответом",
        "вопрос удалось решить с первого раза",
        "я смог нормально отдохнуть на выходных",
    ]
    everyday_subjects = [
        "фильм",
        "сериал",
        "курс",
        "доклад",
        "урок",
        "город",
        "маршрут",
        "ноутбук",
        "телефон",
        "плейлист",
    ]
    everyday_adjectives = [
        "полезным",
        "понятным",
        "удобным",
        "интересным",
        "спокойным",
        "приятным",
        "удачным",
        "красивым",
        "лёгким",
        "сильным",
    ]
    hobbies = [
        "читать вечером",
        "гулять после работы",
        "слушать музыку по дороге домой",
        "готовить ужин без спешки",
        "работать в тишине",
        "смотреть старые фильмы",
        "разбирать фотографии",
        "заниматься английским утром",
        "кататься по городу на выходных",
        "сидеть с кофе и книгой",
    ]
    plans = [
        "отдохнуть на выходных",
        "спокойно закончить отчёт завтра",
        "встретиться с друзьями вечером",
        "закрыть мелкие дела до пятницы",
        "подготовиться к экзамену без спешки",
        "переустановить систему на выходных",
        "прочитать новую книгу в отпуске",
        "наконец разобрать почту",
        "выспаться в субботу",
        "сходить в кино после работы",
    ]
    sincere_caps_templates = [
        "Мне ЭТО действительно понравилось.",
        "Я ОЧЕНЬ рад, что всё получилось.",
        "Мне ТАК приятно, что ты помог.",
        "Я ОЧЕНЬ благодарен за поддержку.",
        "Мы ТАК хорошо провели время вчера.",
        "Я ТАК ждал эту встречу и очень рад, что она состоялась.",
    ]
    workplace_templates = [
        "Сегодня на работе всё прошло спокойно и без лишней суеты.",
        "Коллеги быстро согласовали правки, и мы закрыли вопрос.",
        "Мне понравилось, как команда распределила задачи.",
        "Созвон получился коротким и полезным.",
        "Я доволен тем, как прошла сегодняшняя встреча.",
        "У меня получилось сосредоточиться и спокойно закончить задачу.",
        "Сегодняшняя обратная связь была понятной и доброжелательной.",
        "Мне было комфортно работать в таком темпе.",
        "Документы подготовили заранее, и всё прошло гладко.",
        "Я рад, что никто не тянул с ответами по делу.",
    ]

    candidates: list[str] = []
    for action in gratitude_actions:
        candidates.append(f"Спасибо, что {action}, мне это очень помогло.")
        candidates.append(f"Я очень ценю, что ты {action}.")

    for event in good_events:
        candidates.append(f"Я рад, что {event}.")
        candidates.append(f"Мне приятно, что {event}.")

    for template, event in itertools.product(calm_templates, calm_events):
        candidates.append(template.format(event=event))

    for subject, adjective in itertools.product(everyday_subjects, everyday_adjectives):
        candidates.append(f"Этот {subject} оказался {adjective}.")
        candidates.append(f"Мне показался {subject} довольно {adjective}.")
        candidates.append(f"Для меня этот {subject} получился очень {adjective}.")
        candidates.append(f"В итоге {subject} оказался действительно {adjective}.")

    for hobby in hobbies:
        candidates.append(f"Мне нравится {hobby}.")
        candidates.append(f"Я люблю {hobby}.")

    for plan in plans:
        candidates.append(f"На этой неделе я хочу {plan}.")
        candidates.append(f"На выходных я собираюсь {plan}.")

    candidates.extend(sincere_caps_templates)
    candidates.extend(workplace_templates)
    candidates.extend(interests)
    return _deduplicate_candidates(candidates)


def expand_manual_russian_dataset(
    output_path: Path = MANUAL_DATASET_PATH,
    target_per_label: int = 400,
    random_state: int = 42,
) -> dict:
    existing_df = pd.read_csv(output_path)
    existing_df["text"] = existing_df["text"].astype(str).str.strip()

    sarcastic_existing = existing_df[existing_df["label"] == 1].copy()
    nonsarcastic_existing = existing_df[existing_df["label"] == 0].copy()

    sarcastic_candidates = _build_sarcastic_candidates()
    nonsarcastic_candidates = _build_non_sarcastic_candidates()

    sarcastic_existing_texts = set(sarcastic_existing["text"].tolist())
    nonsarcastic_existing_texts = set(nonsarcastic_existing["text"].tolist())

    sarcastic_candidates = [text for text in sarcastic_candidates if text not in sarcastic_existing_texts]
    nonsarcastic_candidates = [text for text in nonsarcastic_candidates if text not in nonsarcastic_existing_texts]

    rng = random.Random(random_state)
    rng.shuffle(sarcastic_candidates)
    rng.shuffle(nonsarcastic_candidates)

    sarcastic_needed = max(0, target_per_label - len(sarcastic_existing))
    nonsarcastic_needed = max(0, target_per_label - len(nonsarcastic_existing))

    sarcastic_generated = pd.DataFrame(
        {
            "text": sarcastic_candidates[:sarcastic_needed],
            "label": 1,
            "source_url": "manual://generated",
            "source_type": "manual_generated",
            "curation_note": "manual_generated_conversational_sarcastic",
        }
    )
    nonsarcastic_generated = pd.DataFrame(
        {
            "text": nonsarcastic_candidates[:nonsarcastic_needed],
            "label": 0,
            "source_url": "manual://generated",
            "source_type": "manual_generated",
            "curation_note": "manual_generated_conversational_not_sarcastic",
        }
    )

    combined_df = pd.concat(
        [sarcastic_existing, nonsarcastic_existing, sarcastic_generated, nonsarcastic_generated],
        ignore_index=True,
    )
    combined_df = combined_df.drop_duplicates(subset=["text", "label"]).reset_index(drop=True)
    combined_df.to_csv(output_path, index=False, encoding="utf-8")

    label_counts = combined_df["label"].value_counts().to_dict()
    return {
        "output_path": str(output_path),
        "total_rows": int(len(combined_df)),
        "sarcastic_rows": int(label_counts.get(1, 0)),
        "nonsarcastic_rows": int(label_counts.get(0, 0)),
        "generated_sarcastic_rows": int(len(sarcastic_generated)),
        "generated_nonsarcastic_rows": int(len(nonsarcastic_generated)),
    }


if __name__ == "__main__":
    result = expand_manual_russian_dataset()
    print(result)
