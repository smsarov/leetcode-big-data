import os
import sys
import time
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Игнорируем предупреждения
warnings.filterwarnings('ignore')


def combine_datasets(file1_path, file2_path=None):
    """Объединяет один или два DataFrame с проверкой дубликатов."""
    try:
        df1 = pd.read_csv(file1_path)
    except FileNotFoundError:
        print(f"Файл с solved_stats не найден: {file1_path}")
        return None
    except Exception as e:
        print(f"Ошибка при загрузке {file1_path}: {e}")
        return None

    if file2_path and os.path.exists(file2_path):
        try:
            df2 = pd.read_csv(file2_path)
            combined_df = pd.concat([df1, df2], ignore_index=True)
        except Exception as e:
            print(f"Ошибка при загрузке {file2_path}, используем только первый файл: {e}")
            combined_df = df1
    else:
        combined_df = df1

    print(f"После объединения: {len(combined_df)} пользователей")
    # Проверяем на дубликаты по username
    duplicate_usernames = combined_df["username"].duplicated().sum()
    if duplicate_usernames > 0:
        print(f"Найдено {duplicate_usernames} дубликатов username!")
        # Удаляем дубликаты, оставляем первую запись
        combined_df = combined_df.drop_duplicates(subset=["username"], keep="first")
        print(f"После удаления дубликатов: {len(combined_df)} пользователей")

    return combined_df


# Объединяем датасеты
print("=== ОБЪЕДИНЕНИЕ ДАТАСЕТОВ ===")

base_out = os.getenv("OUT_DIR")
if base_out:
    file1_default = os.path.join(base_out, "dataset", "user-data", "solved_stats.csv")
    file2_default = os.path.join(base_out, "dataset", "user-data", "solved_stats2.csv")
else:
    # Фоллбек для старой структуры / локального запуска
    file1_default = "../../results/solved_stats.csv"
    file2_default = "../../results/solved_stats2.csv"

df_combined = combine_datasets(file1_default, file2_default if os.path.exists(file2_default) else None)

if df_combined is None or df_combined.empty:
    print("Нет данных solved_stats для обучения модели, скрипт predictional_model завершает работу")
    sys.exit(0)

def create_features(df):
    """
    Создаем признаки из исходных данных
    """
    df_features = df.copy()

    numeric_columns = ['easy', 'medium', 'hard', 'ac_easy', 'ac_medium', 'ac_hard']
    for col in numeric_columns:
        df_features[col] = pd.to_numeric(df_features[col], errors='coerce')

    # Вычисляем успешность для каждого пользователя по каждой сложности
    df_features['success_rate_easy'] = np.where(
        df_features['easy'] > 0,
        df_features['ac_easy'] / df_features['easy'],
        0
    )
    df_features['success_rate_medium'] = np.where(
        df_features['medium'] > 0,
        df_features['ac_medium'] / df_features['medium'],
        0
    )
    df_features['success_rate_hard'] = np.where(
        df_features['hard'] > 0,
        df_features['ac_hard'] / df_features['hard'],
        0
    )

    # Базовые признаки
    df_features['total_attempted'] = df_features['easy'] + df_features['medium'] + df_features['hard']
    df_features['total_solved'] = df_features['ac_easy'] + df_features['ac_medium'] + df_features['ac_hard']

    # Общая успешность
    df_features['overall_success_rate'] = np.where(
        df_features['total_attempted'] > 0,
        df_features['total_solved'] / df_features['total_attempted'],
        0
    )

    # Распределение по сложностям
    df_features['easy_ratio'] = np.where(
        df_features['total_attempted'] > 0,
        df_features['easy'] / df_features['total_attempted'],
        0
    )
    df_features['medium_ratio'] = np.where(
        df_features['total_attempted'] > 0,
        df_features['medium'] / df_features['total_attempted'],
        0
    )
    df_features['hard_ratio'] = np.where(
        df_features['total_attempted'] > 0,
        df_features['hard'] / df_features['total_attempted'],
        0
    )

    # Логарифмические признаки
    df_features['log_total_attempted'] = np.log1p(df_features['total_attempted'])
    df_features['log_easy'] = np.log1p(df_features['easy'])
    df_features['log_medium'] = np.log1p(df_features['medium'])
    df_features['log_hard'] = np.log1p(df_features['hard'])

    return df_features


def advanced_bayesian_smoothing(df):
    """Продвинутое байесовское сглаживание с учетом сложности"""
    df_smoothed = df.copy()

    # Разные параметры сглаживания для разных сложностей
    smoothing_params = {
        'easy': {'alpha': 10, 'beta': 2},  # Для Easy - больше уверенности в успехе
        'medium': {'alpha': 5, 'beta': 5},  # Для Medium - баланс
        'hard': {'alpha': 2, 'beta': 10}  # Для Hard - больше уверенности в неудаче
    }

    for difficulty in ['easy', 'medium', 'hard']:
        alpha = smoothing_params[difficulty]['alpha']
        beta = smoothing_params[difficulty]['beta']

        # Проверяем, что есть данные для этой сложности
        total_attempts = df[difficulty].sum()
        if total_attempts > 0:
            global_success = df[f'ac_{difficulty}'].sum() / total_attempts
        else:
            global_success = 0.5  # Значение по умолчанию

        # Применяем байесовское сглаживание
        df_smoothed[f'success_rate_{difficulty}'] = (
            df[f'ac_{difficulty}'] + alpha * global_success
        ) / (df[difficulty] + alpha + beta)

    return df_smoothed


def prepare_training_data(df):
    """
    Подготавливаем данные для обучения модели
    Каждый пользователь будет представлен тремя примерами (по одному для каждой сложности)
    """
    training_samples = []

    for _, user in df.iterrows():
        # Пропускаем пользователей с малым опытом
        if user['total_attempted'] <= 5:
            continue

        # Для каждой сложности создаем отдельный пример
        for difficulty in ['Easy', 'Medium', 'Hard']:
            # Определяем целевую переменную (успешность для данной сложности)
            if difficulty == 'Easy':
                target = user['success_rate_easy']
                weight = user['easy']  # Вес пропорционален количеству попыток
            elif difficulty == 'Medium':
                target = user['success_rate_medium']
                weight = user['medium']
            else:  # Hard
                target = user['success_rate_hard']
                weight = user['hard']

            # Пропускаем, если не было попыток по этой сложности
            if weight == 0:
                continue

            # Создаем пример для обучения
            sample = {
                # Базовые признаки
                'total_attempted': user['total_attempted'],
                'total_solved': user['total_solved'],
                'overall_success_rate': user['overall_success_rate'],

                # Признаки специализации
                'easy_ratio': user['easy_ratio'],
                'medium_ratio': user['medium_ratio'],
                'hard_ratio': user['hard_ratio'],

                # Логарифмические признаки
                'log_total_attempted': user['log_total_attempted'],
                'log_easy': user['log_easy'],
                'log_medium': user['log_medium'],
                'log_hard': user['log_hard'],

                # Признаки сложности (one-hot encoding)
                'difficulty_Easy': 1 if difficulty == 'Easy' else 0,
                'difficulty_Medium': 1 if difficulty == 'Medium' else 0,
                'difficulty_Hard': 1 if difficulty == 'Hard' else 0,

                # Целевая переменная и вес
                'target': target,
                'weight': weight,
                'username': user['username']
            }

            training_samples.append(sample)

    return pd.DataFrame(training_samples)
df_with_features = create_features(df_combined)
df_smoothed = advanced_bayesian_smoothing(df_with_features)

# 4. Подготавливаем данные для обучения из сглаженных данных
print("\n=== ПОДГОТОВКА ДАННЫХ ДЛЯ ОБУЧЕНИЯ ===")
training_df = prepare_training_data(df_smoothed)
training_df.to_csv('training_data.csv', index=False)
print(f"Создано {len(training_df)} примеров для обучения")

def check_and_fix_nan(df):
    """Проверяет и исправляет NaN значения в данных"""

    # Проверяем наличие NaN
    nan_count = df.isnull().sum().sum()

    if nan_count > 0:
        df_fixed = df.fillna(0)

        return df_fixed
    else:
        return df


def prepare_for_training(training_df, test_size=0.2, random_state=42):
    """
    Подготавливает данные для обучения моделей
    """

    # Убираем username - это не признак для модели
    features_df = training_df.drop(columns=['username'])

    # Определяем признаки (X) и целевую переменную (y)
    feature_columns = [col for col in features_df.columns if col not in ['target', 'weight']]
    X = features_df[feature_columns]
    y = features_df['target']
    weights = features_df['weight']


    # Разделяем на train/test с стратификацией по сложности
    X_train, X_test, y_train, y_test, weights_train, weights_test = train_test_split(
        X, y, weights,
        test_size=test_size,
        random_state=random_state,
        stratify=X[['difficulty_Easy', 'difficulty_Medium', 'difficulty_Hard']]
    )

    print(f"\nРазделение данных:")
    print(f"  Обучающая выборка: {len(X_train):,} примеров")
    print(f"  Тестовая выборка:  {len(X_test):,} примеров")

    # Масштабируем признаки
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    return (X_train_scaled, X_test_scaled, y_train, y_test,
            weights_train, weights_test, scaler, feature_columns)


# Проверяем и исправляем данные
training_df_fixed = check_and_fix_nan(training_df)

# Подготавливаем данные для обучения
(X_train, X_test, y_train, y_test,
 weights_train, weights_test, scaler, feature_columns) = prepare_for_training(training_df_fixed)


def train_and_evaluate_models(X_train, X_test, y_train, y_test, weights_train):
    """
    Обучает несколько моделей и сравнивает их производительность
    """
    models = {
        'Linear Regression': LinearRegression(),
        'Ridge Regression': Ridge(alpha=1.0),
        'Random Forest': RandomForestRegressor(
            n_estimators=100,
            random_state=42,
            n_jobs=-1,
            max_depth=10
        ),
        'Gradient Boosting': GradientBoostingRegressor(
            n_estimators=100,
            random_state=42,
            max_depth=6,
            learning_rate=0.1
        )
    }

    results = {}

    print("\n=== ОБУЧЕНИЕ И ОЦЕНКА МОДЕЛЕЙ ===")
    print("Модель                 | Train MAE | Test MAE  | Train R² | Test R²  | Время")
    print("-" * 85)

    for name, model in models.items():
        start_time = time.time()

        try:
            # Обучаем модель с весами (если поддерживается)
            if hasattr(model, 'fit') and 'sample_weight' in model.fit.__code__.co_varnames:
                model.fit(X_train, y_train, sample_weight=weights_train)
            else:
                model.fit(X_train, y_train)

            # Предсказания
            y_pred_train = model.predict(X_train)
            y_pred_test = model.predict(X_test)

            # Оценка качества
            train_mae = mean_absolute_error(y_train, y_pred_train)
            test_mae = mean_absolute_error(y_test, y_pred_test)
            train_r2 = r2_score(y_train, y_pred_train)
            test_r2 = r2_score(y_test, y_pred_test)

            training_time = time.time() - start_time

            results[name] = {
                'model': model,
                'train_mae': train_mae,
                'test_mae': test_mae,
                'train_r2': train_r2,
                'test_r2': test_r2,
                'predictions': y_pred_test,
                'time': training_time
            }

            print(
                f"{name:<20} | {train_mae:9.4f} | {test_mae:9.4f} | {train_r2:8.4f} | {test_r2:8.4f} | {training_time:5.2f}с")

        except Exception as e:
            print(f"{name:<20} | Ошибка: {e}")

    return results


# Обучаем и оцениваем модели
results = train_and_evaluate_models(X_train, X_test, y_train, y_test, weights_train)


def analyze_results(results):
    """Анализирует результаты и выбирает лучшую модель"""

    print("\n" + "=" * 60)
    print("АНАЛИЗ РЕЗУЛЬТАТОВ И ВЫБОР ЛУЧШЕЙ МОДЕЛИ")
    print("=" * 60)

    # Находим лучшую модель по test MAE (меньше - лучше)
    best_model_name = min(results.keys(), key=lambda x: results[x]['test_mae'])
    best_result = results[best_model_name]

    print(f"ЛУЧШАЯ МОДЕЛЬ: {best_model_name}")
    print(f"   Test MAE: {best_result['test_mae']:.4f}")
    print(f"   Test R²:  {best_result['test_r2']:.4f}")
    print(f"   Время обучения: {best_result['time']:.2f}с")

    # Интерпретация MAE
    mae_interpretation = {
        'Отлично': (0, 0.02),  # Ошибка < 2%
        'Хорошо': (0.02, 0.05),  # Ошибка 2-5%
        'Удовлетворительно': (0.05, 0.1),  # Ошибка 5-10%
        'Плохо': (0.1, 1.0)  # Ошибка > 10%
    }

    mae = best_result['test_mae']
    for category, (low, high) in mae_interpretation.items():
        if low <= mae < high:
            print(f"   Качество: {category} (ошибка {mae * 100:.1f}%)")
            break

    # Сравнение всех моделей
    print(f"\nСРАВНЕНИЕ МОДЕЛЕЙ (по Test MAE):")
    sorted_models = sorted(results.items(), key=lambda x: x[1]['test_mae'])
    for i, (name, result) in enumerate(sorted_models, 1):
        print(f"   {i}. {name:<20} - MAE: {result['test_mae']:.4f}, R²: {result['test_r2']:.4f}")

    return best_model_name, results[best_model_name]


best_model_name, best_result = analyze_results(results)


def visualize_results(results, y_test, best_model_name):
    """Визуализирует результаты моделей"""

    plt.style.use('seaborn-v0_8')
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    # 1. Сравнение MAE моделей
    models = list(results.keys())
    train_mae = [results[name]['train_mae'] for name in models]
    test_mae = [results[name]['test_mae'] for name in models]

    x = np.arange(len(models))
    width = 0.35

    bars1 = ax1.bar(x - width / 2, train_mae, width, label='Train MAE', alpha=0.7, color='skyblue')
    bars2 = ax1.bar(x + width / 2, test_mae, width, label='Test MAE', alpha=0.7, color='lightcoral')

    # Подсвечиваем лучшую модель
    best_idx = models.index(best_model_name)
    bars1[best_idx].set_color('blue')
    bars2[best_idx].set_color('red')

    ax1.set_xlabel('Модели')
    ax1.set_ylabel('MAE (меньше - лучше)')
    ax1.set_title('Сравнение MAE моделей')
    ax1.set_xticks(x)
    ax1.set_xticklabels(models, rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Добавляем значения на столбцы
    for bar in bars1 + bars2:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2., height + 0.001,
                 f'{height:.3f}', ha='center', va='bottom', fontsize=8)

    # 2. Сравнение R² моделей
    train_r2 = [results[name]['train_r2'] for name in models]
    test_r2 = [results[name]['test_r2'] for name in models]

    bars3 = ax2.bar(x - width / 2, train_r2, width, label='Train R²', alpha=0.7, color='lightgreen')
    bars4 = ax2.bar(x + width / 2, test_r2, width, label='Test R²', alpha=0.7, color='orange')

    # Подсвечиваем лучшую модель
    bars3[best_idx].set_color('green')
    bars4[best_idx].set_color('darkorange')

    ax2.set_xlabel('Модели')
    ax2.set_ylabel('R² (больше - лучше)')
    ax2.set_title('Сравнение R² моделей')
    ax2.set_xticks(x)
    ax2.set_xticklabels(models, rotation=45, ha='right')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # 3. Предсказания vs Фактические значения (лучшая модель)
    best_predictions = results[best_model_name]['predictions']

    scatter = ax3.scatter(y_test, best_predictions,
                          c=weights_test, alpha=0.6, s=10, cmap='viridis')
    ax3.plot([0, 1], [0, 1], 'r--', alpha=0.8, linewidth=2)
    ax3.set_xlabel('Фактическая успешность')
    ax3.set_ylabel('Предсказанная успешность')
    ax3.set_title(f'Предсказания vs Фактические значения\n({best_model_name})')
    ax3.grid(True, alpha=0.3)

    # Добавляем colorbar для весов
    plt.colorbar(scatter, ax=ax3, label='Вес (количество попыток)')

    # 4. Распределение ошибок предсказания
    errors = best_predictions - y_test
    ax4.hist(errors, bins=50, alpha=0.7, color='purple', edgecolor='black')
    ax4.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Идеальные предсказания')
    ax4.set_xlabel('Ошибка предсказания')
    ax4.set_ylabel('Частота')
    ax4.set_title('Распределение ошибок предсказания')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    # Добавляем статистику ошибок
    mean_error = errors.mean()
    std_error = errors.std()
    ax4.text(0.05, 0.95, f'Среднее: {mean_error:.4f}\nСт. отклонение: {std_error:.4f}',
             transform=ax4.transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.tight_layout()
    plt.show()

    return best_predictions, errors


best_predictions, errors = visualize_results(results, y_test, best_model_name)

# =============================================================================
# АНАЛИЗ НЕУДАЧНЫХ РЕЗУЛЬТАТОВ И ОШИБОК
# =============================================================================

print("\n" + "=" * 80)
print("АНАЛИЗ НЕУДАЧНЫХ РЕЗУЛЬТАТОВ И ОШИБОК")
print("=" * 80)

# Анализ остатков для лучшей модели
best_predictions = best_result['predictions']
residuals = y_test - best_predictions

print(f"\nАНАЛИЗ ОСТАТКОВ ДЛЯ ЛУЧШЕЙ МОДЕЛИ ({best_model_name}):")
print(f"   Средний остаток: {residuals.mean():.6f}")
print(f"   Стандартное отклонение остатков: {residuals.std():.6f}")
print(f"   Максимальная положительная ошибка: {residuals.max():.6f}")
print(f"   Максимальная отрицательная ошибка: {residuals.min():.6f}")

# Анализ худших предсказаний
worst_predictions_idx = np.argsort(np.abs(residuals))[-20:]  # 20 худших предсказаний

print(f"\nАНАЛИЗ 5 ХУДШИХ ПРЕДСКАЗАНИЙ:")
worst_data = []
for idx in worst_predictions_idx[-5:]:
    worst_data.append({
        'actual': y_test.iloc[idx],
        'predicted': best_predictions[idx],
        'error': residuals.iloc[idx],
        'abs_error': abs(residuals.iloc[idx])
    })

worst_df = pd.DataFrame(worst_data)
print(worst_df.to_string(index=False))

# =============================================================================
# СОХРАНЕНИЕ МОДЕЛИ И РЕЗУЛЬТАТОВ
# =============================================================================

import joblib
import json


def save_model_and_results(best_model, best_model_name, scaler, feature_columns, results, file_prefix='model'):
    """Сохраняет модель и результаты обучения"""

    # Сохраняем модель
    model_filename = f'{file_prefix}_{best_model_name.lower().replace(" ", "_")}.pkl'
    joblib.dump(best_model, model_filename)
    print(f" Модель сохранена как: {model_filename}")

    # Сохраняем scaler
    scaler_filename = f'{file_prefix}_scaler.pkl'
    joblib.dump(scaler, scaler_filename)
    print(f"Scaler сохранен как: {scaler_filename}")

    # Сохраняем информацию о признаках
    features_info = {
        'feature_columns': feature_columns,
        'best_model': best_model_name,
        'training_date': str(pd.Timestamp.now()),
        'performance': {
            'test_mae': results[best_model_name]['test_mae'],
            'test_r2': results[best_model_name]['test_r2']
        }
    }

    features_filename = f'{file_prefix}_features_info.json'
    with open(features_filename, 'w', encoding='utf-8') as f:
        json.dump(features_info, f, indent=2, ensure_ascii=False)
    print(f"Информация о признаках сохранена как: {features_filename}")

    return model_filename, scaler_filename, features_filename


# Сохраняем модель и результаты
model_file, scaler_file, features_file = save_model_and_results(
    best_result['model'], best_model_name, scaler, feature_columns, results
)

