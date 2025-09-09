import json
import requests
from typing import List, Dict, Any, Optional
from dataclasses import asdict
from datetime import datetime
import random
from langchain_xai import ChatXAI
from langchain_core.messages import HumanMessage, SystemMessage

class GrokDataGenerator:
    """Generate synthetic lead data using Grok API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.llm = ChatXAI(model="grok-4", api_key=self.api_key, temperature=0.7)
    
    def generate_lead_schema_prompt(self) -> str:
        """Generate a detailed prompt with the Lead class structure"""
        
        schema_prompt = """
                        You are a lead generation expert creating realistic B2B sales leads for a SaaS company demo.

                        Generate synthetic lead data following this EXACT structure:

                        LEAD STRUCTURE as a dictionary:

                            "first_name": "string - realistic first name",
                            "last_name": "string - realistic last name", 
                            "email": "string - professional email format: first.last@company.com",
                            "company": "string - realistic company name (mix of tech, manufacturing, retail, etc.)",
                            "phone": "string - US phone format: +1-555-XXX-XXXX (optional, 70% of leads have phone)",
                            "title": "string - professional title like CTO, VP Sales, Director Marketing, etc.",
                            
                            "lead_source": "one of: website|linkedin|email_campaign|referral|cold_outreach|trade_show|webinar|other",
                            "status": "new (always start with new)",
                            
                            "company_size": "integer - number of employees (10-5000 range, realistic distribution)",
                            "annual_revenue": "integer - company revenue in dollars (100K to 500M range)",
                            "budget": "integer - potential budget for solution in dollars (10K to 1M range, should be reasonable for company size)",
                            "decision_maker": "boolean - true for C-level, VPs, Directors; false for managers and below",
                            "pain_points": "array of strings - 1-4 realistic business pain points like 'manual processes', 'data silos', 'scaling challenges', 'cost optimization'",
                            "timeline": "one of: immediate|3_months|6_months|next_year",
                            
                            "notes": "string - brief note about lead context or conversation summary (2-3 sentences)",
                            "tags": "array of strings - 1-3 relevant tags like 'enterprise', 'startup', 'tech', 'manufacturing'"


                        IMPORTANT GUIDELINES:
                        1. Make data realistic and internally consistent (budget should match company size/revenue)
                        2. Use diverse industries: technology, manufacturing, healthcare, finance, retail, consulting
                        3. Vary lead quality - mix of high-value enterprise leads and smaller prospects  
                        4. Pain points should be relevant to the industry and company size
                        5. Decision maker status should align with title level
                        6. Timeline should correlate somewhat with budget (higher budgets often have longer timelines)
                        7. Create leads that would be realistic for a B2B SaaS sales pipeline

                        Generate {count} unique leads as a JSON array. Ensure no duplicate emails.
                        """
        return schema_prompt
    
    def generate_contextual_prompt(self, count: int = 10) -> str:
        """Generate a more contextual prompt for specific scenarios"""
        
        base_context = f"""
                        Generate {count} realistic B2B sales leads for a SaaS company demo. 
                        """                    
        quality_context = {
            "high": "Focus on enterprise leads with larger budgets (50K+) and senior decision makers.",
            "medium": "Mix of mid-market companies with moderate budgets (10K-50K).",
            "mixed": "Diverse mix of company sizes from startups to enterprise.",
            "startup": "Focus on smaller, growing companies with limited budgets but immediate needs."
        }
        
        base_context += quality_context["mixed"]
        
        return base_context + "\n\n" + self.generate_lead_schema_prompt().format(count=count)
    

    def generate_leads_with_grok(self, count: int = 10, temperature: float = 0.7) -> List[Dict]:
        """Generate synthetic leads using Grok API"""
        
        prompt = self.generate_contextual_prompt(count)
        
        messages = [SystemMessage(content="You are an expert at generating realistic B2B sales lead data. Always respond with valid JSON only, no additional text."),HumanMessage(content=prompt)]
        
        try:
            response = self.llm.invoke(messages)
            content = response.content
                
            # Parse JSON response
            try:
                data = json.loads(content)
                # Handle if Grok returns an object with a "leads" array or just an array
                if isinstance(data, dict) and 'leads' in data:
                    return data['leads']
                elif isinstance(data, list):
                    return data
                else:
                    raise ValueError("Unexpected response format")                
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON response: {e}")
                print(f"Raw response: {content}")
                return []                
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return []
