# Деплой на GitHub Pages

Рекомендуемый способ: публиковать папку `docs/` из ветки `main`.

## Шаги

```bash
git init
git add .
git commit -m "Initial deploy of olympiad task database"
git branch -M main
git remote add origin <URL_ВАШЕГО_РЕПОЗИТОРИЯ>
git push -u origin main
```

Затем на GitHub:

1. Repository → Settings → Pages.
2. Source / Build and deployment: Deploy from a branch.
3. Branch: `main`.
4. Folder: `/docs`.
5. Save.

После публикации:

- `/` откроет публичную read-only базу;
- `/admin.html` откроет рабочую версию с локальным редактированием.

## Проверка перед push

```bash
python3 tools/verify_static_bundle.py
```

Проверка должна подтвердить 237 задач, 51 источник, `CAN_EDIT=false` в публичной версии и `CAN_EDIT=true` в рабочей версии.
