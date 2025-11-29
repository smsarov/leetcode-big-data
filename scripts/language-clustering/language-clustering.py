import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler, Normalizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import warnings

warnings.filterwarnings('ignore')


# Загрузка данных
def load_data(file1_path, file2_path):
    """Загрузка и предобработка данных"""
    df1 = pd.read_csv(file1_path)
    df2 = pd.read_csv(file2_path)
    df = pd.concat([df1, df2], ignore_index=True)
    print(f"Всего записей: {len(df)}")
    print(f"Уникальных пользователей: {df['username'].nunique()}")
    print(f"Уникальных языков: {df['languageName'].nunique()}")
    print("\nПервые несколько строк данных:")
    print(df.head())
    return df


def create_user_language_matrix(df):
    """Создает матрицу, где строки - пользователи, столбцы - языки"""
    # Создаем копию DataFrame чтобы не изменять оригинал
    df_modified = df.copy()

    # Преобразуем все значения в колонке languageName в строки
    df_modified['languageName'] = df_modified['languageName'].astype(str)

    # Заменяем Python3 на Python в колонке languageName
    df_modified['languageName'] = df_modified['languageName'].str.replace(
        'Python3', 'Python', case=False, regex=False
    )

    # Убедимся, что problemsSolved числовой
    df_modified['problemsSolved'] = pd.to_numeric(df_modified['problemsSolved'], errors='coerce').fillna(0)

    # Создаем pivot table с количеством решенных задач
    user_language = df_modified.pivot_table(
        index='username',
        columns='languageName',
        values='problemsSolved',
        aggfunc='sum',
        fill_value=0
    )

    print(f"\nРазмер матрицы пользователь-язык: {user_language.shape}")
    print(f"Языки программирования: {list(user_language.columns)}")

    return user_language


# Анализ и визуализация данных
def explore_data(user_language):
    """Анализ и визуализация исходных данных"""
    # Самые популярные языки
    language_stats = user_language.astype(bool).sum().sort_values(ascending=False)

    plt.figure(figsize=(15, 10))

    # График популярности языков
    plt.subplot(2, 2, 1)
    language_stats.head(15).plot(kind='barh')
    plt.title('Топ-15 самых популярных языков')
    plt.xlabel('Количество пользователей')

    # Распределение количества языков на пользователя
    plt.subplot(2, 2, 2)
    languages_per_user = (user_language > 0).sum(axis=1)
    languages_per_user.hist(bins=30, alpha=0.7)
    plt.title('Распределение количества языков на пользователя')
    plt.xlabel('Количество языков')
    plt.ylabel('Количество пользователей')

    # Тепловая карта корреляций между языками (топ-15)
    plt.subplot(2, 2, 3)
    top_languages = language_stats.head(15).index
    correlation_matrix = user_language[top_languages].corr()
    mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
    sns.heatmap(correlation_matrix, mask=mask, cmap='coolwarm', center=0,
                square=True, linewidths=.5, cbar_kws={"shrink": .5})
    plt.title('Корреляция между языками (топ-15)')

    plt.tight_layout()
    plt.show()

    print(f"\nСреднее количество языков на пользователя: {languages_per_user.mean():.2f}")
    print(f"Максимальное количество языков: {languages_per_user.max()}")

    return language_stats


# Подготовка данных для кластеризации - оставляем только 12 самых популярных языков
def prepare_data(user_language, n_languages=15):
    """Подготовка данных для кластеризации - оставляем 12 самых популярных языков"""
    # Выбираем топ-N самых популярных языков
    language_counts = (user_language > 0).sum()
    top_languages = language_counts.nlargest(n_languages).index
    user_language_filtered = user_language[top_languages]

    print(f"\nОставлено {len(top_languages)} самых популярных языков:")
    for i, lang in enumerate(top_languages, 1):
        count = language_counts[lang]
        print(f"{i:2d}. {lang}: {count} пользователей")

    # Нормализуем данные (важно для косинусного расстояния)
    normalizer = Normalizer(norm='l2')
    normalized_data = normalizer.fit_transform(user_language_filtered)

    return normalized_data, user_language_filtered, top_languages


# Определение оптимального количества кластеров
def find_optimal_clusters(normalized_data, max_k=10):
    """Поиск оптимального количества кластеров"""
    inertia = []
    silhouette_scores = []
    k_range = range(2, max_k + 1)

    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(normalized_data)
        inertia.append(kmeans.inertia_)
        silhouette_scores.append(silhouette_score(normalized_data, labels))

    # Визуализация
    plt.figure(figsize=(15, 5))

    plt.subplot(1, 3, 1)
    plt.plot(k_range, inertia, 'bo-')
    plt.xlabel('Количество кластеров')
    plt.ylabel('Inertia')
    plt.title('Метод локтя')

    plt.subplot(1, 3, 2)
    plt.plot(k_range, silhouette_scores, 'ro-')
    plt.xlabel('Количество кластеров')
    plt.ylabel('Silhouette Score')
    plt.title('Silhouette Score')

    # Находим оптимальное k (максимальный silhouette score)
    optimal_k = k_range[np.argmax(silhouette_scores)]

    plt.subplot(1, 3, 3)
    plt.bar(k_range, silhouette_scores, color='lightblue')
    plt.axvline(x=optimal_k, color='red', linestyle='--', label=f'Оптимальное k = {optimal_k}')
    plt.xlabel('Количество кластеров')
    plt.ylabel('Silhouette Score')
    plt.title(f'Оптимальное количество кластеров: {optimal_k}')
    plt.legend()

    plt.tight_layout()
    plt.show()

    print(f"Оптимальное количество кластеров: {optimal_k}")
    print(f"Лучший silhouette score: {max(silhouette_scores):.3f}")

    return optimal_k


# Кластеризация
def perform_clustering(normalized_data, n_clusters):
    """Выполнение кластеризации K-means"""
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(normalized_data)

    print(f"\nКластеризация завершена. Распределение по кластерам:")
    unique, counts = np.unique(cluster_labels, return_counts=True)
    for cluster, count in zip(unique, counts):
        print(f"Кластер {cluster}: {count} пользователей ({count / len(cluster_labels) * 100:.1f}%)")

    return kmeans, cluster_labels


# Анализ характеристик кластеров - показываем только по 3 языка на кластер
def analyze_clusters(user_language_filtered, cluster_labels, popular_languages, n_clusters):
    """Анализ характеристик каждого кластера - по 3 языка на кластер"""
    # Добавляем метки кластеров к данным
    clustered_data = user_language_filtered.copy()
    clustered_data['cluster'] = cluster_labels

    # Считаем средние значения по кластерам
    cluster_means = clustered_data.groupby('cluster').mean()

    # Анализируем для каждого кластера топ-3 языка
    plt.figure(figsize=(20, 10))

    # Определяем layout для subplots
    rows = (n_clusters + 3) // 4  # Округляем вверх
    cols = min(n_clusters, 4)

    for i in range(n_clusters):
        plt.subplot(rows, cols, i + 1)
        cluster_profile = cluster_means.loc[i].sort_values(ascending=False)
        # Берем топ-3 языка в кластере
        top_languages = cluster_profile.head(3)
        colors = plt.cm.Set3(np.linspace(0, 1, len(top_languages)))
        bars = plt.bar(range(len(top_languages)), top_languages.values, color=colors)
        plt.title(f'Кластер {i}\n({len(clustered_data[clustered_data["cluster"] == i])} пользователей)')
        plt.xticks(range(len(top_languages)), top_languages.index, rotation=45, ha='right')
        plt.ylabel('Среднее количество решенных задач')
        plt.ylim(0, max(cluster_means.max()) * 1.1)  # Единая шкала для сравнения

        # Добавляем значения на столбцы
        for bar, value in zip(bars, top_languages.values):
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                     f'{value:.1f}', ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.show()

    # Тепловая карта кластеров (только топ-3 языка для каждого кластера)
    plt.figure(figsize=(12, 8))

    # Для каждого кластера берем только топ-3 языка
    top_languages_per_cluster = {}
    for i in range(n_clusters):
        cluster_profile = cluster_means.loc[i].sort_values(ascending=False)
        top_languages_per_cluster[i] = cluster_profile.head(3).index.tolist()

    # Собираем все уникальные языки из топ-3 всех кластеров
    all_top_languages = set()
    for langs in top_languages_per_cluster.values():
        all_top_languages.update(langs)

    # Создаем уменьшенную матрицу для тепловой карты
    heatmap_data = cluster_means[list(all_top_languages)]

    sns.heatmap(heatmap_data.T, annot=True, fmt='.1f', cmap='YlOrRd',
                cbar_kws={'label': 'Среднее количество решенных задач'})
    plt.title('Топ-3 языка для каждого кластера')
    plt.xlabel('Кластер')
    plt.ylabel('Язык программирования')
    plt.tight_layout()
    plt.show()

    return cluster_means


# Визуализация кластеров с помощью PCA
def visualize_clusters_pca(normalized_data, cluster_labels, user_language_filtered):
    """Визуализация кластеров с помощью PCA"""
    import matplotlib.colors as mcolors
    import numpy as np

    # Уменьшаем размерность до 2D для визуализации
    pca = PCA(n_components=2, random_state=42)
    pca_result = pca.fit_transform(normalized_data)

    # Обрабатываем метки кластеров - гарантируем целочисленные значения
    cluster_labels_clean = cluster_labels.astype(int)

    # Создаем DataFrame для удобства
    pca_df = pd.DataFrame({
        'PC1': pca_result[:, 0],
        'PC2': pca_result[:, 1],
        'cluster': cluster_labels_clean
    })

    unique_clusters = sorted(pca_df['cluster'].unique())
    print(f"Уникальные кластеры: {unique_clusters}")

    # ЯВНО ЗАДАЕМ ЦВЕТА ДЛЯ КАЖДОГО КЛАСТЕРА
    cluster_colors = {
        0: '#1f77b4',  # синий
        1: '#ff7f0e',  # оранжевый
        2: '#2ca02c',  # зеленый
        3: '#d62728',  # красный
        4: '#9467bd',  # фиолетовый
        5: '#8c564b',  # коричневый
        6: '#e377c2',  # розовый
        7: '#7f7f7f',  # серый
        8: '#bcbd22',  # желто-зеленый
        9: '#17becf'  # голубой
    }

    # Создаем список цветов для каждого кластера
    colors = [cluster_colors.get(cluster, '#000000') for cluster in pca_df['cluster']]

    # Визуализация с явными цветами
    plt.figure(figsize=(12, 8))
    scatter = plt.scatter(pca_df['PC1'], pca_df['PC2'],
                          c=colors, alpha=0.7, s=15, edgecolors='white', linewidth=0.3)

    # Создаем кастомную легенду
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=cluster_colors[cluster],
                             label=f'Кластер {cluster}') for cluster in unique_clusters]

    plt.legend(handles=legend_elements, title='Кластеры',
               bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.title('Визуализация кластеров (PCA)')
    plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%} дисперсии)')
    plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%} дисперсии)')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

    print(f"Объясненная дисперсия PCA: {pca.explained_variance_ratio_.sum():.2%}")
# Детальный анализ каждого кластера - только по 3 языка
def detailed_cluster_analysis(clustered_data, cluster_means, n_clusters):
    """Детальный анализ каждого кластера - только по 3 языка"""
    print("\n" + "=" * 80)
    print("ДЕТАЛЬНЫЙ АНАЛИЗ КЛАСТЕРОВ (ТОП-3 ЯЗЫКА)")
    print("=" * 80)

    for cluster_id in range(n_clusters):
        cluster_data = clustered_data[clustered_data['cluster'] == cluster_id]
        cluster_size = len(cluster_data)

        print(f"\n--- Кластер {cluster_id} ({cluster_size} пользователей) ---")

        # Топ-3 языков в кластере
        cluster_languages = cluster_means.loc[cluster_id].sort_values(ascending=False)
        top_languages = cluster_languages.head(3)

        print("Характерные языки (топ-3):")
        for lang, score in top_languages.items():
            if score > 0:
                users_with_lang = (cluster_data[lang] > 0).sum()
                percentage = (users_with_lang / cluster_size) * 100
                print(f"  - {lang}: {score:.1f} средних решенных задач, "
                      f"{users_with_lang} пользователей ({percentage:.1f}%)")

        # Среднее количество языков на пользователя в кластере
        avg_languages = (cluster_data.drop('cluster', axis=1) > 0).sum(axis=1).mean()
        print(f"Среднее количество языков на пользователя: {avg_languages:.1f}")


# Основная функция
def main(file1_path, file2_path):
    """Основная функция выполнения кластеризации"""
    print("ЗАГРУЗКА ДАННЫХ...")
    df = load_data(file1_path, file2_path)

    print("\nПОДГОТОВКА МАТРИЦЫ ПОЛЬЗОВАТЕЛЬ-ЯЗЫК...")
    user_language = create_user_language_matrix(df)

    print("\nАНАЛИЗ ДАННЫХ...")
    language_stats = explore_data(user_language)

    print("\nПОДГОТОВКА ДАННЫХ ДЛЯ КЛАСТЕРИЗАЦИИ...")
    normalized_data, user_language_filtered, popular_languages = prepare_data(user_language, n_languages=17)

    print("\nПОИСК ОПТИМАЛЬНОГО КОЛИЧЕСТВА КЛАСТЕРОВ...")
    optimal_k = find_optimal_clusters(normalized_data)

    print("\nВЫПОЛНЕНИЕ КЛАСТЕРИЗАЦИИ...")
    kmeans, cluster_labels = perform_clustering(normalized_data, optimal_k)

    print("\nАНАЛИЗ КЛАСТЕРОВ...")
    cluster_means = analyze_clusters(user_language_filtered, cluster_labels, popular_languages, optimal_k)

    print("\nВИЗУАЛИЗАЦИЯ КЛАСТЕРОВ...")
    visualize_clusters_pca(normalized_data, cluster_labels, user_language_filtered)

    # Создаем clustered_data для детального анализа
    clustered_data = user_language_filtered.copy()
    clustered_data['cluster'] = cluster_labels

    print("\nДЕТАЛЬНЫЙ АНАЛИЗ...")
    detailed_cluster_analysis(clustered_data, cluster_means, optimal_k)

    # Сохраняем результаты
    clustered_data.to_csv('clustered_users_12_languages.csv', index=True)
    print(f"\nРезультаты сохранены в файл 'clustered_users_12_languages.csv'")

    return clustered_data, kmeans, cluster_means


# Запуск анализа
if __name__ == "__main__":
    file1_path = "../../results/language_stats.csv"
    file2_path = "../../results/language_stats2.csv"

    try:
        results = main(file1_path, file2_path)
        print("\nАнализ завершен успешно!")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        print("Убедитесь, что:")
        print("1. Файл данных существует по указанному пути")
        print("2. Файл имеет правильный формат CSV")
        print("3. Столбцы в файле соответствуют ожидаемым: username, languageName, problemsSolved")