from datetime import datetime
from typing import BinaryIO, List, Optional, Any

from bson.objectid import ObjectId
from fastapi import HTTPException
import psycopg2
from pymongo.database import Database
import requests

from ..utils.security import hash_password
from pymongo.results import DeleteResult, UpdateResult


import logging

import json, os, tempfile
from dotenv import load_dotenv

from youtube_transcript_api import YouTubeTranscriptApi

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
    You are a teacher, and your task is to create VERY DETAILED teaching scenario.
        STUDENT CATEGORY :  {student_category},
        STUDENT_LEVEL : {student_level},

    Remember, you must consider the specific details in the provided content to craft a teaching scenario. Adapt the complexity according to the STUDENT CATEGORY and STUDENT LEVEL, and follow the command ```{custom_filter}```.

    ANALYZE the following text TO CREATE VERY DETAILED SCENARIO:\n
        ```{materials}```

    Return the answer in VALID JSON format and content should be in {language} language, DO NOT WRITE ANY QUOTES, DOUBLE QUOTES, SLASH and BACKSLASH characters:
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
youtube_api_key = os.getenv('YOUTUBE_API_KEY')

def establish_database_connection():
    logger = logging.getLogger('my_app')

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

class YoutubeRepository:
    def __init__(self, database: Database):
        self.database = database

    def store_responses_in_db(self, responses, user_nickname, youtube_urls, youtube_prompt):
        connection = establish_database_connection()
        cursor = connection.cursor()


        response_for_history = ''


        for response in responses:
            
            for topic, value in json.loads(response).items():
                response_for_history += topic
                response_for_history += '\n'
                    
                for inst_speech, content in value.items():
                    
                    response_for_history += f'{inst_speech} : {content}'
                    response_for_history += '\n'

                response_for_history += '\n'
            
            logger.info(response_for_history)
            try:
                command = 'INSERT INTO history_youtube (user_id, topic, response, youtube_urls) VALUES(%s, %s, %s, %s)' 
                cursor.execute(command, (user_nickname, youtube_prompt, response_for_history, youtube_urls))
                connection.commit()

            except (Exception, psycopg2.Error) as error:
                print("Error executing SQL statements when setting pdf_file in history_youtube:", error)
                connection.rollback()

            
        cursor.close()
        connection.close()

    def create_scenario_with_youtube(self, youtube_urls: List[str], user_nickname : str, youtube_prompt: str, student_category: str, student_level: str, custom_filter: str, language: str):
        youtube_ids = []
    
        if len(youtube_prompt) != 0:
            yt_videos = self.get_youtube_videos(youtube_prompt)
            for video in yt_videos:
                youtube_ids.append(video['id']['videoId'])
        

        videos = youtube_urls.copy()
        videos.extend([f'https://youtu.be/{id}' for id in youtube_ids])
        logger.debug(f'\nTHE YOUTUBE LINKS USED ========================================== {videos}')


        for url in youtube_urls:
            youtube_ids.append(url.split('/')[3])
        
        docs, no_transcript_urls = self.split_into_docs(youtube_ids)
   
        responses = self.get_responses_from_gpt(docs, student_category, student_level, custom_filter, language)

        self.store_responses_in_db(responses, user_nickname, youtube_urls, youtube_prompt)

        return responses, no_transcript_urls
        

    def get_youtube_videos(self, prompt):
        url = f"https://www.googleapis.com/youtube/v3/search?key={youtube_api_key}&q={prompt}&type=video&part=snippet&maxResults=1&videoDuration=medium"
        response = requests.get(url)
        data = json.loads(response.content)
        logger.debug(f'\nYOUTUBE API RESPONSE: ================================== {data}')
        return data["items"]
    

    def get_responses_from_gpt(self, docs, student_category, student_level, custom_filter, language):
        llm=ChatOpenAI(model_name='gpt-3.5-turbo-16k', temperature=0.3, verbose=True)

        system_prompt = SystemMessagePromptTemplate.from_template(system_template)

        human_prompt_template = '''HELP ME WRITE TEACHING SCENARIO'''
        human_prompt = HumanMessagePromptTemplate.from_template(human_prompt_template)

        chain_prompt = ChatPromptTemplate.from_messages([human_prompt, system_prompt])
        chain = LLMChain(llm=llm, prompt=chain_prompt)

        summarization_chain = load_summarize_chain(llm, chain_type="map_reduce")
        text_splitter = CharacterTextSplitter(separator="\n", chunk_size=2000, chunk_overlap=300)

        
        prev_responses_summary = ''
        responses = []

        # for i in range(len(docs)):
        #     logger.debug(f'NUMBER {i + 1} DOCUMENT HAS {llm.get_num_tokens(docs[i].page_content)}')
        #     logger.debug(f'\nTHE DOC NUMBER {i + 1} CONTENT:\n {docs[i].page_content}')
        
        i = 1
        for doc in docs:
            with get_openai_callback() as cb:
                logger.debug(f'=============================NUMBER {i} DOCUMENT HAS {llm.get_num_tokens(doc.page_content)}')
                logger.debug(f'=============================\nTHE DOC NUMBER {i} CONTENT:=====================\n {doc.page_content[:100]}')

                response = chain.run(prev_responses_summary=prev_responses_summary, student_category = student_category, student_level = student_level, custom_filter=custom_filter, materials=doc.page_content, language=language)
                responses.append(response)

                logger.debug(f'==============================RESPONSE NUMBER {i}:=================== \n {response}')
                logger.debug(f'==============================debug ABOUT OPENAI FOR MAIN CHAIN: {cb}')
            i += 1
            # with get_openai_callback() as cb:
            #     inp = text_splitter.create_documents(responses)
            #     prev_responses_summary = summarization_chain.run(inp)

            #     logger.debug(f'=====================================================THE SUMMARY OF PREVIOUS RESPONSES: \n {prev_responses_summary}')
            #     logger.debug(f'===================================================debug ABOUT OPENAI FOR SUMMARIZATION CHAIN: {cb}')

        return responses



    def split_into_docs(self, youtube_ids):
        llm = ChatOpenAI(model='gpt-3.5-turbo', temperature=0, verbose=True)
        text_splitter = CharacterTextSplitter(separator="\n", chunk_size=10000, chunk_overlap=0, length_function = len)

        no_transcript_urls = []
        docs = []

        for id in youtube_ids:
            filtered_transcript = ''
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(id)
            except Exception as e:
                no_transcript_urls.append(f'https://youtu.be/{id}')
                continue


            transcript = transcript_list.find_transcript(['en', 'ru'])
            translated_transcript = transcript.translate('en').fetch()

            if len(translated_transcript) != 0:
                final_transcript = translated_transcript
            else:
                final_transcript = transcript.fetch()


            for text in final_transcript:
                filtered_transcript = filtered_transcript + text['text'] + ' '

            logger.debug(f'=====================VIDEO IDDDDD==================\n\n{id}')
          
            doc = text_splitter.create_documents([filtered_transcript])

            for d in docs:
                logger.debug(f'\n\n============THE DOC from {id} ============== \n\n{d.page_content[:1000]}')

            docs.extend(doc)

        if no_transcript_urls:
            untranscriptble_urls_message = 'Извините данные ссылки не имеют транскрита:\n'
            for url in no_transcript_urls:
                untranscriptble_urls_message += f'\n{url}\n'

        return docs, no_transcript_urls