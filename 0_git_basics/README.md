# Семинарские занятия по теме git
_____

## Шпаргалка для нетерпеливых: 

Инициализировать репо:
```
cd project/
git init
```
Добавить комментарий после изменения файла main.py:
```
git add main.py
git commit -m "КАКОЙ-ТО КОММИТ"
```

Заливаем на github

      git push

Сливаем с github

      git pull

Удаляем ненужное:

      добавить venv/ в .gitignore
      git rm -r --cached venv

Добавить субмодуль в проект:

      git submodule add https://github.com/fa-python-network/3_Parallelism

## Начало

1. Поставь репозиторию звездочку
2. Сделай fork репозитория
3. Открой на своем компьютере папку для будущего проекта
4. Открой терминал в этой папке и склонируй удаленный репозиторий с помощью git clone
5. Открой проект с помощью Pycharm
6. Запусти основной файл


Для дальнейшей работы с удаленным репозиторием указываем данные вашего аккаунта:
```
git config —-local user.name "John Doe"

git config —-local user.email johndoe@example.com
```

1. Попробуй сделать изменение в файле binary_search.py
2. git add binary_search.py 
3. git commit -m "Something terribly misguided"
4. git reset HEAD~ - Undo last commit
5. Убираем свои изменения и добавляем где-то пробел, чтобы было что-то новенькое
6. git add .
7. git commit -m "Cool commit"
8. git push origin main

## Откат отправленного коммита на GitHub обратно

1. git push origin +62b182ac^:main , где 62b182ac - номер коммита, который хотим откатить
2. Убеждаемся, что пуш откатился

<h1> Теги... Теги! </h1>

1. git tag
2. git tag v1.0
3. git tag
4. git push origin v1.0
5. Видим тег в репозитории
6. git push —delete origin v1.0  - откатываем тег из репозитория

<h2> Возможные проблемы </h2>

Support for password authentication was removed on august 13 2021

Решение:

Settings => Developer Settings => Personal Access Token => Generate New Token 

Ставим галочки на весь repo и на read_org

Токен сгенерирован! Теперь вставляем его вместо пароля.

_______________

# Семинарская работа

Цель: Нам нужно смержить ветки, выполнив следующие команды:

```
git init

git add .

git commit -m " test this app"

git remote add origin https://github.com/username/0-git-basic.git

git push  origin master


git branch hello

git checkout hello

git add .

git commit -m " add hello to hello"

git push  origin hello

git checkout master

git merge hello

git push  origin master
```

Создаем каталог на компьютере где будет лежать наш проект
 - ![image](img/1.png)

 Создаем файл README.md
 - ![image](img/2.png)

Заполняем файл рандомным текстом, чтобы он не был пустым

 - ![image](img/3.png)

 Сохраняем файл, иначе пустой файл не запушится в репозиторий
 - ![image](img/4.png)
 
 
 Коммитим изменения

 Равносильно двум подряд командам 
       git add
       git commit

 - ![image](img/-2024-02-07_17-43-59.png)

 - ![image](img/-2024-02-07_17-44-26.png)

 - ![image](img/-2024-02-07_17-44-57.png)
 - ![image](img/-2024-02-07_17-45-22.png)
 - ![image](img/-2024-02-07_17-47-11.png)

 Пушим в репозиторий (если до этого настроили github в vscode)
 - ![image](img/-2024-02-07_17-47-40.png)
 - ![image](img/-2024-02-07_17-49-29.png)
  
  Если vscode не настроен, то список репозиториев будет недоступен.

 - ![image](img/-2024-02-07_17-58-31.png)

  Тогда идём создавать репозиторий вручную на сайт githib.com
 - ![image](img/-2024-02-07_18-21-05.png)
 - ![image](img/-2024-02-07_18-21-25.png)


 - ![image](img/-2024-02-07_18-21-55.png)
 - ![image](img/-2024-02-07_18-22-29.png)
  
  Теперь выбираем из списка только что созданный репозиторий 
  
  
  
 В строке должны увидеть список своих репозиториев.
  Если списка нет, то настраиваем аутентификацию с github

  ```
  git config --global user.name "vladimir"
  git config --global user.email "email@address.com"
  ```

  и пушим в него


 - ![image](img/-2024-02-07_18-23-11.png)

Идём смотреть, что получилось. Обращаем внимание на ветку master
 - ![image](img/-2024-02-07_18-25-23.png)

Создаем файл hello.py
 - ![image](img/-2024-02-07_18-28-22.png)
 Создаем новую ветку (git branch hello), переключаемся на неё (git checkout hello) 
 - ![image](img/-2024-02-07_18-30-15.png)
 Пушим изменения в репозиторий ветку hello , наблюдаем что там на github
 - ![image](img/-2024-02-07_18-31-33.png)
 - ![image](img/-2024-02-07_18-31-53.png)
 - ![image](img/-2024-02-07_18-32-17.png)
 Переключаемся в ветку master (git checkout master)
 - ![image](img/-2024-02-07_18-32-59.png)
 - ![image](img/-2024-02-07_18-33-26.png)
 Сливаем ветку hello в master
 - ![image](img/-2024-02-07_18-34-03.png)


 - ![image](img/-2024-02-07_18-34-40.png)
 Пушим изменения ветки master
 - ![image](img/-2024-02-07_18-35-06.png)
 - ![image](img/-2024-02-07_18-35-27.png)
 Смотрим, что ветки слились
 - ![image](img/-2024-02-07_18-36-06.png)