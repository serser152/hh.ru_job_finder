#!/usr/bin/env python3
from fastapi import FastAPI
from pydantic import BaseModel
from .grab_hh import get_vacancies, accept_vacancy
import json

class SearchRequest(BaseModel):
    phone: str
    password: str
    request: str

class AcceptRequest(BaseModel):
    phone: str
    password: str
    request: str
    vacancy_id: int

app = FastAPI(host='0.0.0.0')

@app.get('/health')
async def health():
    return 'ok'

@app.post('/find_vacancies')
async def find_vacancies(request: SearchRequest):
    print('find vacancies '+request.request)
    df = get_vacancies(request.phone, request.password, request.request)
    return df.to_json(orient='records')

@app.post('/accept_vacancy')
async def accept_vacancy_by_id(request: AcceptRequest):
    print('accept vacancies '+request.request+' '+str(request.vacancy_id))
    res = accept_vacancy(request.phone, request.password, request.request, request.vacancy_id)
    return str(res)


