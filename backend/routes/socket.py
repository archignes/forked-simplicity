from fastapi import (
    APIRouter,
    WebSocket,
)

import json
from dotenv import load_dotenv
import os
import json
import pongo
from exa_py import Exa
from openai import OpenAI
import logging

socket_router = APIRouter()
load_dotenv()
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")



exa_client = Exa( os.environ.get("EXA_API_KEY"))

openai_client = OpenAI(api_key=os.environ.get("TOGETHER_API_KEY"), base_url='https://api.together.xyz/v1')
pongo_client = pongo.PongoClient(os.environ.get("PONGO_API_KEY"))

logging.basicConfig(level=logging.INFO)

@socket_router.websocket("/sockets/test")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    while True:
        query = await websocket.receive_text()

        llm_prompt = ''

        search_results = exa_client.search_and_contents(
            query, 
            use_autoprompt=True,
            num_results=10,
            text={  "include_html_tags": False,'max_characters': 2000 },
            highlights={ 'highlights_per_url': 10, 'num_sentences': 10})

        data_for_pongo = []
        grouped_highlights = {}

        for cur_result in search_results.results:
            if not cur_result:
                break
            
            cur_metadata = {'title': cur_result.title if cur_result.title else 'no title'}
            
            # Group the highlights by the URL
            if cur_result.url in grouped_highlights:
                grouped_highlights[cur_result.url]['text'] += '\n\n' + '\n\n'.join(cur_result.highlights)
                grouped_highlights[cur_result.url]['metadata'] = cur_metadata
                grouped_highlights[cur_result.url]['id'] = cur_result.id
            else:
                grouped_highlights[cur_result.url] = {
                    'text': '\n\n'.join(cur_result.highlights),
                    'metadata': cur_metadata,
                    'id': cur_result.id,
                    'url': cur_result.url
                }

        # Add the grouped highlights to the data_for_pongo list
        data_for_pongo = list(grouped_highlights.values())
        # logging.info("Grouped Highlights: %s", json.dumps(grouped_highlights, indent=2))

        # logging.info("Data for Pongo: %s", json.dumps(data_for_pongo, indent=2))

        filtered_results = pongo_client.filter(
            query=query, 
            docs=data_for_pongo,
            num_results=8, 
            public_metadata_field="metadata", 
            key_field="id", 
            text_field='text'
        )
        
        if filtered_results.status_code != 200:
            # logging.error("API request failed with status %d: %s", filtered_results.status_code, filtered_results.text)
            await websocket.send_text("Error processing your request.")
            continue  # Skip further processing or handle the error appropriately
        else:
            filtered_body = filtered_results.json()

        try:
            filtered_body = filtered_results.json()
        except json.JSONDecodeError:
            logging.error("Failed to decode JSON from response: %s", filtered_results.text)
            await websocket.send_text("Error processing your request.")
            continue  # Skip further processing or handle the error appropriately



        await websocket.send_text("JSON_STRING:" + json.dumps(filtered_body))

        # logging.info("Filtered Results: %s", json.dumps(filtered_body, indent=2))

        sources_string = ''
        used_urls = set()  # Keep track of used URLs
        i = 0
        while (i < 8):
            cur_source = filtered_body[i] 

            if(len(sources_string) > 10000):
                break
            
            # Check if the URL has already been used
            if cur_source['url'] not in used_urls:
                sources_string += f'''\n# Source #{i+1} (from "{cur_source['metadata']['title']}"):\n\n${cur_source['text']}\n\n'''
                used_urls.add(cur_source['url'])  # Add the URL to the used_urls set
                i += 1

        logging.info("Sources String: %s", sources_string)

        llm_prompt = f'''Please concisely answer the following question using ONLY the snippets from websites provided at the bottom of this prompt.  If the question cannot be answered from the sources, then just say so. 
        Make sure you cite each source used inline with ONLY the source number wrapped in brackets, so you would cite Source #2 as just "[2]".
        DO NOT include a list of references at the end, only use inline citations as previously described.

        Note: If the query is simply a URL, then the results will be webpages similar to the URL page and the question should
        be interpreted as a review of these similar pages. Do not discuss the URL provided at all.

        Provide your answer in valid markdown format.
        Discuss every relevant source.

        Question: {query}

        Sources: {sources_string}'''

        for chunk in openai_client.chat.completions.create(
            model="META-LLAMA/LLAMA-3-70B-CHAT-HF",
            messages=[{"role": "user", "content": llm_prompt}],
            stream=True,
            temperature=0.2,
        ):
            if isinstance(chunk.choices[0].delta.content, str):
                await websocket.send_text(chunk.choices[0].delta.content)
