# Job assistant

## Goals
  - Market analysis (vacancy count, main companies, job parameters)
  - Find and respond to vacancies
  - Automatic vacancies matching, skills analysis (TBD)

## Supported sites
  - hh.ru
  - zarplata.ru

## System requirements

OS Linux with docker-compose and git installed.

## Installation

```
git clone https://github.com/serser152/hh.ru_job_finder
cd hh.ru_job_finder
docker-compose build
docker-compose up -d
```

UI - [http://localhost:8501](http://localhost:8501)

grafana interface - [http://localhost:3000](http://localhost:3000)

## Install

## Architecture

Service implemented via docker containers. There are following containers:
- postgresql
- grafana
- hh_grubber (selenium)
- scheduller (apscheduler)
- gui (streamlit + celery)
- redis (for celery)
- rabbitmq (for celery)

## Examples

### UI

#### Settings tab
![4](images/example4.png)
#### data tab
![5](images/example5.png)

table in fullscreen mode
![6](images/example6.png)
#### count bar chart 
![7](images/example7.png)

### Grafana charts

#### Обзор рынка

![1](images/example1.png)
![2](images/example2.png)

#### Мониторинг работы загрузки вакансий
![3](images/example3.png)


