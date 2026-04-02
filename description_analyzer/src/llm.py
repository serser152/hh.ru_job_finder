#!/usr/bin/env python
"""
LLM module
Analyze job description via LLM
"""

from os import environ
from time import sleep

from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_ollama import ChatOllama
load_dotenv(find_dotenv())

api_key = environ.get("OPENROUTER_API_KEY","")
llm_type = environ.get("LLM_TYPE","OpenRouter")
llm_name = environ.get("LLM_NAME","gpt-oss-20b:free")
ollama_url = environ.get("OLLAMA_URL","http://localhost:11434")
print(f'or key="{api_key}"')

if llm_type.lower() == 'openrouter':
    llm = ChatOpenAI(model=llm_name,
                 base_url="https://openrouter.ai/api/v1",
                 api_key=api_key)
elif llm_type.lower() == 'ollama':
    llm = ChatOllama(model=llm_name,
                 base_url=ollama_url)
else:
    print('Unknown llm type')
    raise Exception('Unknown llm type')

desc = """
Наша исследовательская AI-команда развивает Copilot сотрудника банка – виртуального ассистента, который участвует в диалоге с клиентом. Сейчас Copilot работает у каждого сотрудника отделения: подсказывает, ищет и исправляет ошибки, помогает вести диалог. Вашей задачей будет расширение функционала и улучшение качества работы ассистента, разработка новых продуктов и тестирование перспективных гипотез.
Обязанности
Вам предстоит:
· Проводить исследования, обучать модели и проверять гипотезы в прикладных бизнес-задачах.
· Разрабатывать, внедрять и поддерживать продукты на базе LLM и BERT-like моделей.
· Искать точки роста продукта, генерировать идеи, как сделать еще круче и лучше :)
· Ускорять и оптимизировать весь пайплайн исполнения на CPU/GPU инфраструктуре
Требования
Мы ждем, что вы:
· Умеете писать хороший код даже без ИИ-ассистентов (и с ними тоже)
· Имеете опыт работы с современными LLM в бизнес задачах (agents, prompt-engineering, tools, structured output, fine-tuning)
· На короткой ноге с BERT-Like моделями (умеете выбрать подходящую для задачи и при необходимости дообучить)
· Знаете классический ML и традиционный стек (torch, numpy, pandas, sklearn, библиотеки визуализации и т.д.)
Условия
Полное соблюдение ТК РФ, льготные условия по программам страхования, кредитования для сотрудников Банка;)
График 5/2, офис на м. Кутузовская;
Режим работы на выбор - офис или гибрид
Достойный уровень вознаграждения (оклад + внушительная годовая премия);
ДМС с первого дня работы и льготная мед. страховка для близких родственников;
Социальная поддержка сотрудников;
Возможность стать частью команды, реализующей программы цифровой трансформации банка - на основе передового опыта и инновационных идей;
Широкие возможности для профессионального развития: корпоративный университет и множество онлайн-программ обучения. Корпоративное обучение за счет компании;
Бесплатная подписка СберПрайм+, многочисленные скидки и бонусы от партнеров: СберМаркет, МегаМаркет, Самокат, Еаптека и др.;
Корпоративная пенсионная программа"""

system_prompt = """
Например:
Работать с современными LLM в бизнес‑контексте (agents, prompt‑engineering, tools, structured output, fine‑tuning)

Ответ:
LLM
prompt engineering
tools
agents
structured output
fine-tuning
"""



def parse_desc(desc: str) -> str:
    """Parse description to list of keywords"""
    prompt = [
        SystemMessage(content="Ты - hr-специалист. Ты должен анализировать вакансии и резюме. Выделять ключевые навыки. Писать на русском языке."+system_prompt),
        HumanMessage(content="Описание вакансии: " + desc + ". Выпиши ключевые навыки по одному в строке?")]

    try_cnt = 5
    while try_cnt > 0:
        try:
            res = llm.invoke(prompt)
            print(res.content)
            return res.content
        except Exception as e:
            print(e)
            try_cnt -= 1
            sleep(10)
    return ""
