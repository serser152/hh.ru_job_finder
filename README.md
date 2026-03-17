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