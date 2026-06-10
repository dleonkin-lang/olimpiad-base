# База олимпиадных задач 5–7

Статическая HTML/JSON-база олимпиадных задач для 5–7 классов.

Текущая версия: `GITHUB-PAGES-BG-PREVIEW-UI-2026-06-10-237`.

- Задач: **237**
- Источников: **51**
- Публичная версия: `docs/index.html`
- Рабочая версия с локальным редактированием: `docs/admin.html`
- JSON базы: `docs/data/olympiad_problems_237.json`
- Полный JSON-бэкап: `docs/data/olympiad_database_full_backup.json`
- Каталог источников: `docs/data/olympiad_source_catalog.json`

## Как задеплоить на GitHub Pages

1. Создать новый репозиторий на GitHub.
2. Распаковать этот архив в корень репозитория.
3. Сделать commit и push в ветку `main`.
4. В настройках репозитория открыть **Pages**.
5. Выбрать **Deploy from a branch**.
6. Branch: `main`, folder: `/docs`.
7. Сохранить настройки.

GitHub Pages будет публиковать содержимое папки `docs/`. Главная страница сайта — `docs/index.html`.

## Локальный просмотр

```bash
python3 -m http.server 8000 -d docs
```

После этого открыть в браузере:

- публичная версия: `http://localhost:8000/`
- рабочая версия: `http://localhost:8000/admin.html`

## Важное про редактирование

`docs/admin.html` — рабочая версия с редактированием, но изменения сохраняются только в `localStorage` браузера. Они не попадают в GitHub автоматически. После правок нужно экспортировать полный JSON и отдельно пересобрать/обновить HTML.

## Структура

```text
docs/                 # источник GitHub Pages
  index.html          # публичная read-only версия
  admin.html          # рабочая версия с редактированием
  data/               # JSON-экспорты и бэкапы
  assets/             # картинка фона для будущих правок
current_release/      # текущие исходные артефакты проекта с историческими именами
project_docs/         # инструкции для Codex и дальнейшей работы
source_materials/     # импортные материалы, PDF и рисунки, не публикуются Pages при source=/docs
tools/                # проверочные скрипты
```

## Проверка пакета

```bash
python3 tools/verify_static_bundle.py
```
