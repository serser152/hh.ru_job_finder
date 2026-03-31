[English version](README.md)

# Персональный ассистент

## Цели проекта
  - Анализ рынка труда (количество вакансий, основные компании, параметры вакансий)
  - Находить и отзываться на вакансии
  - Автоматически оценивать соответствие вакансий своему резюме (TBD)

## Поддерживаемые сайты
  - hh.ru
  - zarplata.ru
  - superjob.ru (TBD)

## Системные требования

OS Linux с установленными docker-compose и git.

## Установка

1) Склонировать репозиторий

```
git clone https://github.com/serser152/hh.ru_job_finder
cd hh.ru_job_finder
docker-compose build
docker-compose up -d
```

Интерфейс - [http://localhost:8501](http://localhost:8501)
Интерфейс grafana - [http://localhost:3000](http://localhost:3000)
Загрузить в графану файлы конфигов дашбордов из директории "grafana_dashboards".

2) Сконфигурировать парольный доступ на работные сайты.
3) Зайти в интерфейс на вкладку settings и заполнить таблицу поиска по сайтам





## Архитектура

Сервис состоит из нескольких docker контейнеров:
- postgresql
- grafana
- hh_grubber (selenium)
- scheduller (apscheduler)
- gui (streamlit + celery)
- redis (for celery)
- rabbitmq (for celery)

## Примеры

### Интерфейс

#### Вкладка настроек
![4](images/example4.png)
#### Вкладка таблицы данных
![5](images/example5.png)

Таблица в полноэкранном режиме
![6](images/example6.png)
#### Вкладка графиков
![7](images/example7.png)

### Grafana

#### Обзор рынка

![1](images/example1.png)
![2](images/example2.png)

#### Мониторинг работы загрузки вакансий
![3](images/example3.png)


