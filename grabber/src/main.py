#!/usr/bin/env python3
"""
API(FastAPI) for hh_grabber functionality
"""

import datetime
from pydantic import BaseModel
import pandas as pd
from fastapi import FastAPI
from .grabber import GrabberFactory

class SearchRequest(BaseModel):
    """Class for search request"""
    site: str
    phone: str
    password: str
    request: str

class AcceptRequest(BaseModel):
    """Class for respond to vacancy"""
    site: str
    phone: str
    password: str
    vacancy_id: list
    cover_letter:str

class GetDescriptionRequest(BaseModel):
    """Class for grab description"""
    site: str
    phone: str
    password: str
    vacancy_ids: list


app = FastAPI(host='0.0.0.0')


@app.get('/health')
async def health():
    """Health function - returns 'ok'"""
    return 'ok'


@app.post('/find_vacancies')
async def find_vacancies(request: SearchRequest):
    """Get vacancies list and returns json"""
    print('find vacancies ' + request.request)
    grabber = GrabberFactory().create_grabber(request.site, request.phone, request.password)
    vacancies = pd.DataFrame(grabber.get_vacancies(request.request))
    vacancies['site'] = request.site
    vacancies['dt'] = datetime.datetime.now()
    return vacancies.to_json(orient='records')


@app.post('/get_vacancy_descriptions')
async def get_desc(request: GetDescriptionRequest):
    """Get vacancies descriptions by vac_id list"""
    print('Get descriptions ' + str(request.vacancy_ids))
    grabber = GrabberFactory().create_grabber(request.site, request.phone, request.password)
    descriptions = pd.DataFrame(grabber.get_vacancies_descriptions(request.vacancy_ids))
    descriptions['site'] = request.site
    return descriptions.to_json(orient='records')


@app.post('/accept_vacancy')
async def accept_vacancy_by_id(request: GetDescriptionRequest):
    """Respond to vacancy by id"""
    print('accept vacancies ' + str(request.vacancy_ids))
    grabber = GrabberFactory().create_grabber(request.site, request.phone, request.password)
    grabber.respond_to_vacancy(request.vacancy_id, request.cover_letter)
