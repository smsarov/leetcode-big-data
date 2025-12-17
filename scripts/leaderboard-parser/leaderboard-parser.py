import os
import argparse
import time
import re

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException


def setup_driver():
    """Настройка Chrome драйвера (headless по умолчанию)"""
    chrome_options = Options()
    # В продакшене работаем в headless-режиме, но даём возможность отключить через переменную
    headless = os.getenv("HEADLESS", "1") != "0"
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    # Более человеческий User-Agent, чтобы снизить шанс блокировки
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )

    binary_path = os.getenv("CHROME_BINARY")
    if binary_path:
        chrome_options.binary_location = binary_path

    # Явно указываем путь к chromedriver, чтобы избежать ошибок Selenium Manager
    driver_path = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    service = ChromeService(executable_path=driver_path)

    driver = webdriver.Chrome(service=service, options=chrome_options)
    try:
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    except Exception:
        # Если по какой-то причине скрипт не выполнился, это не критично
        pass
    return driver


def parse_user_row(row):
    """Парсинг данных одного пользователя из строки"""
    try:
        # Парсим rank
        rank_elem = row.find_element(By.CSS_SELECTOR, "[class*='w-\\[65px\\]'] div:last-child")
        rank = rank_elem.text.strip()

        # Парсим username из ссылки
        try:
            link_elem = row.find_element(By.CSS_SELECTOR, "a[href*='/u/']")
            href = link_elem.get_attribute('href')
            username = href.split('/u/')[-1].split('/')[0] if '/u/' in href else "N/A"
        except NoSuchElementException:
            username = "N/A"

        # Парсим display name
        try:
            name_elem = row.find_element(By.CSS_SELECTOR, "a[href*='/u/']")
            display_name = name_elem.text.strip()
        except NoSuchElementException:
            display_name = "N/A"

        # Парсим score
        try:
            score_elem = row.find_element(By.XPATH,
                                          ".//div[contains(@class, 'min-w-[80px]')]//div[contains(@class, 'font-medium')]")
            score = score_elem.text.strip()
        except NoSuchElementException:
            try:
                score_elems = row.find_elements(By.XPATH, ".//div[contains(@class, 'font-medium')]")
                if len(score_elems) > 1:
                    score = score_elems[1].text.strip()
                else:
                    score = "N/A"
            except:
                score = "N/A"

        # Парсим country
        try:
            country_elem = row.find_element(By.CSS_SELECTOR, "span[title]")
            country = country_elem.get_attribute('title')
        except NoSuchElementException:
            country = "Not specified"

        # Парсим количество контестов
        try:
            contests_elem = row.find_element(By.CLASS_NAME, "text-xs")
            contests_text = contests_elem.text.strip()
            contests_match = re.search(r'(\d+)\s*contest', contests_text)
            contests_attended = contests_match.group(1) if contests_match else "0"
        except NoSuchElementException:
            contests_attended = "0"


        return {
            'global_rank': rank,
            'username': username,
            'display_name': display_name,
            'score': score,
            'country': country,
            'contests_attended': contests_attended
        }

    except Exception as e:
        print(f"Ошибка при парсинге строки: {e}")
        return None


def get_global_ranking(driver, max_pages: int | None = None):
    """
    Парсинг глобального рейтинга LeetCode с пагинацией.
    Если max_pages is None — идём до тех пор, пока есть страницы.
    """
    try:
        start_page = 1
        driver.get(f"https://leetcode.com/contest/globalranking/{start_page}")

        # Ждем загрузки страницы (таймаут можно настроить через LEETCODE_WAIT_SEC)
        wait_seconds = int(os.getenv("LEETCODE_WAIT_SEC", "60"))
        wait = WebDriverWait(driver, wait_seconds)
        print("Ожидание загрузки страницы...")
        current_page = start_page
        # Ждем появления хотя бы одной ссылки на профиль пользователя
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/u/']")))
        time.sleep(3)

        all_data = []
        page_counter = 0

        while True:
            print(f"\n=== Парсинг страницы {current_page} ===")

            # Ждем загрузки данных на странице
            time.sleep(3)

            # Находим все строки с участниками
            try:
                rows = driver.find_elements(By.CSS_SELECTOR, "[class*='bg-fill-quaternary']")
                if not rows:
                    print("Строки с участниками не найдены, выходим из цикла пагинации")
                    break

                # Парсим каждую строку
                successful_parses = 0
                for i, row in enumerate(rows):
                    user_data = parse_user_row(row)
                    if user_data:
                        user_data["page"] = current_page
                        all_data.append(user_data)
                        successful_parses += 1

                print(f"Успешно распарсено: {successful_parses}/{len(rows)}")
            except Exception as e:
                # Ошибку на странице просто логируем и пробуем перейти дальше
                print(f"Ошибка при парсинге страницы {current_page}: {e}")

            page_counter += 1
            if max_pages is not None and page_counter >= max_pages:
                print(f"Достигнут лимит страниц ({max_pages}), прекращаем парсинг")
                break

            # Переход на следующую страницу
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='next']:not([disabled])")

                if next_button.is_enabled():
                    print(f"Переход на страницу {current_page + 1}...")
                    driver.execute_script("arguments[0].click();", next_button)

                    # Ждем обновления страницы
                    time.sleep(3)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='bg-fill-quaternary']")))
                    current_page += 1
                    continue
                else:
                    print("Кнопка next заблокирована, завершаем парсинг")
                    break

            except NoSuchElementException:
                print("Кнопка next не найдена, завершаем парсинг")
                break
            except Exception as e:
                print(f"Ошибка при переходе на следующую страницу: {e}")
                break

        return all_data

    except TimeoutException:
        print("Таймаут при загрузке страницы")
        try:
            html_preview = driver.page_source[:5000]
            print("Фрагмент HTML страницы (для отладки):")
            print(html_preview)
        except Exception:
            pass
        return []
    except Exception as e:
        print(f"Ошибка при получении глобального рейтинга: {e}")
        return []


def save_to_csv(data, filename='leetcode_global_ranking.csv'):
    """Сохранение данных в CSV файл"""
    if not data:
        print("Нет данных для сохранения")
        return None

    df = pd.DataFrame(data)

    # Убираем дубликаты по username
    df = df.drop_duplicates(subset=['username'], keep='first')

    # Сортируем по рангу
    df['global_rank_num'] = pd.to_numeric(df['global_rank'], errors='coerce')
    df = df.sort_values('global_rank_num').drop('global_rank_num', axis=1)

    df.to_csv(filename, index=False, encoding="utf-8")
    print(f"Данные сохранены в {filename}")
    print(f"Всего записей: {len(df)}")
    return df


def run_leaderboard_scrape(output_path: str, max_pages: int | None = None):
    """
    Высокоуровневая функция для внешнего использования.
    Никогда не выбрасывает исключения наружу.
    """
    driver = None
    try:
        driver = setup_driver()
        ranking_data = get_global_ranking(driver, max_pages=max_pages)
        if ranking_data:
            save_to_csv(ranking_data, filename=output_path)
        else:
            print("Не удалось получить данные глобального рейтинга или список пуст")
    except Exception as e:
        print(f"Необработанная ошибка при парсинге глобального рейтинга: {e}")
    finally:
        try:
            if driver is not None:
                driver.quit()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(
        description="Парсер глобального рейтинга LeetCode."
    )
    parser.add_argument(
        "--output",
        "-o",
        dest="output",
        default="leetcode_global_ranking.csv",
        help="Путь к CSV-файлу для сохранения результатов",
    )
    parser.add_argument(
        "--max-pages",
        dest="max_pages",
        type=int,
        default=None,
        help="Максимальное количество страниц для парсинга (по умолчанию без ограничения)",
    )
    args = parser.parse_args()

    run_leaderboard_scrape(args.output, max_pages=args.max_pages)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Unexpected error in leaderboard main(): {e}")