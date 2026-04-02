#!/usr/bin/env python3
'''
API(FastAPI) for hh_grabber functionality
'''

from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from .llm import parse_desc


class ParseDescriptionRequest(BaseModel):
    'Class for search request'
    desc: str

app = FastAPI(host='0.0.0.0')


@app.get('/health')
async def health():
    'Health function - returns "ok"'
    return 'ok'


@app.post('/parse_descriptions')
async def parse_description(request: ParseDescriptionRequest):
    'Get vacancies list and returns json'
    print('find vacancies ' + request.desc)
    res = parse_desc(request.desc)
    print(f'res = {res}')
    df = pd.DataFrame(res.split('\n'), columns=['skill'])
    return df.to_json(orient='records')
