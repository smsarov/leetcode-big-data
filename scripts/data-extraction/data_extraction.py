import os
import sys

import pandas as pd


def main(dataset_dir: str | None = None, results_dir: str | None = None):
    """
    Генерация агрегированных CSV-файлов без использования Postgres.
    Читает users.csv, language_stats.csv и solved_stats.csv из dataset_dir
    и пишет popular_languages.csv, languages_by_country.csv, avg_solved_by_country.csv в results_dir.
    """
    try:
        base_out = os.getenv("OUT_DIR")
        if dataset_dir is None or results_dir is None:
            # Работаем либо относительно OUT_DIR, либо относительно структуры репозитория
            if base_out:
                root = base_out
            else:
                root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

            if dataset_dir is None:
                dataset_dir = os.path.join(root, "dataset")
            if results_dir is None:
                results_dir = os.path.join(root, "results")

        users_path = os.path.join(dataset_dir, "users", "users.csv")
        lang_path = os.path.join(dataset_dir, "user-data", "language_stats.csv")
        solved_path = os.path.join(dataset_dir, "user-data", "solved_stats.csv")

        print(f"Чтение users из {users_path}")
        users = pd.read_csv(users_path)
        print(f"Чтение language_stats из {lang_path}")
        lang = pd.read_csv(lang_path)
        print(f"Чтение solved_stats из {solved_path}")
        solved = pd.read_csv(solved_path)

        os.makedirs(results_dir, exist_ok=True)

        # 1. Самые популярные языки
        try:
            df1 = (
                lang.groupby("languageName")["username"]
                .nunique()
                .reset_index(name="user_count")
                .sort_values("user_count", ascending=False)
            )
            df1.to_csv(os.path.join(results_dir, "popular_languages.csv"), index=False)
            print("popular_languages.csv сохранён")
        except Exception as e:
            print(f"Не удалось сформировать popular_languages.csv: {e}")

        # 2. Самые популярные языки по странам
        try:
            df_lang_users = lang.merge(
                users[["username", "country"]], on="username", how="left"
            )
            df2 = (
                df_lang_users.groupby(["country", "languageName"])["username"]
                .nunique()
                .reset_index(name="user_count")
                .sort_values(["country", "user_count"], ascending=[True, False])
            )
            df2.to_csv(os.path.join(results_dir, "languages_by_country.csv"), index=False)
            print("languages_by_country.csv сохранён")
        except Exception as e:
            print(f"Не удалось сформировать languages_by_country.csv: {e}")

        # 3. Среднее количество решённых задач по странам
        try:
            df_solved_users = solved.merge(
                users[["username", "country"]], on="username", how="left"
            ).copy()

            for col in ["easy", "medium", "hard", "ac_easy", "ac_medium", "ac_hard"]:
                if col in df_solved_users.columns:
                    df_solved_users[col] = pd.to_numeric(
                        df_solved_users[col], errors="coerce"
                    ).fillna(0)

            df_solved_users["total"] = (
                df_solved_users.get("easy", 0)
                + df_solved_users.get("medium", 0)
                + df_solved_users.get("hard", 0)
            )
            df_solved_users["total_ac"] = (
                df_solved_users.get("ac_easy", 0)
                + df_solved_users.get("ac_medium", 0)
                + df_solved_users.get("ac_hard", 0)
            )

            df3 = (
                df_solved_users.groupby("country")[["total", "total_ac"]]
                .mean()
                .reset_index()
                .rename(columns={"total": "avg_solved", "total_ac": "avg_ac"})
                .sort_values("avg_solved", ascending=False)
            )
            df3.to_csv(os.path.join(results_dir, "avg_solved_by_country.csv"), index=False)
            print("avg_solved_by_country.csv сохранён")
        except Exception as e:
            print(f"Не удалось сформировать avg_solved_by_country.csv: {e}")

    except FileNotFoundError as e:
        print(f"Файл не найден при генерации агрегатов: {e}")
    except Exception as e:
        print(f"Необработанная ошибка при генерации агрегатов: {e}")


if __name__ == "__main__":
    # Позволяем передать пути через аргументы, но не рушимся при ошибках
    try:
        ds_dir = None
        res_dir = None
        if len(sys.argv) >= 3:
            ds_dir = sys.argv[1]
            res_dir = sys.argv[2]
        main(ds_dir, res_dir)
    except Exception as e:
        print(f"Unexpected error in data_extraction main(): {e}")