from datetime import datetime
from typing import BinaryIO, List, Optional, Any

from bson.objectid import ObjectId
from fastapi import HTTPException
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
    Based on PREVIOUS RESPONSES SUMMARY write the LOGICAL CONTINUATION OF THE SCENARIO, DO NOT REPEAT THE CONTENT:
        ```
            {prev_responses_summaries}
        ```

    You need to use the following data to create plan:
            ```{materials}```

    You are a teacher, You need to create a teaching scenario for {student_category}

    You are aware that your student knowledge is at {student_level} level, so you adapt the materials to them
    
    For example, if they are beginner, explain them in easy and understanding way. If they are proffient or higher, you can explain in more complex way with good examples if needed

    You need to follow this command ```{custom_filter}```


    Return the answer in VALID JSON format in russian language:
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

class PdfRepository:
    def __init__(self, database: Database):
        self.database = database

    def create_scenario(self, file: BinaryIO, filename: str, student_category: str, student_level: str, custom_filter: str):

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(file.read())
        loader = PyPDFLoader(tmp_file.name)
        text_splitter = CharacterTextSplitter(separator='\n', chunk_size=20000, chunk_overlap=0)

        docs = loader.load_and_split(text_splitter=text_splitter)
        os.remove(tmp_file.name)

        for i in range(len(docs)):
            logger.debug(f'Doc number {i}: \n {docs[i].page_content}')
        
        llm = ChatOpenAI(temperature=0.5)
        summarization_chain = load_summarize_chain(llm, chain_type="map_reduce")

        responses = []
        prev_response_summaries = ''

        i = 1
        
        for doc in docs:

            logger.debug(f'HERE IS THE SUMMARY OF PREV ANSWER {i}: \n {prev_response_summaries}')

            response = self.get_response_from_gpt(doc.page_content, prev_response_summaries, student_category, student_level, custom_filter)
            responses.append(response)   

            logger.debug(f'HERE IS THE RESPONSE NUMBER {i}: \n {response}') 
            i += 1

            inp = text_splitter.create_documents(responses)
            prev_response_summaries = summarization_chain.run(inp)

        
        final_responses = []
        for response in responses:
            final_responses.append(json.loads(response))
            logger.debug(f'TYPE OF RESPONSES : \n {type(final_responses[-1])}')
        
        return final_responses

    def get_response_from_gpt(self, docs, prev_response_summaries, student_category, student_level, custom_filter):
        llm=ChatOpenAI(model_name='gpt-3.5-turbo-16k', temperature=0, verbose=True)

        system_prompt = SystemMessagePromptTemplate.from_template(system_template)

        human_template = '''Complete the following request: {query}'''
        human_prompt = HumanMessagePromptTemplate.from_template(human_template)

        chain_prompt = ChatPromptTemplate.from_messages([human_prompt, system_prompt])

        chain = LLMChain(llm=llm, prompt=chain_prompt, verbose=True)

        with get_openai_callback() as cb:
            response = chain.run(query='Create Teaching Scenario', materials=docs, prev_responses_summaries=prev_response_summaries, student_category=student_category, student_level=student_level, custom_filter=custom_filter)
            print(cb)

        return response