# Вывод результатов трейдинга в сервисе "Тинькофф Инвестиции"

Программа выводит результаты за выбранный день, период, сводные данные:
* оборот (в долларовом и рублевом эквивалентах);
* размер удержанной комиссии за сделки (в долларовом и рублевом эквивалентах);
* финансовый результат (в долларовом и рублевом эквивалентах);
* средняя эффективность сделок (в %);
* количество сделок;
* итоговые данные за период, если в указанном периоде несколько торговых дней;
* ТОП бумаг по обороту;
* ТОП бумаг по полученному финансовому результату.

### Примеры вывода результатов
Результат за один день
![Результат за один день](https://user-images.githubusercontent.com/30386440/120017013-00b64900-bfee-11eb-9bbd-c2352d70a103.png)

Результаты за выбранный период с общими итогами
![Результаты за выбранный период](https://user-images.githubusercontent.com/30386440/120017058-10359200-bfee-11eb-9ce9-76c3a1f10513.png)

Сводные (консолидированные) результаты за выбранный период
![Сводные (консолидированные) результаты за выбранный период](https://user-images.githubusercontent.com/30386440/120017073-14fa4600-bfee-11eb-92d9-c67a31408968.png)

### Алгоритм расчета
Торговый день считается с 2:00 текущего дня до 2:00 следующего календарного дня (московское время)). 
В обороте и комиссиях учитываются все сделки покупки и продажи. 
Финансовый результат и эффективность сделок определяются только по закрытым сделкам внутри дня. 
Если выводятся сводные (консолидированные) результаты, то закрытые сделки считаются все (не только внутри дня). 

Финансовый результат равен сумме продажи минус сумма покупки минус комиссии за сделки продажи и покупки. 
Эффективность за день равна финансовому результату по всем закрытым сделкам, поделенному на среднее значение сумм покупки и продажи по закрытым сделкам. 

В ТОП бумаг по обороту выводятся до пяти бумаг с наибольшим оборотом за выбранный день или период. 

В ТОП бумаг по прибыли выводятся до пяти бумаг с наибольшим суммарным финансовым результатом за выбранный день или период.

### Tinkoff Invest
Реализовано на основе проекта [Tinkoff Invest](https://github.com/Tinkoff/invest-python) для работы с OpenAPI Тинькофф Инвестиции.


## Установка и запуск
### Установка
На вашем компьютере должен быть установлен Python 3.x.

Для запуска на локальном компьютере необходимо:
* склонировать проект на свой компьютер <code>git clone https://github.com/amidvn/tinkoff-statistika.git</code>
* перейти в каталог проекта <code>cd tinkoff-statistika</code>
* выполнить команду <code>pip install -r requirements.txt</code> для установки требуемых для работы библиотек
* указать в переменную среды <code>TINKOFFAPI_TOKEN</code> ваш токен OpenAPI Тинькофф (см. [ниже](https://github.com/amidvn/tinkoff-statistika#%D1%83%D0%BA%D0%B0%D0%B7%D0%B0%D0%BD%D0%B8%D0%B5-%D1%82%D0%BE%D0%BA%D0%B5%D0%BD%D0%B0-%D0%B0%D1%83%D1%82%D0%B5%D0%BD%D1%82%D0%B8%D1%84%D0%B8%D0%BA%D0%B0%D1%86%D0%B8%D0%B8)). 

### Запуск
Для запуска ввести команду (выведет результат за сегодняшний день):
```
python tstat.py
```
__Другие варианты запуска с параметрами:__

Вывод результата за вчерашний день:
```
python tstat.py yesterday
```
Вывод результата за любой произвольный день:
```
python tstat.py 03.05.2021
```
Вывод результата за любой произвольный период:
```
python tstat.py 01.04.2021 31.05.2021
```
Вывод результатов за текущую неделю (thisweek), текущий месяц (thismonth), текущий год (thisyear), прошлую неделю (lastweek), прошлый месяц (lastmonth), прошлый год (lastyear):
```
python tstat.py thisweek
python tstat.py thismonth
python tstat.py thisyear
python tstat.py lastweek
python tstat.py lastmonth
python tstat.py lastyear
```
Для вывода данных без разбивки по торговым дням и расчету сводных данных (соответственно, финансовый результат будет считаться не только у внутридневных сделок), 
указать последним параметром <code>cons</code>. Например, для вывода сводных данных за текущий год ввести:
```
python tstat.py thisyear cons
```


## Указание токена аутентификации
### Получение токена
1. Зайти в раздел инвестиций в [личном кабинете tinkoff](https://www.tinkoff.ru/invest/).
2. Перейти в настройки.
3. Функция "Подтверждение сделок кодом" должна быть отключена.
4. Выпустить токен OpenAPI для биржи: в разделе **Токены Tinkoff Invest API** нажать "Создать токен" (без разницы какой режим "Только для чтения" или "Полный доступ").
5. Скопировать токен и сохранить его. Токен отображается только один раз, просмотреть его позже не получится. Тем не менее вы можете выпускать неограниченное количество токенов.

### Сохранение токена в переменные среды вашего компьютера
Способ 1 (рекомендуемый):
1. Создать в папке проекта файл с наименованием <code>.env</code>
2. Вставить в файл строку:
```
TINKOFFAPI_TOKEN=ВАШ_ТОКЕН
```
где <code>ВАШ_ТОКЕН</code> заменить на полученый токен.


Способ 2 (для Windows):
1. Свойства компьютера -- Дополнительные параметры системы -- закладка "Дополнительно" -- "Переменные среды".
2. Создать новую переменную среды текущего пользователя с именем <code>TINKOFFAPI_TOKEN</code> и указать полученный токен.


Способ 3 (через командную строку для Windows):

Выполнить команду:
```
setx TINKOFFAPI_TOKEN ваш_токен
```
