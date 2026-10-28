import json
from pathlib import Path

import nbformat as nbf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_SCRIPT = PROJECT_ROOT / "report" / "kr7_stl10_autoencoder_experiment.py"
METRICS_PATH = PROJECT_ROOT / "outputs" / "kr7" / "metrics.json"
NOTEBOOK_PATH = PROJECT_ROOT / "KR7_Variant7_STL10_Autoencoder_Report.ipynb"


def md(text: str):
    return nbf.v4.new_markdown_cell(text)


def code(text: str):
    return nbf.v4.new_code_cell(text)


def main() -> None:
    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    main_metrics = metrics["main_experiment"]
    binary_metrics = metrics["binary_experiment"]

    full_code = EXPERIMENT_SCRIPT.read_text(encoding="utf-8")
    full_code = full_code.replace(
        '\nif __name__ == "__main__":\n    main()\n', "\n"
    )

    nb = nbf.v4.new_notebook()
    nb["metadata"]["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    nb["metadata"]["language_info"] = {"name": "python", "version": "3.12"}

    task_text = """
1. Загрузить набор данных `stl10` из `TensorFlow Datasets` с разбиением на обучающую и тестовую выборки.
2. Оставить в обучающей и тестовой выборках только классы `0, 1, 2, 3, 4`.
3. Преобразовать цветные изображения в оттенки серого, нормализовать пиксели в диапазон `[0.0, 1.0]` и привести данные к форме `(N, 32, 32, 1)`.
4. Создать и обучить автокодировщик с размерностью латентного пространства `32`, самостоятельно выбрав архитектуру и гиперпараметры.
5. Оценить качество модели автокодировщика на тестовой выборке по показателю `MSPE`.
6. Найти тестовые изображения с минимальной и максимальной ошибками реконструкции и визуализировать исходные и восстановленные изображения.
7. Изменить размерность латентного пространства на `2`, переобучить автокодировщик для изображений классов `0` и `1`, сохранив архитектуру и гиперпараметры.
8. Визуализировать тестовую выборку на плоскости двух латентных признаков с раскраской по классам.
9. Выполнить бинарную классификацию методом `kNN` по латентным признакам и по всем признакам, оценить `accuracy`.
10. Построить ROC-кривые для двух классификаторов на одном рисунке и визуализировать границы решений `kNN` в латентном пространстве.
    """.strip()

    nb.cells = [
        md(
            "# Контрольная работа №7\n\n"
            "## Автокодировщики\n\n"
            "**Номер варианта:** 7 "
            "(принят по имени файла задания `2026_Test_7.ipynb`).\n\n"
            "**Тема работы:** исследование автокодировщика для изображений набора `STL10` и "
            "классификация объектов по скрытым и полным признакам."
        ),
        md(
            "## Текст задания\n\n"
            f"{task_text}\n\n"
            "В работе ниже все этапы выполнены последовательно: загрузка и подготовка данных, "
            "обучение автокодировщика с латентной размерностью `32`, оценка `MSPE`, анализ "
            "лучшей и худшей реконструкций, переобучение модели с латентной размерностью `2`, "
            "классификация `kNN`, ROC-кривые и границы решений."
        ),
        md(
            "## Выбранный подход\n\n"
            "Для основной части выбран **сверточный автокодировщик (CNN autoencoder)**, поскольку "
            "изображения обладают локальной структурой и сверточные слои обычно восстанавливают "
            "их лучше, чем простой `MLP`. Архитектура энкодера: `Conv2D(32) -> Conv2D(64) -> "
            "Conv2D(128) -> Dense(128) -> Dense(latent_dim)`. Декодер симметричен и использует "
            "`Conv2DTranspose`. Для достижения низкого `MSPE` использована **двухэтапная схема "
            "обучения**: сначала модель обучается по `MSE`, а затем донастраивается по смешанной "
            "функции потерь `0.25 * MSE + 0.75 * stable_MSPE`. Оптимизатор — `Adam`, размер "
            "мини-пакета — `128`, а для стабильного обучения подключены `EarlyStopping` и "
            "`ReduceLROnPlateau`.\n\n"
            "Для метрики `MSPE` использована **устойчивая версия**: знаменатель ограничивается "
            "снизу величиной `1/255`, что соответствует одному уровню яркости 8-битного "
            "изображения после нормализации. Это нужно, потому что обычный `MSPE` для "
            "нормализованных изображений становится численно нестабильным на почти нулевых пикселях."
        ),
        code(
            "# Библиотеки и параметры окружения\n"
            "import json\n"
            "from pathlib import Path\n"
            "import matplotlib.pyplot as plt\n"
            "import numpy as np\n"
        ),
        md(
            "## Полный воспроизводимый код эксперимента\n\n"
            "Ниже приведен полный код, который загружает `STL10`, обучает обе версии "
            "автокодировщика, вычисляет метрики и сохраняет артефакты в каталог `outputs/kr7`."
        ),
        code(full_code),
        code(
            "# Полный эксперимент уже выполнен, поэтому здесь считываются готовые результаты.\n"
            "# Для повторного запуска полного обучения можно раскомментировать следующую строку:\n"
            "# main()\n\n"
            "PROJECT_ROOT = Path.cwd()\n"
            "with open(PROJECT_ROOT / 'outputs' / 'kr7' / 'metrics.json', 'r', encoding='utf-8') as f:\n"
            "    results = json.load(f)\n\n"
            "main_results = results['main_experiment']\n"
            "binary_results = results['binary_experiment']\n\n"
            "print('MSPE на тестовой выборке:', round(main_results['test_mspe_mean'], 4))\n"
            "print('Минимальный MSPE:', round(main_results['min_mspe_value'], 4), 'индекс =', main_results['min_mspe_index'])\n"
            "print('Максимальный MSPE:', round(main_results['max_mspe_value'], 4), 'индекс =', main_results['max_mspe_index'])\n"
            "print('Accuracy kNN по латентным признакам:', round(binary_results['latent_accuracy'], 4))\n"
            "print('Accuracy kNN по всем признакам:', round(binary_results['pixel_accuracy'], 4))\n"
            "print('Параметры латентного kNN:', binary_results['latent_knn_params'])\n"
            "print('Параметры kNN по всем признакам:', binary_results['pixel_knn_params'])\n"
        ),
        md(
            "## Результаты для автокодировщика с латентной размерностью 32\n\n"
            f"- Размер обучающей выборки: **{main_metrics['train_shape'][0]}** изображений.\n"
            f"- Размер тестовой выборки: **{main_metrics['test_shape'][0]}** изображений.\n"
            f"- Число классов: **5** (`0..4`).\n"
            f"- Средний `MSPE` на тестовой выборке: **{main_metrics['test_mspe_mean']:.4f}**.\n"
            f"- Минимальный `MSPE`: **{main_metrics['min_mspe_value']:.4f}** "
            f"(индекс изображения `{main_metrics['min_mspe_index']}`).\n"
            f"- Максимальный `MSPE`: **{main_metrics['max_mspe_value']:.4f}** "
            f"(индекс изображения `{main_metrics['max_mspe_index']}`).\n\n"
            "График обучения по функции потерь:\n\n"
            "![История обучения](outputs/kr7/main_training_history.png)\n\n"
            "Изображение с минимальной ошибкой реконструкции:\n\n"
            "![Лучшая реконструкция](outputs/kr7/best_reconstruction.png)\n\n"
            "Изображение с максимальной ошибкой реконструкции:\n\n"
            "![Худшая реконструкция](outputs/kr7/worst_reconstruction.png)"
        ),
        md(
            "## Результаты для латентной размерности 2 и бинарной классификации\n\n"
            f"- Размер обучающей выборки: **{binary_metrics['train_shape'][0]}** изображений.\n"
            f"- Размер тестовой выборки: **{binary_metrics['test_shape'][0]}** изображений.\n"
            f"- Классы: **0** и **1**.\n"
            f"- `Accuracy` для `kNN` по латентным признакам: **{binary_metrics['latent_accuracy']:.4f}**.\n"
            f"- `Accuracy` для `kNN` по всем признакам: **{binary_metrics['pixel_accuracy']:.4f}**.\n"
            f"- `AUC` для `kNN` по латентным признакам: **{binary_metrics['latent_auc']:.4f}**.\n"
            f"- `AUC` для `kNN` по всем признакам: **{binary_metrics['pixel_auc']:.4f}**.\n"
            f"- Лучшие параметры `kNN` по латентным признакам: "
            f"`k={binary_metrics['latent_knn_params']['n_neighbors']}`, "
            f"`weights={binary_metrics['latent_knn_params']['weights']}`.\n"
            f"- Лучшие параметры `kNN` по всем признакам: "
            f"`k={binary_metrics['pixel_knn_params']['n_neighbors']}`, "
            f"`weights={binary_metrics['pixel_knn_params']['weights']}`.\n\n"
            "История обучения автокодировщика с латентной размерностью 2:\n\n"
            "![История обучения 2D-модели](outputs/kr7/binary_training_history.png)\n\n"
            "Тестовая выборка в двумерном латентном пространстве:\n\n"
            "![Латентное пространство](outputs/kr7/latent_space_test.png)\n\n"
            "ROC-кривые для двух классификаторов:\n\n"
            "![ROC-кривые](outputs/kr7/knn_roc_curves.png)\n\n"
            "Границы решений `kNN` в латентном пространстве:\n\n"
            "![Границы решений](outputs/kr7/latent_knn_decision_boundaries.png)"
        ),
        md(
            "## Краткие выводы\n\n"
            "1. Сверточный автокодировщик с латентной размерностью `32` дал приемлемое качество "
            f"реконструкции и показал средний `MSPE = {main_metrics['test_mspe_mean']:.4f}` на "
            "тестовой выборке.\n\n"
            "2. Наилучшая реконструкция сохраняет общую форму объекта, а наихудшая соответствует "
            "сложному изображению с заметной потерей деталей, что логично для сильного сжатия до "
            "32 признаков.\n\n"
            "3. Наилучший результат по `MSPE` дал не обычный `MSE`, а двухэтапный режим "
            "`MSE -> mixed(MSE, MSPE-like)`, то есть явная оптимизация в сторону целевой метрики "
            "оказалась важнее, чем простое уменьшение средней квадратичной ошибки.\n\n"
            "4. При уменьшении латентного пространства до двух признаков данные частично разделяются, "
            "но сохраняют существенное перекрытие, поэтому качество `kNN` по латентным признакам "
            f"({binary_metrics['latent_accuracy']:.4f}) уступает качеству по всем пикселям "
            f"({binary_metrics['pixel_accuracy']:.4f}).\n\n"
            "5. ROC-кривые подтверждают тот же вывод: полные признаки дают более уверенное разделение "
            "классов, чем двумерное скрытое представление."
        ),
    ]

    nbf.write(nb, NOTEBOOK_PATH)
    print(NOTEBOOK_PATH)


if __name__ == "__main__":
    main()
