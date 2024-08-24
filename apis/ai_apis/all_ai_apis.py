from fastapi import APIRouter, UploadFile
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.schema.messages import HumanMessage
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from bs4 import BeautifulSoup


import os
from dotenv import load_dotenv


#  api router for authentications
ai_router = APIRouter()

# load the env variable
load_dotenv()

OPEN_API_KEY = os.getenv("OPENAI_KEY")


# extract the cases
def extract_cases(section):
    cases = ""
    next_node = section.find_next_sibling()
    
    while next_node and next_node.name != 'h3':  # Stop when the next section starts
        if next_node.name == 'h4':
            cases += str(next_node)
        elif next_node.name == 'p':
            cases += str(next_node)
        next_node = next_node.find_next_sibling()
    
    return cases


@ai_router.get("/query/{question}")
async def query_api(question:str):

	loader = PyPDFLoader("ai_req_docs/model_req/PharmacologyRevisionE6_5.pdf")
	docs = loader.load()

	text_splitter = CharacterTextSplitter(
		chunk_size=1000,
		chunk_overlap=150
	)

	document = text_splitter.split_documents(docs)

	embedding = OpenAIEmbeddings(api_key=OPEN_API_KEY)

	persist_directory = 'docs/chroma/'

	# Create the vector store
	vectordb = Chroma.from_documents(
		documents=document,
		embedding=embedding,
		persist_directory=persist_directory
	)

	llm = ChatOpenAI(model ="gpt-4o-mini", temperature=0.7, api_key=OPEN_API_KEY)

	template = """Use the following pieces of context to answer the question at the end. You have all the knowledge in the medical field and also about the knowledge that i have given to you. If you don't know the answer, just say that you don't know, don't try to make up an answer. Always answer in points and headings in standard *HTML5* tags and do not use any special characters. {context}
	Question: {question}
	Helpful Answer:"""
	QA_CHAIN_PROMPT = PromptTemplate.from_template(template) # Run chain
	qa_chain = RetrievalQA.from_chain_type(
		llm,
		retriever=vectordb.as_retriever(),
		return_source_documents=True,
		chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
	)
	
	result = qa_chain({"query": question})

	return {"response": result["result"]}



# differential diagonise api
@ai_router.get("/differential-diagonise")
async def differential_diagonise_api(question:str):
	# change file to ECG Cases
	loader = PyPDFLoader("ai_req_docs/model_req/PharmacologyRevisionE6_5.pdf")
	documents = loader.load()

	# split the documents into chunks
	text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=0)
	texts = text_splitter.split_documents(documents)

	embeddings = OpenAIEmbeddings(api_key=OPEN_API_KEY)
	db = Chroma.from_documents(texts, embeddings)

	template = """You are a medical chatbot with expertise only in the medical field. Do not use any special characters, answer in standard *HTML5* body tags. and Provide differential diagnoses in the following format:

	Differential Diagnosis:
	Normal Causes
	Case 1:
	Primary Disease:
	Rationale:
	Additional Diagnostics:
	Case 2:
	Primary Disease:
	Rationale:
	Additional Diagnostics:

	Must Not Miss
	Case 1:
	Primary Disease:
	Rationale:
	Additional Diagnostics:

	Rare Diagnoses
	Case 1:
	Primary Disease:
	Rationale:
	Additional Diagnostics:

	Keep explanations clear, professional, and concise and use at least 2-3 cases in each.

	query : {question}
	{context}
    """
	
	llm = ChatOpenAI(model ="gpt-4o-mini", temperature=0.7, max_tokens=450, api_key=OPEN_API_KEY)

	retriever = db.as_retriever(search_kwargs={"k":2})
	QA_CHAIN_PROMPT = PromptTemplate.from_template(template)# Run chain
	qa_chain = RetrievalQA.from_chain_type(
		llm,
		retriever=retriever,
		# return_source_documents=True,
		chain_type_kwargs={"prompt": QA_CHAIN_PROMPT},
	)

	# we will create a question here once user send us the form
	result = qa_chain({"query": question})

	# Parse the HTML content
	soup = BeautifulSoup(result["result"], 'html.parser')

	# Dictionary to store the sections and their cases
	diagnosis_dict = {}

	# Extracting the sections
	sections = soup.find_all('h3')
	for section in sections:
		section_title = section.get_text()
		cases = extract_cases(section)
		diagnosis_dict[section_title] = cases
    
	# Check the result of the query
	return {"response": diagnosis_dict}



# below code is necessary to initiate the case simulation model
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, max_tokens=256, api_key=OPEN_API_KEY)

template = """
Act as a medical expert and ask the user a question about a medical scenario.
After the user responds, evaluate their answer and give them a score out of 10 on different parameters.
Your question should randomly cover Infections, Flews, Pathology, Neurology, ECG, Cardiology, Accidents, Gynacology and more.
Also remember to adjust the difficulty of questions based on user's previous score and be very strict while scoring.
If the user score is less then 3 ask him easy question if between 4-7 ask medium and for rest ask harder questions.
Explain why you gave that score.
{history}
Question: {input}
  "evaluation": 
    "understanding_of_condition": 
      "score": ,
      "comments": ""

    leadership_quality": 
      "score": ,
      "comments": ""
    
    "immediate_treatment": 
      "score": ,
      "comments": ""
    
    "overall_clinical_approach": 
      "score": ,
      "comments": ""
"""

prompt = PromptTemplate(
    input_variables=["history", "input"],
    template=template
)

memory = ConversationBufferMemory(size=2)

conversation = ConversationChain(prompt=prompt,
                                 llm=llm,
                                 memory=memory)


@ai_router.get("/case-simulation")
async def case_simulation_api(user_input: str):
    output = conversation.predict(input=user_input)
    return {"response": output}