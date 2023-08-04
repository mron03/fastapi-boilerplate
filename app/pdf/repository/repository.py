from datetime import datetime
from typing import BinaryIO, List, Optional, Any

from bson.objectid import ObjectId
from fastapi import HTTPException
import psycopg2
from pymongo.database import Database

from ..utils.security import hash_password
from pymongo.results import DeleteResult, UpdateResult


import logging

import json, os, tempfile
from dotenv import load_dotenv

from langchain import LLMChain
from langchain.document_loaders import PyPDFLoader
from langchain.chains.summarize import load_summarize_chain
from langchain.chat_models import ChatOpenAI
from langchain.callbacks import get_openai_callback
from langchain.text_splitter import CharacterTextSplitter
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)


import logging
import sys

logger = logging.getLogger('my_app')
logger.setLevel(logging.DEBUG)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logger.addHandler(stdout_handler)



system_template = '''
    You are a teacher, and your task is to create a unique teaching scenario for {student_category} based on the specific content provided below. Your student's knowledge is at {student_level} level, so make sure to adapt the materials to them.

    Remember, you must consider the specific details in the provided content to craft a teaching scenario that hasn't been covered in previous responses. Adapt the complexity according to the student level, and follow the command ```{custom_filter}```.

    
    ANALYZE the following text:\n
        ```{materials}```

    Return the answer in VALID JSON format and the content should be in {language} language, DO NOT WRITE ANY QUOTES, DOUBLE QUOTES, SLASH and BACKSLASH characters:
        {{
            "Write the topic name" : {{
                "Instruction 1" : "Write What to do",
                "Speech 1": "Write what to tell for instruction 1",
                "Instruction 2" : "Write What to do",
                "Speech 2": "Write what to tell for instruction 2",
                "Instruction 3" : "Write What to do",
                "Speech 3": "Write what to tell for instruction 3",
                "Instruction N": "...",
                "Speech N": "..."
            }}
        }}

    Example of idiomatic JSON response: {{"Integrals":{{"Instruction 1":"Introduce topic of integrals","Speech 1":"Today, we are going to learn integrals","Instruction 2":"Show examples and problems","Speech 2":"Here is the problem we are going to solve","Instruction 3":"Conclude the topic","Speech 3":"In conclusion, integrals are very useful"}}}}
'''
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

def establish_database_connection():
    db_host = os.getenv('DB_HOST')
    db_database = os.getenv('DB_DATABASE')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')

    try:
        connection = psycopg2.connect(
            host=db_host,
            database=db_database,
            user=db_user,
            password=db_password
        )
        logger.info("Successfully connected to the PostgreSQL database!")
        return connection
    except (Exception, psycopg2.Error) as error:
        logger.info("Error while connecting to PostgreSQL:", error)
        return None


class PdfRepository:
    def __init__(self, database: Database):
        self.database = database

    def store_responses_in_db(self, responses, file, user_nickname):
        connection = establish_database_connection()
        cursor = connection.cursor()

        for response in responses:
            response_for_history = ''
            if file:
                pdf_for_history = file.read()
        
            for topic, value in response.items():

                response_for_history += topic
                response_for_history += '\n'

                for inst_speech, content in value.items():

                    response_for_history += f'{inst_speech} : {content}'
                    response_for_history += '\n'

                response_for_history += '\n'

            logger.debug(f'RESPONSE FOR HISTORY ================================ \n{response_for_history}')

            if file:
                try:
                    command = 'INSERT INTO history_pdf (user_id, pdf_file, response) VALUES(%s, %s, %s)' 
                    cursor.execute(command, (user_nickname, psycopg2.Binary(pdf_for_history), response_for_history,))
                    connection.commit()
                except (Exception, psycopg2.Error) as error:
                    logger.info("Error executing SQL statements when setting pdf_file in history_pdf:", error)
                    connection.rollback()
            
        cursor.close()
        connection.close()

                


    def create_scenario(self, file: BinaryIO, user_nickname : str, student_category: str, student_level: str, custom_filter: str, language : str):

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(file.read())
        loader = PyPDFLoader(tmp_file.name)
        text_splitter = CharacterTextSplitter(separator='\n', chunk_size=40000, chunk_overlap=0)

        docs = loader.load_and_split(text_splitter=text_splitter)
        os.remove(tmp_file.name)

        
        llm = ChatOpenAI(temperature=0.5)
        summarization_chain = load_summarize_chain(llm, chain_type="map_reduce")

        responses = []
        prev_response_summaries = ''

        i = 1
        logger.debug(f'==========================NUM OF DOCS ============= {len(docs)}')
        for doc in docs:

            logger.debug(f'=================================HERE IS THe  PREV ANSWER {i}===============================: \n {prev_response_summaries}')

            response = self.get_response_from_gpt(doc.page_content, prev_response_summaries, student_category, student_level, custom_filter, language)
            responses.append(response)   

            i += 1

            inp = json.loads(response)

            inpp = ''
            for topic, value in inp.items():
                inpp = inpp + topic + '\n'

                for inst, speech in value.items():
                    inpp += f'{inst} : {speech}'

            logger.debug(f'===========================RESPONSE FORMATTED======================= \n {inpp}')
            prev_response_summaries = inpp  

            # inp = text_splitter.create_documents(responses)
            # prev_response_summaries = summarization_chain.run(inp)

        
        final_responses = []
        for response in responses:
            try:
                final_responses.append(json.loads(response)) 
            except Exception:
                continue

        
        logger.debug(f'======================FINAL RESPONSES=====================\n\n{final_responses}')

        self.store_responses_in_db(final_responses, file, user_nickname)
        
        return final_responses

    def get_response_from_gpt(self, docs, prev_response_summaries, student_category, student_level, custom_filter, language):
        llm=ChatOpenAI(model_name='gpt-3.5-turbo-16k', temperature=0.5, verbose=True)

        system_prompt = SystemMessagePromptTemplate.from_template(system_template)

        human_template = '''HELP ME WRITE TEACHING SCENARIO'''
        human_prompt = HumanMessagePromptTemplate.from_template(human_template)

        chain_prompt = ChatPromptTemplate.from_messages([human_prompt, system_prompt])

        chain = LLMChain(llm=llm, prompt=chain_prompt, verbose=True)

        with get_openai_callback() as cb:
            response = chain.run(materials=docs, prev_responses=prev_response_summaries, student_category=student_category, student_level=student_level, custom_filter=custom_filter, language=language)
            print(cb)

        return response