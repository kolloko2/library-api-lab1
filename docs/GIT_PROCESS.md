# Git-процесс и сценарий защиты

## Путь изменения

`Issue → feature-ветка → несколько коммитов → Pull Request → проверка → merge в main → тег v0.1.0`.

Реализованная демонстрационная функция: выдача и возврат экземпляров. Ссылка на задачу и PR указана в истории удалённого репозитория.

## Смоделированный конфликт

Конфликт создаётся учебными изменениями одной строки в `docs/conflict-demo.txt` в двух ветках. В feature-ветке записан лимит `4`, в `main` — `5`. При слиянии Git останавливается на конфликте; итоговое значение `5` выбирается согласно ТЗ и переменной `MAX_ACTIVE_LOANS`. Разрешение фиксируется отдельным merge-коммитом, поэтому его можно показать командами:

```bash
git log --graph --oneline --all
git show --cc <merge-commit>
```

## Приёмка небольшого изменения на защите

```bash
git switch main
git pull
git switch -c fix/<номер-задачи>-short-name
# изменить код/документацию
pytest -q
python -m compileall app
git add <конкретные-файлы>
git commit -m "fix: краткое описание"
git push -u origin HEAD
gh pr create --fill
```

После проверки PR сливается через интерфейс GitHub или `gh pr merge --merge`.

## Проверка секретов

```bash
git check-ignore -v .env library.db .venv/
git ls-files | grep -E '(^|/)(\.env|.*\.db|\.venv)' # вывод должен быть пустым
```

