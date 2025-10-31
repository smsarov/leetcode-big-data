from turtledemo.penrose import start
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time
import pandas as pd
import re


def setup_driver():
    """Настройка Chrome драйвера"""
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
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


def get_global_ranking(driver, pages_to_scrape=10):
    """Парсинг глобального рейтинга LeetCode с пагинацией"""
    try:
        start_page= 1
        driver.get(f"https://leetcode.com/contest/globalranking/{start_page}")

        # Ждем загрузки страницы
        wait = WebDriverWait(driver, 20)
        print("Ожидание загрузки страницы...")
        current_page = start_page
        # Ждем появления данных
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='bg-fill-quaternary']")))
        time.sleep(3)

        all_data = []
        while current_page <= (start_page+pages_to_scrape):
            print(f"\n=== Парсинг страницы {current_page} ===")

            # Ждем загрузки данных на странице
            time.sleep(3)

            # Находим все строки с участниками
            try:
                rows = driver.find_elements(By.CSS_SELECTOR, "[class*='bg-fill-quaternary']")
                if not rows:
                    break

                # Парсим каждую строку
                successful_parses = 0
                for i, row in enumerate(rows):
                    user_data = parse_user_row(row)
                    if user_data:
                        user_data['page'] = current_page
                        all_data.append(user_data)
                        successful_parses += 1

                print(f"Успешно распарсено: {successful_parses}/{len(rows)}")
            except Exception as e:
                print(f"Ошибка при парсинге страницы {current_page}: {e}")
                break

            # Переход на следующую страницу
            if current_page < (start_page+pages_to_scrape):
                try:
                    # Находим кнопку next
                    next_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='next']:not([disabled])")

                    if next_button.is_enabled():
                        print(f"Переход на страницу {current_page + 1}...")
                        driver.execute_script("arguments[0].click();", next_button)

                        # Ждем обновления страницы
                        time.sleep(3)
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='bg-fill-quaternary']")))
                        current_page += 1
                    else:
                        print("Кнопка next заблокирована")
                        break

                except NoSuchElementException:
                    print("Кнопка next не найдена")
                    break
                except Exception as e:
                    print(f"Ошибка при переходе на следующую страницу: {e}")
                    break
            else:
                break

        return all_data

    except TimeoutException:
        print("Таймаут при загрузке страницы")
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

    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"Данные сохранены в {filename}")
    print(f"Всего записей: {len(df)}")
    return df


def main():
    driver = setup_driver()
    try:
        ranking_data = get_global_ranking(driver, pages_to_scrape=10)
        if ranking_data:
            df = save_to_csv(ranking_data)
        else:
            print("Не удалось получить данные")

    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        input("Нажмите Enter для закрытия браузера...")
        driver.quit()
        print("Парсинг завершен")


if __name__ == "__main__":
    main()