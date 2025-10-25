from db_connector import engine
import pandas as pd
import os

base_dir = os.path.dirname(os.path.abspath(__file__))

# 1. Самые популярные языки
query1 = '''
SELECT languagename, COUNT(DISTINCT username) AS user_count
FROM language_stats
GROUP BY languagename
ORDER BY user_count DESC;
'''
df1 = pd.read_sql(query1, engine)
df1.to_csv(os.path.join(base_dir, "popular_languages.csv"), index=False)
print("popular_languages.csv сохранён")

# 2. Самые популярные языки по странам
query2 = '''
SELECT u.country, l.languagename, COUNT(DISTINCT l.username) AS user_count
FROM language_stats l
JOIN users u ON l.username = u.username
GROUP BY u.country, l.languagename
ORDER BY u.country, user_count DESC;
'''
df2 = pd.read_sql(query2, engine)
df2.to_csv(os.path.join(base_dir, "languages_by_country.csv"), index=False)
print("languages_by_country.csv сохранён")

# 3. Среднее количество решённых задач по странам
query3 = '''
SELECT 
    u.country, 
    AVG((s.easy::int + s.medium::int + s.hard::int)) AS avg_solved,
    AVG((s.ac_easy::int + s.ac_medium::int + s.ac_hard::int)) AS avg_ac
FROM solved_stats s
JOIN users u ON s.username = u.username
GROUP BY u.country
ORDER BY avg_solved DESC;
'''
df3 = pd.read_sql(query3, engine)
df3.to_csv(os.path.join(base_dir, "avg_solved_by_country.csv"), index=False)
print("avg_solved_by_country.csv сохранён")