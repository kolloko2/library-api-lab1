# Git-процесс и сценарий защиты

## Путь изменения

`Issue → feature-ветка → несколько коммитов → Pull Request → проверка → merge в main → тег v0.1.0`.

Реализованная демонстрационная функция: выдача и возврат экземпляров:

- задача: [Issue #1](https://github.com/kolloko2/library-api-lab1/issues/1);
- ветка: `feature/1-loans`;
- запрос на слияние и проверка: [Pull Request #2](https://github.com/kolloko2/library-api-lab1/pull/2);
- merge-коммит PR: `143d65c`;
- релиз: тег `v0.1.0`.

## Смоделированный конфликт

Конфликт создан учебными изменениями одной строки в `docs/conflict-demo.txt` в двух ветках. В feature-ветке был записан лимит `4`, в `main` — `5`. При слиянии Git остановился на конфликте; итоговое значение `5` выбрано согласно ТЗ и переменной `MAX_ACTIVE_LOANS`. Разрешение зафиксировано merge-коммитом `96683ca`, поэтому его можно показать командами:

```bash
git log --graph --oneline --all
git show --cc 96683ca
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
