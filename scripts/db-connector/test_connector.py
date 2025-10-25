from db_connector import load_csv_to_db, fetch_data

# Загрузка CSV в БД
csv_tables = [
    ("submissions.csv", "submissions"),
    ("language_stats.csv", "language_stats"),
    ("solved_stats.csv", "solved_stats"),
    ("users.csv", "users")
]

for csv_path, table_name in csv_tables:
    load_csv_to_db(csv_path, table_name)

# Примеры выборки
print(fetch_data("language_stats")[:5])
print(fetch_data("solved_stats")[:5])
print(fetch_data("users")[:5])

# Конкретный пользователь
print(fetch_data("language_stats", username="xiaowuc1"))
print(fetch_data("solved_stats", username="_kevinyang"))
print(fetch_data("users", username="klion26"))

# Только нужные колонки
print(fetch_data("language_stats", username="Naruto_x", columns=["languagename"]))
print(fetch_data("solved_stats", username="_kevinyang", columns=["hard", "ac_hard"]))
print(fetch_data("users", username="klion26", columns=["display_name", "country"]))
