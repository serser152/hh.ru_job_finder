# Job assistant

## Goals
  - help with market analysis (vacancy count, main companies, job parameters)
  - help to find and response to vacancies



## Supported sites
  - hh.ru


## Architecture

Service implemented via docker containers. There are following containers:
- postgresql
- grafana
- hh_grubber
- scheduller
- gui (interface to work)

## Examples

### Grafana charts

#### Обзор рынка

![1](images/example1.png)
![2](images/example2.png)

#### Мониторинг работы загрузки вакансий
![3](images/example3.png)