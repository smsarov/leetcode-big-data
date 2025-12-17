import argparse
import os
import subprocess
import sys
import time


def run_subprocess(cmd: list[str], cwd: str | None = None, env: dict | None = None):
    """Обёртка над subprocess.run, которая никогда не бросает исключений."""
    print(f"\n==== Запуск: {' '.join(cmd)} ====")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        if result.returncode != 0:
            print(f"Команда завершилась с кодом {result.returncode}, продолжаем пайплайн")
    except Exception as e:
        print(f"Ошибка при выполнении команды {' '.join(cmd)}: {e}")


def wait_for_api(base_url: str, timeout_sec: int = 0):
    """Ожидает готовности локального API. timeout_sec=0 => ждать бесконечно."""
    import requests

    start = time.time()
    attempt = 0
    while True:
        attempt += 1
        try:
            # Пробуем лёгкий запрос к API. Любой ответ от сервера считаем признаком готовности.
            resp = requests.get(base_url, timeout=5)
            print(f"API ответил со статусом {resp.status_code}, считаем его готовым")
            return
        except Exception as e:
            print(f"API ещё не готов ({e}), попытка {attempt}")

        if timeout_sec and time.time() - start > timeout_sec:
            print("Истёк таймаут ожидания API, продолжаем без гарантии доступности")
            return

        time.sleep(5)


def ensure_dirs(out_dir: str):
    dataset_users = os.path.join(out_dir, "dataset", "users")
    dataset_user_data = os.path.join(out_dir, "dataset", "user-data")
    results_dir = os.path.join(out_dir, "results")
    graphs_dir = os.path.join(results_dir, "img", "graphs")

    for d in [dataset_users, dataset_user_data, graphs_dir]:
        os.makedirs(d, exist_ok=True)

    return {
        "dataset_users": dataset_users,
        "dataset_user_data": dataset_user_data,
        "results": results_dir,
        "graphs": graphs_dir,
    }


def run_pipeline(out_dir: str):
    # Готовим структуру директорий
    dirs = ensure_dirs(out_dir)

    # Устанавливаем OUT_DIR для всех подпроцессов
    env = os.environ.copy()
    env["OUT_DIR"] = out_dir
    os.environ["OUT_DIR"] = out_dir

    # 1. Ждём готовности API
    api_base_url = env.get("API_BASE_URL", "http://api:3000")
    print(f"Ожидание API по адресу {api_base_url}")
    try:
        wait_for_api(api_base_url)
    except Exception as e:
        print(f"Ошибка при ожидании API: {e}")

    # Флаг тестового режима
    test_mode = env.get("RUN_TEST", "0") == "1"

    # 2. Парсинг глобального рейтинга LeetCode
    users_csv = os.path.join(dirs["dataset_users"], "users.csv")
    try:
        cmd = [
            sys.executable,
            "scripts/leaderboard-parser/leaderboard-parser.py",
            "--output",
            users_csv,
        ]
        if test_mode:
            # Ограничиваем количество страниц рейтинга для ускорения теста
            cmd.extend(["--max-pages", "3"])
        run_subprocess(cmd, env=env)
    except Exception as e:
        print(f"Ошибка при запуске парсера рейтинга: {e}")

    # 3. Сбор пользовательской статистики через локальный API
    lang_stats_csv = os.path.join(dirs["dataset_user_data"], "language_stats.csv")
    solved_stats_csv = os.path.join(dirs["dataset_user_data"], "solved_stats.csv")
    try:
        if test_mode:
            # Ограничиваем количество пользователей для тестового прогона
            env.setdefault("PROCESS_COUNT", "500")
            env.setdefault("THROTTLE_DELAY_SEC", "0.01")
        run_subprocess(
            [
                sys.executable,
                "scripts/fill-user-info/fill-user-info.py",
            ],
            env=env,
        )
    except Exception as e:
        print(f"Ошибка при запуске fill-user-info: {e}")

    # 4. Генерация агрегированных CSV (popular_languages, languages_by_country, avg_solved_by_country)
    try:
        run_subprocess(
            [
                sys.executable,
                "scripts/data-extraction/data_extraction.py",
                os.path.join(out_dir, "dataset"),
                os.path.join(out_dir, "results"),
            ],
            env=env,
        )
    except Exception as e:
        print(f"Ошибка при запуске data_extraction: {e}")

    # 5. Графики по решённым задачам
    try:
        run_subprocess(
            [
                sys.executable,
                "scripts/graphs/tasks-solved.py",
            ],
            env=env,
        )
    except Exception as e:
        print(f"Ошибка при запуске tasks-solved: {e}")

    # 6. Круговая диаграмма языков
    try:
        run_subprocess(
            [
                sys.executable,
                "scripts/graphs/language-pie-chart.py",
            ],
            env=env,
        )
    except Exception as e:
        print(f"Ошибка при запуске language-pie-chart: {e}")

    # 7. Экспорт для Kibana
    try:
        kibana_csv = os.path.join(out_dir, "results", "leetcode_global_ranking_for_kibana.csv")
        run_subprocess(
            [
                sys.executable,
                "scripts/leaderboard-parser/kibana_export.py",
                users_csv,
                kibana_csv,
            ],
            env=env,
        )
    except Exception as e:
        print(f"Ошибка при запуске kibana_export: {e}")

    # 8. Кластеризация по языкам (опционально)
    run_clustering = env.get("RUN_CLUSTERING", "1") != "0"
    if run_clustering:
        try:
            run_subprocess(
                [
                    sys.executable,
                    "scripts/language-clustering/language-clustering.py",
                ],
                env=env,
            )
        except Exception as e:
            print(f"Ошибка при запуске language-clustering: {e}")

    # 9. Обучение предиктивной модели (опционально)
    run_model = env.get("RUN_MODEL", "1") != "0"
    if run_model:
        try:
            run_subprocess(
                [
                    sys.executable,
                    "scripts/prediction model/predictional_model.py",
                ],
                env=env,
            )
        except Exception as e:
            print(f"Ошибка при запуске predictional_model: {e}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Полный пайплайн сбора и анализа данных LeetCode."
    )
    parser.add_argument(
        "-out",
        dest="out_dir",
        default=os.getenv("OUT_DIR", "/data/out"),
        help="Каталог, куда будут записаны подкаталоги dataset/ и results/ (по умолчанию /data/out)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    out_dir = os.path.abspath(args.out_dir)
    try:
        run_pipeline(out_dir)
    except Exception as e:
        # Никогда не отдаём необработанное исключение наружу
        print(f"Unexpected error in main pipeline: {e}")


