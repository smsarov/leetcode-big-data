import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Базовый каталог вывода (OUT_DIR/dataset, OUT_DIR/results и т.п.)
OUT_DIR = os.getenv("OUT_DIR")
if OUT_DIR:
    base_dir = OUT_DIR
else:
    # Фоллбек на структуру репозитория
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

graph_dir = os.path.join(base_dir, "results", "img", "graphs")
os.makedirs(graph_dir, exist_ok=True)

# =============================================================================
# ЗАГРУЗКА И ПРЕДОБРАБОТКА ДАННЫХ
# =============================================================================

# Загрузка данных
solved_path = os.path.join(base_dir, "dataset", "user-data", "solved_stats.csv")
try:
    df_combined = pd.read_csv(solved_path)
except FileNotFoundError:
    print(f"Файл {solved_path} не найден, графики по решённым задачам построены не будут")
    raise SystemExit(0)

if df_combined.empty:
    print(f"Файл {solved_path} пуст, графики по решённым задачам построены не будут")
    raise SystemExit(0)

# Очистка данных
df_combined = df_combined.drop_duplicates(subset=['username'])
df_combined = df_combined.fillna(0)

# Преобразование числовых колонок
numeric_columns = ['easy', 'medium', 'hard', 'ac_easy', 'ac_medium', 'ac_hard']
for col in numeric_columns:
    df_combined[col] = pd.to_numeric(df_combined[col], errors='coerce').fillna(0)

# =============================================================================
# РАСЧЕТНЫЕ ПОЛЯ
# =============================================================================

# Общее количество решенных задач и попыток
df_combined['total_solved'] = df_combined['ac_easy'] + df_combined['ac_medium'] + df_combined['ac_hard']
df_combined['total_attempted'] = df_combined['easy'] + df_combined['medium'] + df_combined['hard']

# Процент успешных решений
df_combined['success_rate'] = np.where(
    df_combined['total_attempted'] > 0,
    df_combined['total_solved'] / df_combined['total_attempted'] * 100,
    0
)

# =============================================================================
# ОБЩАЯ СТАТИСТИКА РЕШЕННЫХ ЗАДАЧ
# =============================================================================

# Цветовая схема для сложностей
difficulty_colors = ['#90EE90', '#87CEEB', '#FFB6C1']

# 1. Распределение решенных задач по сложности
plt.figure(figsize=(10, 8))
difficulty_dist = df_combined[['ac_easy', 'ac_medium', 'ac_hard']].sum()
plt.pie(difficulty_dist.values, labels=['Easy', 'Medium', 'Hard'],
        autopct='%1.1f%%', colors=difficulty_colors, startangle=90)
plt.title('Распределение решенных задач по уровням сложности', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{graph_dir}/1_распределение_задач_по_сложностям.png', dpi=300, bbox_inches='tight')
plt.show()

# 2. Средняя успешность по уровням сложности
plt.figure(figsize=(10, 8))
success_rates = [
    (df_combined["ac_easy"] / df_combined["easy"]).mean() * 100,
    (df_combined["ac_medium"] / df_combined["medium"]).mean() * 100,
    (df_combined["ac_hard"] / df_combined["hard"]).mean() * 100
]

bars = plt.bar(["Easy", "Medium", "Hard"], success_rates, color=difficulty_colors)

# Добавление значений на столбцы
for i, rate in enumerate(success_rates):
    plt.text(i, rate + 1, f'{rate:.1f}%', ha='center', va='bottom', fontsize=12, fontweight='bold')

plt.title("Эффективность решения задач по уровням сложности", fontsize=14, fontweight='bold')
plt.ylabel("Процент успешных решений (%)")
plt.ylim(0, max(success_rates) * 1.15)
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(f'{graph_dir}/2_эффективность_по_сложностям.png', dpi=300, bbox_inches='tight')
plt.show()

# =============================================================================
# ГРУППИРОВКА ПОЛЬЗОВАТЕЛЕЙ ПО АКТИВНОСТИ
# =============================================================================

# Определение квантилей для группировки
#quantiles = df_combined['total_solved'].quantile([0.25, 0.5, 0.75, 0.9])
#q1, median, q3, p90 = quantiles.values

# Создание групп пользователей
#conditions = [
#    df_combined['total_solved'] <= q1,
#    (df_combined['total_solved'] > q1) & (df_combined['total_solved'] <= median),
#    (df_combined['total_solved'] > median) & (df_combined['total_solved'] <= q3),
#    (df_combined['total_solved'] > q3) & (df_combined['total_solved'] <= p90),
#    df_combined['total_solved'] > p90
#]

#groups = [
#    f'Решено (0-{q1:.0f})',
#    f'Решено ({q1:.0f}-{median:.0f})',
#    f'Решено ({median:.0f}-{q3:.0f})',
#    f'Решено ({q3:.0f}-{p90:.0f})',
#    f'Решено ({p90:.0f}+)'
#]

#df_combined['user_group'] = np.select(conditions, groups, default='Не определено')
#valid_groups = [g for g in groups if g in df_combined['user_group'].unique()]
#df_filtered = df_combined[df_combined['user_group'].isin(valid_groups)]


# Вычисляем децили (10%, 20%, ..., 90%)
deciles = df_combined['total_solved'].quantile([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
d1, d2, d3, d4, d5, d6, d7, d8, d9 = deciles.values

# Создаем условия для группировки
conditions = [
    df_combined['total_solved'] <= d1,
    (df_combined['total_solved'] > d1) & (df_combined['total_solved'] <= d2),
    (df_combined['total_solved'] > d2) & (df_combined['total_solved'] <= d3),
    (df_combined['total_solved'] > d3) & (df_combined['total_solved'] <= d4),
    (df_combined['total_solved'] > d4) & (df_combined['total_solved'] <= d5),
    (df_combined['total_solved'] > d5) & (df_combined['total_solved'] <= d6),
    (df_combined['total_solved'] > d6) & (df_combined['total_solved'] <= d7),
    (df_combined['total_solved'] > d7) & (df_combined['total_solved'] <= d8),
    (df_combined['total_solved'] > d8) & (df_combined['total_solved'] <= d9),
    df_combined['total_solved'] > d9
]

# Формируем названия групп
groups = [
    f'Решено (0-{d1:.0f})',
    f'Решено ({d1:.0f}-{d2:.0f})',
    f'Решено ({d2:.0f}-{d3:.0f})',
    f'Решено ({d3:.0f}-{d4:.0f})',
    f'Решено ({d4:.0f}-{d5:.0f})',
    f'Решено ({d5:.0f}-{d6:.0f})',
    f'Решено ({d6:.0f}-{d7:.0f})',
    f'Решено ({d7:.0f}-{d8:.0f})',
    f'Решено ({d8:.0f}-{d9:.0f})',
    f'Решено ({d9:.0f}+)'
]

# Присваиваем группы
df_combined['user_group'] = np.select(conditions, groups, default='Не определено')

# Фильтруем валидные группы
valid_groups = [g for g in groups if g in df_combined['user_group'].unique()]
df_filtered = df_combined[df_combined['user_group'].isin(valid_groups)]
# =============================================================================
# СТАТИСТИКА ПО ГРУППАМ ПОЛЬЗОВАТЕЛЕЙ
# =============================================================================

# Расчет статистики по группам
group_stats_solved = df_filtered.groupby('user_group')[['ac_easy', 'ac_medium', 'ac_hard']].mean().reindex(valid_groups)
group_stats_attempted = df_filtered.groupby('user_group')[['easy', 'medium', 'hard']].mean().reindex(valid_groups)

# Дополнительная информация по группам
group_info = {}
for group in valid_groups:
    group_data = df_filtered[df_filtered['user_group'] == group]
    total_attempted = group_data[['easy', 'medium', 'hard']].sum().sum()
    total_solved = group_data[['ac_easy', 'ac_medium', 'ac_hard']].sum().sum()
    success_rate = (total_solved / total_attempted * 100) if total_attempted > 0 else 0

    group_info[group] = {
        'count': len(group_data),
        'success_rate': success_rate
    }

# =============================================================================
# ВИЗУАЛИЗАЦИЯ СТАТИСТИКИ ГРУПП
# =============================================================================
print("=" * 60)
print("ОБЩАЯ СТАТИСТИКА АНАЛИЗА")
print("=" * 60)
print(f"Всего пользователей: {len(df_combined):,}")
print(f"Всего решенных задач: {df_combined['total_solved'].sum():,}")
print(f"Средняя успешность: {df_combined['success_rate'].mean():.1f}%")
print(f"Медианное количество решений: {df_combined['total_solved'].median():.1f}")

print(f"\nРАСПРЕДЕЛЕНИЕ ПО ГРУППАМ:")
for group in valid_groups:
    count = len(df_filtered[df_filtered['user_group'] == group])
    percentage = (count / len(df_filtered)) * 100
    avg_solved = df_filtered[df_filtered['user_group'] == group]['total_solved'].mean()
    avg_success= df_filtered[df_filtered['user_group'] == group]['success_rate'].mean()
    print(f"  {group}: {count} пользователей ({percentage:.1f}%), в среднем {avg_solved:.1f} решений, успешных решений {avg_success:.1f} ")

print(f"\nСТАТИСТИКА ПО СЛОЖНОСТЯМ:")
print(f"  Easy:   {df_combined['ac_easy'].sum():,} решено")
print(f"  Medium: {df_combined['ac_medium'].sum():,} решено")
print(f"  Hard:   {df_combined['ac_hard'].sum():,} решено")
# =============================================================================
# УСПЕШНОСТЬ РЕШЕНИЯ ПО СЛОЖНОСТЯМ В КАЖДОЙ ГРУППЕ
# =============================================================================

# Расчет успешности по сложностям для каждой группы
group_success_by_difficulty = {}

for group in valid_groups:
    group_data = df_filtered[df_filtered['user_group'] == group]

    # Расчет успешности для каждого уровня сложности (избегаем деления на ноль)
    easy_success = (group_data['ac_easy'].sum() / group_data['easy'].sum() * 100) if group_data['easy'].sum() > 0 else 0
    medium_success = (group_data['ac_medium'].sum() / group_data['medium'].sum() * 100) if group_data[
                                                                                               'medium'].sum() > 0 else 0
    hard_success = (group_data['ac_hard'].sum() / group_data['hard'].sum() * 100) if group_data['hard'].sum() > 0 else 0

    group_success_by_difficulty[group] = {
        'easy': easy_success,
        'medium': medium_success,
        'hard': hard_success,
        'overall': group_info[group]['success_rate']
    }

# Визуализация успешности по сложностям в группах
plt.figure(figsize=(14, 10))

# Подготовка данных для графика
groups = list(group_success_by_difficulty.keys())
easy_rates = [group_success_by_difficulty[group]['easy'] for group in groups]
medium_rates = [group_success_by_difficulty[group]['medium'] for group in groups]
hard_rates = [group_success_by_difficulty[group]['hard'] for group in groups]

# Создание столбчатой диаграммы
x = np.arange(len(groups))
width = 0.25

plt.bar(x - width, easy_rates, width, label='Easy', color='#90EE90', alpha=0.9)
plt.bar(x, medium_rates, width, label='Medium', color='#87CEEB', alpha=0.9)
plt.bar(x + width, hard_rates, width, label='Hard', color='#FFB6C1', alpha=0.9)

plt.xlabel('Группы пользователей', fontsize=12, fontweight='bold')
plt.ylabel('Процент успешных решений (%)', fontsize=12, fontweight='bold')
plt.title('Успешность решения задач по уровням сложности в разных группах пользователей',
          fontsize=14, fontweight='bold')
plt.xticks(x, groups, rotation=45, ha='right')
plt.legend()
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()

# Добавление значений на столбцы
for i, (easy, medium, hard) in enumerate(zip(easy_rates, medium_rates, hard_rates)):
    plt.text(i - width, easy + 1, f'{easy:.1f}%', ha='center', va='bottom', fontsize=8)
    plt.text(i, medium + 1, f'{medium:.1f}%', ha='center', va='bottom', fontsize=8)
    plt.text(i + width, hard + 1, f'{hard:.1f}%', ha='center', va='bottom', fontsize=8)

plt.savefig(f'{graph_dir}/3_успешность_по_сложностям_в_группах.png', dpi=300, bbox_inches='tight')
plt.show()

# Тепловая карта успешности по группам и сложностям
plt.figure(figsize=(12, 8))

# Подготовка данных для тепловой карты
heatmap_data = []
for group in groups:
    row = [
        group_success_by_difficulty[group]['easy'],
        group_success_by_difficulty[group]['medium'],
        group_success_by_difficulty[group]['hard'],
        group_success_by_difficulty[group]['overall']
    ]
    heatmap_data.append(row)

heatmap_df = pd.DataFrame(
    heatmap_data,
    index=groups,
    columns=['Easy', 'Medium', 'Hard', 'Overall']
)

# Создание тепловой карты
sns.heatmap(heatmap_df, annot=True, fmt='.1f', cmap='YlGnBu',
            cbar_kws={'label': 'Процент успешных решений (%)'})
plt.title('Тепловая карта успешности решения задач по группам и сложностям',
          fontsize=14, fontweight='bold')
plt.xlabel('Уровень сложности')
plt.ylabel('Группы пользователей')
plt.tight_layout()
plt.savefig(f'{graph_dir}/4_тепловая_карта_успешности.png', dpi=300, bbox_inches='tight')
plt.show()

# =============================================================================
# ВЫВОД СТАТИСТИКИ В КОНСОЛЬ
# =============================================================================

print("\n" + "=" * 80)
print("УСПЕШНОСТЬ РЕШЕНИЯ ЗАДАЧ ПО СЛОЖНОСТЯМ В ГРУППАХ")
print("=" * 80)

for group in groups:
    stats = group_success_by_difficulty[group]
    print(f"\n{group}:")
    print(f"  Всего пользователей: {group_info[group]['count']}")
    print(f"  Easy:   {stats['easy']:.1f}% успешных решений")
    print(f"  Medium: {stats['medium']:.1f}% успешных решений")
    print(f"  Hard:   {stats['hard']:.1f}% успешных решений")
    print(f"  Общая успешность: {stats['overall']:.1f}%")

# Анализ тенденций
print("\n" + "=" * 80)
print("АНАЛИЗ ТЕНДЕНЦИЙ")
print("=" * 80)

# Сравнение успешности между группами
first_group = groups[0]
last_group = groups[-1]

print(f"\nСравнение групп '{first_group}' и '{last_group}':")

for difficulty in ['easy', 'medium', 'hard']:
    first_rate = group_success_by_difficulty[first_group][difficulty]
    last_rate = group_success_by_difficulty[last_group][difficulty]
    difference = last_rate - first_rate

    print(f"  {difficulty.capitalize()}: {first_rate:.1f}% → {last_rate:.1f}% "
          f"({difference:+.1f}%)")

# Анализ эффективности по сложностям
print(f"\nЭФФЕКТИВНОСТЬ ПО СЛОЖНОСТЯМ ВО ВСЕХ ГРУППАХ:")
avg_easy = np.mean([group_success_by_difficulty[group]['easy'] for group in groups])
avg_medium = np.mean([group_success_by_difficulty[group]['medium'] for group in groups])
avg_hard = np.mean([group_success_by_difficulty[group]['hard'] for group in groups])

print(f"  Средняя успешность Easy:   {avg_easy:.1f}%")
print(f"  Средняя успешность Medium: {avg_medium:.1f}%")
print(f"  Средняя успешность Hard:   {avg_hard:.1f}%")

# Нахождение наиболее и наименее успешных групп для каждой сложности
for difficulty in ['easy', 'medium', 'hard']:
    rates = [(group, group_success_by_difficulty[group][difficulty]) for group in groups]
    best_group = max(rates, key=lambda x: x[1])
    worst_group = min(rates, key=lambda x: x[1])

    print(f"\n  {difficulty.capitalize()}:")
    print(f"    Лучшая группа: {best_group[0]} ({best_group[1]:.1f}%)")
    print(f"    Худшая группа: {worst_group[0]} ({worst_group[1]:.1f}%)")
# 3. Количество решенных и затронутых задач по группам
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 10))
x_pos = np.arange(len(valid_groups))

# График решенных задач
solved_cumulative = np.zeros(len(valid_groups))
for i, difficulty in enumerate(['ac_easy', 'ac_medium', 'ac_hard']):
    values = group_stats_solved[difficulty].values
    bars = ax1.bar(x_pos, values, bottom=solved_cumulative, label=difficulty[3:], color=difficulty_colors[i])
    solved_cumulative += values

    # Добавляем подписи значений для каждого сегмента
    for j, value in enumerate(values):
        if value > 25:  # Подписываем только ненулевые значения
            height = solved_cumulative[j] - values[j] / 2  # Середина сегмента
            ax1.text(x_pos[j], height, f'{value:.1f}',
                    ha='center', va='center', fontsize=9, fontweight='bold',
                    color='black')

ax1.set_title('Среднее количество решенных задач по группам пользователей', fontsize=14, fontweight='bold')
ax1.set_ylabel('Количество решенных задач')
ax1.set_xticks(x_pos)
ax1.legend(title='Сложность')
ax1.grid(axis='y', alpha=0.3)

# Добавляем общее количество решенных задач сверху столбцов
for i, total in enumerate(solved_cumulative):
    ax1.text(x_pos[i], total +13, f'{total:.1f}',
             ha='center', va='bottom', fontsize=10, fontweight='bold',
             bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8))

# График затронутых задач
attempted_cumulative = np.zeros(len(valid_groups))
for i, difficulty in enumerate(['easy', 'medium', 'hard']):
    values = group_stats_attempted[difficulty].values
    bars = ax2.bar(x_pos, values, bottom=attempted_cumulative, label=difficulty, color=difficulty_colors[i])
    attempted_cumulative += values

    # Добавляем подписи значений для каждого сегмента
    for j, value in enumerate(values):
        if value > 25:  # Подписываем только ненулевые значения
            height = attempted_cumulative[j] - values[j] / 2  # Середина сегмента
            ax2.text(x_pos[j], height, f'{value:.1f}',
                    ha='center', va='center', fontsize=9, fontweight='bold',
                    color='black')

ax2.set_title('Среднее количество затронутых задач по группам пользователей', fontsize=14, fontweight='bold')
ax2.set_xlabel('Группы пользователей')
ax2.set_ylabel('Количество затронутых задач')
ax2.set_xticks(x_pos)

# Добавляем общее количество затронутых задач сверху столбцов
for i, total in enumerate(attempted_cumulative):
    ax2.text(x_pos[i], total + 13, f'{total:.1f}',
             ha='center', va='bottom', fontsize=10, fontweight='bold',
             bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8))

# Подписи для обоих графиков
x_labels = [f"{group}\n{group_info[group]['count']} чел." for group in valid_groups]
ax1.set_xticklabels(x_labels, rotation=0)
ax2.set_xticklabels(x_labels, rotation=0)
ax2.legend(title='Сложность')

plt.tight_layout()
plt.savefig(f'{graph_dir}/3_10_активность_по_группам.png', dpi=300, bbox_inches='tight')
plt.show()

# 4. Процентное соотношение по группам
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 12))

# Проценты решенных задач
solved_percentages = group_stats_solved.div(group_stats_solved.sum(axis=1), axis=0) * 100
solved_cumulative_pct = np.zeros(len(valid_groups))

for i, difficulty in enumerate(['ac_easy', 'ac_medium', 'ac_hard']):
    values = solved_percentages[difficulty].values
    bars = ax1.bar(x_pos, values, bottom=solved_cumulative_pct, label=difficulty[3:], color=difficulty_colors[i])
    solved_cumulative_pct += values

    # Добавляем подписи процентов для каждого сегмента
    for j, value in enumerate(values):
        if value >= 0:  # Подписываем только сегменты >= 5% для читаемости
            height = solved_cumulative_pct[j] - values[j] / 2  # Середина сегмента
            ax1.text(x_pos[j], height, f'{value:.1f}%',
                    ha='center', va='center', fontsize=9, fontweight='bold',
                    color='black')

ax1.set_title('Процентное соотношение решенных задач по группам', fontsize=14, fontweight='bold')
ax1.set_ylabel('Доля решенных задач (%)')
ax1.set_ylim(0, 100)
ax1.set_xticks(x_pos)
ax1.legend(title='Сложность')
ax1.grid(axis='y', alpha=0.3)

# Добавляем общее количество решенных задач сверху
total_solved_per_group = group_stats_solved.sum(axis=1)


# Проценты затронутых задач
attempted_percentages = group_stats_attempted.div(group_stats_attempted.sum(axis=1), axis=0) * 100
attempted_cumulative_pct = np.zeros(len(valid_groups))

for i, difficulty in enumerate(['easy', 'medium', 'hard']):
    values = attempted_percentages[difficulty].values
    bars = ax2.bar(x_pos, values, bottom=attempted_cumulative_pct, label=difficulty, color=difficulty_colors[i])
    attempted_cumulative_pct += values

    # Добавляем подписи процентов для каждого сегмента
    for j, value in enumerate(values):
        if value >= 0:  # Подписываем только сегменты >= 5% для читаемости
            height = attempted_cumulative_pct[j] - values[j] / 2  # Середина сегмента
            ax2.text(x_pos[j], height, f'{value:.1f}%',
                    ha='center', va='center', fontsize=9, fontweight='bold',
                    color='black')

ax2.set_title('Процентное соотношение затронутых задач по группам', fontsize=14, fontweight='bold')
ax2.set_xlabel('Группы пользователей')
ax2.set_ylabel('Доля затронутых задач (%)')
ax2.set_ylim(0, 100)
ax2.set_xticks(x_pos)
ax2.legend(title='Сложность')
ax2.grid(axis='y', alpha=0.3)

# Добавляем общее количество затронутых задач сверху

# Подписи с успешностью
x_labels = [f"{group}\nУспешность: {group_info[group]['success_rate']:.1f}%" for group in valid_groups]
ax1.set_xticklabels(x_labels, rotation=0)
ax2.set_xticklabels(x_labels, rotation=0)

plt.tight_layout()
plt.savefig(f'{graph_dir}/4_10_процентное_соотношение_по_группам.png', dpi=300, bbox_inches='tight')
plt.show()

# =============================================================================
# КОРРЕЛЯЦИОННЫЙ АНАЛИЗ
# =============================================================================

# 5. Матрица корреляций
plt.figure(figsize=(10, 8))
correlation_data = df_combined[['ac_easy', 'ac_medium', 'ac_hard', 'total_solved', 'success_rate']]
correlation_matrix = correlation_data.corr()

sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
            square=True, linewidths=0.5, cbar_kws={'shrink': 0.8})
plt.title('Корреляция между метриками продуктивности', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{graph_dir}/5_10_матрица_корреляций.png', dpi=300, bbox_inches='tight')
plt.show()

# =============================================================================
# РАСПРЕДЕЛЕНИЯ И ДИАГРАММЫ РАССЕЯНИЯ
# =============================================================================

# 6. Распределение количества решенных задач
plt.figure(figsize=(12, 8))
ax = sns.histplot(df_combined["total_solved"], bins=50, kde=True, color="skyblue")

median_val = df_combined["total_solved"].median()
mean_val = df_combined["total_solved"].mean()

plt.axvline(median_val, color='red', linestyle='--', alpha=0.8, label=f'Медиана: {median_val:.1f}')
plt.axvline(mean_val, color='green', linestyle='--', alpha=0.8, label=f'Среднее: {mean_val:.1f}')

plt.title("Распределение пользователей по количеству решенных задач", fontsize=14, fontweight='bold')
plt.xlabel("Количество решенных задач")
plt.ylabel("Количество пользователей")
plt.legend()
plt.grid(alpha=0.3)
plt.savefig(f'{graph_dir}/6_10_распределение_решенных_задач.png', dpi=300, bbox_inches='tight')
plt.show()

# 7. Распределение успешности решений
plt.figure(figsize=(12, 8))
ax = sns.histplot(df_combined["success_rate"], bins=50, kde=True, color="lightcoral", binrange=(0, 100))

median_sr = df_combined["success_rate"].median()
mean_sr = df_combined["success_rate"].mean()

plt.axvline(median_sr, color='red', linestyle='--', alpha=0.8, label=f'Медиана: {median_sr:.1f}%')
plt.axvline(mean_sr, color='green', linestyle='--', alpha=0.8, label=f'Среднее: {mean_sr:.1f}%')

plt.title("Распределение успешности решений пользователей", fontsize=14, fontweight='bold')
plt.xlabel("Процент успешных решений (%)")
plt.ylabel("Количество пользователей")
plt.xlim(0, 100)
plt.legend()
plt.grid(alpha=0.3)
plt.savefig(f'{graph_dir}/7_10_распределение_успешности.png', dpi=300, bbox_inches='tight')
plt.show()

# 8. Зависимость успешности от опыта
plt.figure(figsize=(14, 8))
group_colors = [
    '#FF9E9E', '#A0E7E5', '#B5EAD7', '#FFDAC1', '#C7CEEA',
    '#F8B195', '#F67280', '#C06C84', '#6C5B7B', '#355C7D'
]

for i, group in enumerate(valid_groups):
    group_data = df_filtered[df_filtered['user_group'] == group]
    plt.scatter(group_data["total_solved"], group_data["success_rate"],
                alpha=0.6, color=group_colors[i], label=group, s=50)

plt.title("Зависимость успешности решений от количества решенных задач", fontsize=14, fontweight='bold')
plt.xlabel("Общее количество решенных задач")
plt.ylabel("Процент успешных решений (%)")
plt.legend(title="Группы пользователей")
plt.grid(alpha=0.3)
plt.savefig(f'{graph_dir}/8_10_успешность_vs_опыт.png', dpi=300, bbox_inches='tight')
plt.show()
plt.figure(figsize=(14, 8))

avg_x = []
avg_y = []

for i, group in enumerate(valid_groups):
    group_data = df_filtered[df_filtered['user_group'] == group]



    # Вычисляем средние значения для группы
    avg_solved = group_data["total_solved"].mean()
    avg_success = group_data["success_rate"].mean()

    # Сохраняем средние значения
    avg_x.append(avg_solved)
    avg_y.append(avg_success)

    # Рисуем большую точку для среднего значения группы

# Соединяем средние точки линией
plt.plot(avg_x, avg_y, color='black', linewidth=2.5, linestyle='--',
         marker='o', markersize=8, alpha=0.8, label='Средние по группам')

plt.title("Зависимость успешности решений от количества решенных задач", fontsize=14, fontweight='bold')
plt.xlabel("Общее количество решенных задач")
plt.ylabel("Процент успешных решений (%)")
plt.legend(title="Группы пользователей")
plt.grid(alpha=0.3)
plt.savefig(f'{graph_dir}/8_10_avg_успешность_vs_опыт.png', dpi=300, bbox_inches='tight')
plt.show()
# 9. Соотношение Easy и Medium задач
plt.figure(figsize=(14, 8))
for i, group in enumerate(valid_groups):
    group_data = df_filtered[df_filtered['user_group'] == group]
    plt.scatter(group_data["ac_easy"], group_data["ac_medium"],
                alpha=0.6, color=group_colors[i], label=group, s=50)

plt.title("Соотношение решенных задач Easy и Medium по группам", fontsize=14, fontweight='bold')
plt.xlabel("Количество решенных Easy задач")
plt.ylabel("Количество решенных Medium задач")
plt.legend(title="Группы пользователей")
plt.grid(alpha=0.3)
plt.savefig(f'{graph_dir}/9_10_соотношение_easy_medium.png', dpi=300, bbox_inches='tight')
plt.show()

# 10. Соотношение Medium и Hard задач
plt.figure(figsize=(14, 8))
for i, group in enumerate(valid_groups):
    group_data = df_filtered[df_filtered['user_group'] == group]
    plt.scatter(group_data["ac_medium"], group_data["ac_hard"],
                alpha=0.6, color=group_colors[i], label=group, s=50)

plt.title("Соотношение решенных задач Medium и Hard по группам", fontsize=14, fontweight='bold')
plt.xlabel("Количество решенных Medium задач")
plt.ylabel("Количество решенных Hard задач")
plt.legend(title="Группы пользователей")
plt.grid(alpha=0.3)
plt.savefig(f'{graph_dir}/10_10_соотношение_medium_hard.png', dpi=300, bbox_inches='tight')
plt.show()


# 11. Распределение пользователей по группам
plt.figure(figsize=(14, 8))
ax = sns.countplot(x="user_group", data=df_filtered, order=valid_groups, palette=group_colors)

plt.title("Распределение пользователей по группам активности", fontsize=14, fontweight='bold')
plt.xlabel("Группы пользователей по количеству решенных задач")
plt.ylabel("Количество пользователей")

# Добавляем подписи значений
for p in ax.patches:
    height = p.get_height()
    ax.text(p.get_x() + p.get_width()/2., height + 0.5,
            f'{int(height)}',
            ha="center", va="bottom", fontsize=11, fontweight='bold')

plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(f'{graph_dir}/11_10_распределение_пользователей_по_группам.png', dpi=300, bbox_inches='tight')
plt.show()

# 12. Средний процент успешности по группам
plt.figure(figsize=(14, 8))
ax = sns.barplot(x="user_group", y="success_rate", data=df_filtered,
                 order=valid_groups, palette=group_colors, estimator="mean")

plt.title("Средняя успешность решений по группам пользователей", fontsize=14, fontweight='bold')
plt.xlabel("Группы пользователей по количеству решенных задач")
plt.ylabel("Средний процент успешных решений (%)")

# Добавляем подписи значений
for p in ax.patches:
    height = p.get_height()
    ax.text(p.get_x() + p.get_width()/2., height + 0.5,
            f'{height:.1f}%',
            ha="center", va="bottom", fontsize=11, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8))

plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(f'{graph_dir}/12_10_средняя_успешность_по_группам.png', dpi=300, bbox_inches='tight')
plt.show()
# =============================================================================
# ФИНАЛЬНАЯ СТАТИСТИКА
# =============================================================================

print("=" * 60)
print("ОБЩАЯ СТАТИСТИКА АНАЛИЗА")
print("=" * 60)
print(f"Всего пользователей: {len(df_combined):,}")
print(f"Всего решенных задач: {df_combined['total_solved'].sum():,}")
print(f"Средняя успешность: {df_combined['success_rate'].mean():.1f}%")
print(f"Медианное количество решений: {df_combined['total_solved'].median():.1f}")

print(f"\nРАСПРЕДЕЛЕНИЕ ПО ГРУППАМ:")
for group in valid_groups:
    count = len(df_filtered[df_filtered['user_group'] == group])
    percentage = (count / len(df_filtered)) * 100
    avg_solved = df_filtered[df_filtered['user_group'] == group]['total_solved'].mean()
    avg_success= df_filtered[df_filtered['user_group'] == group]['success_rate'].mean()

    print(f"  {group}: {count} пользователей ({percentage:.1f}%), в среднем {avg_solved:.1f} решений, успешных решений {avg_success:.1f} ")

print(f"\nСТАТИСТИКА ПО СЛОЖНОСТЯМ:")
print(f"  Easy:   {df_combined['ac_easy'].sum():,} решено")
print(f"  Medium: {df_combined['ac_medium'].sum():,} решено")
print(f"  Hard:   {df_combined['ac_hard'].sum():,} решено")