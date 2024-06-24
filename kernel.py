import json
import os
import subprocess

from openai import OpenAI
from selenium import webdriver
from bs4 import BeautifulSoup
import dotenv
import dataclasses

dotenv.load_dotenv()

api_token = os.getenv('API_TOKEN')
client = OpenAI(api_key=api_token)
chrome = webdriver.Chrome()


@dataclasses.dataclass
class SearchResult:
    is_found: bool
    link: str


def get_forms_html(url):
    driver = webdriver.Chrome()
    driver.get(url)

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    forms = soup.find_all('form')
    forms_html = [str(form) for form in forms]

    driver.quit()

    return forms_html


def generate_answer(messages: list, funcs, func_name):
    result = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        functions=funcs,
        function_call=func_name
    )
    print(result)
    return result.choices[0].message.function_call.arguments


def execute(site: str):
    chrome.get(site)
    soup = BeautifulSoup(chrome.page_source, 'html.parser')

    links_dict = {a.get_text(strip=True): a['href'] for a in soup.find_all('a', href=True)}
    question = f'Запрос: {site}, ссылки: {links_dict}'
    print(question)
    chrome.quit()

    answer = generate_answer(
        [
            {'role': 'system',
             'content': "I will send you the content from the site and you need to return a JSON structure: {'is_found': bool, 'link': str} where 'link' is the link to the page where the contact form might be found"},
            {'role': 'user', 'content': question}
        ],
        [
            {
                "name": "find_contact_form",
                "description": "Find the contact form link on the website",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "is_found": {
                            "type": "boolean",
                            "description": "Whether the contact form is found or not"
                        },
                        "link": {
                            "type": "string",
                            "description": "The link to the contact form"
                        }
                    },
                    "required": ["is_found", "link"]
                }
            }
        ],
        {"name": "find_contact_form"}
    )
    result = SearchResult(**json.loads(answer))
    if result.is_found:
        forms = get_forms_html(result.link)


site_ = 'https://pcsgaragedoors.co.uk/'
# execute(site_)
site__ = 'https://pcsgaragedoors.co.uk/contact-us'
answer = generate_answer(
    [
        {"role": "system", "content": f"You are an expert in web automation using Selenium. Use only this: from selenium import webdriver from selenium.webdriver.common.by import By import time and driver = webdriver.Chrome(). auto paste url inside driver.get() ({site__}. final program should be 100% works. at the end of the program wait 5 seconds and print driver.page_source"},
        {"role": "user",
         "content": f"Here are some HTML forms: {get_forms_html(site__)}. Please provide Python code using Selenium that fills and submits these forms."}
    ],
    [
        {
            "name": "generate_form_filling_code",
            "description": "Generate Python code to fill and submit HTML forms using Selenium.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The Python code to fill and submit the forms."
                    },
                    "form_submit_link": {
                        "type": "string",
                        "description": "Ссылка по которой отправляется форма"
                    }
                },
                "required": ["code", 'form_submit_link']
            }
        }
    ],
    {"name": "generate_form_filling_code"}
)
filename = f'generations/{site__.split("//")[1].split(".")[0]}.py'
with open(filename, "w") as f:
    f.write(json.loads(answer)['code'])
print(json.loads(answer)['form_submit_link'])
# Теперь можно запустить сгенерированный код
result = subprocess.run(["python", filename], capture_output=True, text=True)
print(result.stdout)
