# Структура проекта

```text
docs/
  index.html
  admin.html
  data/
    olympiad_problems_237.json
    olympiad_database_full_backup.json
    olympiad_source_catalog.json
  assets/
    mathematical_revolution_in_marching_unity.png
current_release/
  olympiad_taxonomy_prototype.html
  olympiad_public_readonly.html
  olympiad_problems_237.json
  olympiad_database_full_backup.json
  olympiad_source_catalog.json
project_docs/
  CODEX_PROMPT_READONLY.md
  PROJECT_STRUCTURE.md
  DEPLOY_GITHUB_PAGES.md
  WORKFLOW.md
source_materials/
  imports/
  source_pdfs/
  figures/
  assets/
tools/
  verify_static_bundle.py
```

## Основные входные точки

- `docs/index.html` — публичная read-only версия для GitHub Pages.
- `docs/admin.html` — рабочая версия с локальным редактированием.
- `current_release/olympiad_public_readonly.html` — тот же публичный артефакт с историческим именем.
- `current_release/olympiad_taxonomy_prototype.html` — тот же рабочий артефакт с историческим именем.

## Данные

HTML-файлы являются автономными: внутри каждого есть блок `const DATA = ...`.
JSON-файлы в `docs/data/` и `current_release/` нужны для резервного копирования, проверки и будущей пересборки.

Текущие инварианты:

- 237 задач;
- 51 источник;
- публичный HTML: `CAN_EDIT = false`;
- рабочий HTML: `CAN_EDIT = true`.

## Интерфейс

Проект написан как один статический HTML-файл с CSS и JavaScript без сборщика. Основные функции находятся в `<script>`:

- навигация по разделам;
- фильтрация задач;
- карточки и полноэкранный просмотр задачи;
- конструктор листочков;
- локальный редактор в `admin.html`;
- экспорт JSON;
- режим просмотра фона на 30 секунд.
