#!/usr/bin/env bash

set -euo pipefail

#############################################
# Конфигурация (подправь под свой репозиторий)
#############################################

# URL репозитория с кодом пайплайна
REPO_URL="https://github.com/smsarov/leetcode-big-data.git"

# Каталог, куда по умолчанию будет клонироваться репозиторий
DEFAULT_REPO_DIR="$(pwd)/bigdata-pipeline"

# Каталог вывода данных по умолчанию (dataset/, results/ и т.п.)
DEFAULT_OUT_DIR="$(pwd)/output"

#############################################

OUT_DIR="$DEFAULT_OUT_DIR"
REPO_DIR="$DEFAULT_REPO_DIR"
TEST_MODE="0"
LOCAL_MODE="0"

usage() {
  echo "Usage: $0 [-out /path/to/output] [-repo /path/to/repo_dir] [--test] [--local]"
  echo "  -out  : каталог, куда будут записаны dataset/ и results/ (по умолчанию $DEFAULT_OUT_DIR)"
  echo "  -repo : каталог, куда будет клонирован репозиторий (по умолчанию $DEFAULT_REPO_DIR)"
  echo "  --test: тестовый режим (ограниченное количество страниц и пользователей)"
  echo "  --local: использовать текущую директорию как репозиторий (без клонирования)"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -out)
      OUT_DIR="$2"
      shift 2
      ;;
    -repo)
      REPO_DIR="$2"
      shift 2
      ;;
    --test|-t)
      TEST_MODE="1"
      shift 1
      ;;
    --local|-l)
      LOCAL_MODE="1"
      shift 1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Неизвестный аргумент: $1"
      usage
      exit 1
      ;;
  esac
done

OUT_DIR="$(cd "$(dirname "$OUT_DIR")" && pwd)/$(basename "$OUT_DIR")"
REPO_DIR="$(cd "$(dirname "$REPO_DIR")" && pwd)/$(basename "$REPO_DIR")"

echo "Каталог репозитория: $REPO_DIR"
echo "Каталог вывода данных: $OUT_DIR"
if [ "$TEST_MODE" = "1" ]; then
  echo "Режим: ТЕСТОВЫЙ (ограниченное количество страниц рейтинга и пользователей)"
else
  echo "Режим: ПОЛНЫЙ (весь рейтинг и все пользователи)"
fi

mkdir -p "$OUT_DIR"

#############################################
# Проверка наличия docker / docker compose
#############################################

if ! command -v docker >/dev/null 2>&1; then
  echo "Ошибка: docker не установлен или не найден в PATH"
  exit 1
fi

if command -v docker compose >/dev/null 2>&1; then
  DOCKER_COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  DOCKER_COMPOSE="docker-compose"
else
  echo "Ошибка: не найден docker compose (ни 'docker compose', ни 'docker-compose')"
  exit 1
fi

#############################################
# Клонирование / обновление репозитория
#############################################

if [ "$LOCAL_MODE" = "1" ]; then
  # Режим локального запуска: используем текущую директорию
  if [ ! -d ".git" ]; then
    echo "Ошибка: --local требует, чтобы текущая директория была git-репозиторием"
    exit 1
  fi
  REPO_DIR="$(pwd)"
  echo "Используется локальный репозиторий: $REPO_DIR"
elif [ ! -d "$REPO_DIR/.git" ]; then
  if ! command -v git >/dev/null 2>&1; then
    echo "Ошибка: git не установлен, а репозиторий ещё не склонирован."
    echo "Либо установите git, либо заранее скачайте репозиторий в $REPO_DIR."
    exit 1
  fi
  echo "Клонирую репозиторий из $REPO_URL в $REPO_DIR ..."
  git clone "$REPO_URL" "$REPO_DIR"
else
  echo "Репозиторий уже существует в $REPO_DIR, попытаюсь обновить (git pull)..."
  if command -v git >/dev/null 2>&1; then
    (cd "$REPO_DIR" && git pull --rebase || true)
  fi
fi

cd "$REPO_DIR"

#############################################
# Привязка каталога вывода к docker-compose
#############################################

# В docker-compose.yml ожидается volume ./output:/data/out
# Сделаем ./output символической ссылкой на желаемый OUT_DIR
rm -rf output
ln -s "$OUT_DIR" output

echo "Запуск docker compose для сервиса pipeline..."
if [ "$TEST_MODE" = "1" ]; then
  RUN_TEST=1 $DOCKER_COMPOSE up --build pipeline
else
  $DOCKER_COMPOSE up --build pipeline
fi


