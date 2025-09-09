from typing import TypedDict, List, Dict, Any, Optional
from langchain_xai import ChatXAI
import json
import os
from datetime import datetime
import hashlib
from dotenv import load_dotenv
from synthetic_lead_generator import GrokDataGenerator
from lead_management import LeadManager
from chat_interface import GrokLeadCLI
from dataclasses import asdict

# Load environment variables from .env file
load_dotenv()
GROK_API_KEY=os.getenv('GROK_API_KEY')

FILENAME = "leads.json"
NUM_LEADS = 1

# Initialize the language model
llm = ChatXAI(model="grok-4", api_key=GROK_API_KEY)

def main():
    # instantiate synthetic data generator
    gdg = GrokDataGenerator(GROK_API_KEY)
    print("***Generating Leads***")
    # generate leads
    leads = gdg.generate_leads_with_grok(count=NUM_LEADS)
    print(leads)
    # dump to file    
    with open(FILENAME, 'w') as json_file:
        json.dump(leads, json_file, indent=4)
    print("***Done!***\n\n")

    # initiate leads manager
    lm = LeadManager()    
    print("***Add all leads to LeadManager to score them***")
    # load leads from file
    try:
        with open(FILENAME, 'r') as file:
            list_of_leads = json.load(file)        
    except FileNotFoundError:
        print("Error: 'data.json' not found.")
    # add to leads manager
    lead_ids = lm.create_lead_objects_from_data(list_of_leads)
    print(lead_ids)
    print("***Done***\n\n")

    # create list of scored leads
    list_of_leads = []
    for id in lead_ids:
        list_of_leads.append(lm.get_lead(id))
    # chat session to analyze the leads
    print("***Chat session***")    
    cli = GrokLeadCLI(GROK_API_KEY, list_of_leads)
    cli.run_interactive_session()

if __name__ == "__main__":
    main()