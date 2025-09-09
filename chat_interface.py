import json
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import sys
from langchain_xai import ChatXAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from dataclasses import asdict

class GrokLeadCLI:
    """Interactive command line interface for lead analysis using Grok"""
    
    def __init__(self, api_key: str, leads_data: List[Dict], base_url: str = "https://api.x.ai/v1"):
        self.api_key = api_key
        self.llm = ChatXAI(model="grok-4", api_key=self.api_key, temperature=0.7)
        self.leads_data = leads_data
        self.conversation_history = []
        
        print(f"🚀 Grok Lead Analyzer initialized with {len(leads_data)} leads")
        print("Type 'help' for available commands or ask natural language questions!")
    
    def create_context_prompt(self, user_query: str) -> str:
        """Create a context-aware prompt with lead data"""
        
        leads_list = []
        for lead in self.leads_data:
            leads_list.append(asdict(lead))
        
        context_prompt = f"""
                        You are a sales intelligence assistant analyzing a lead database. 

                        LEAD DATABASE CONTEXT:
                        Total Leads: {len(self.leads_data)}
                        Sample Data Structure: {json.dumps(leads_list[0] if leads_list else {}, indent=2)}

                        AVAILABLE LEAD DATA FIELDS:
                        - first_name, last_name, email, company, phone, title
                        - lead_source, status, company_size, annual_revenue, budget
                        - decision_maker, pain_points, timeline, qualification_score
                        - notes, tags, created_at, updated_at

                        LEADS:
                        {json.dumps(leads_list, indent=2)}

                        USER QUERY: {user_query}

                        INSTRUCTIONS:
                        1. Analyze the lead data to answer the user's question
                        2. Provide specific insights with numbers and examples
                        3. If asked to find/filter leads, describe the criteria and potential matches
                        4. For analysis requests, provide actionable insights
                        5. Be conversational and helpful
                        6. If you need to see more data, ask the user to be more specific

                        Respond in a helpful, analytical tone with specific insights based on the data.
                        """        
        return context_prompt
    
    def query_grok(self, prompt: str) -> str:
        """Send query to Grok and get response"""
        self.conversation_history.append(prompt)
        messages = [SystemMessage(content="You are a sales intelligence assistant. Analyze lead data and provide actionable insights. Be specific and data-driven in your responses."),HumanMessage(content=" ".join(self.conversation_history))]
        
        try:
            response = self.llm.invoke(messages)
            return response.content                
        except requests.exceptions.RequestException as e:
            return f"❌ API Error: {e}"
        except Exception as e:
            return f"❌ Unexpected error: {e}"
    
    def process_local_query(self, query: str) -> str:
        """Process queries that can be handled locally without Grok"""
        
        query_lower = query.lower()
        
        if "count" in query_lower and "leads" in query_lower:
            return f"📊 Total leads in database: {len(self.leads_data)}"
        
        elif "qualified" in query_lower:
            qualified = [lead for lead in self.leads_data if lead.qualification_score >= 70]
            return f"✅ Qualified leads (score ≥70): {len(qualified)} out of {len(self.leads_data)}"
        
        elif "hot" in query_lower:
            hot = [lead for lead in self.leads_data if lead.qualification_score >= 85]
            return f"🔥 Hot leads (score ≥85): {len(hot)} out of {len(self.leads_data)}"
        
        elif "average score" in query_lower or "avg score" in query_lower:
            scores = [lead.qualification_score for lead in self.leads_data]
            avg_score = sum(scores) / len(scores) if scores else 0
            return f"📈 Average qualification score: {avg_score:.1f}"
        
        elif "companies" in query_lower and "list" in query_lower:
            companies = list(set(lead.company for lead in self.leads_data))
            companies.sort()
            return f"🏢 Companies ({len(companies)}): {', '.join(companies[:10])}{'...' if len(companies) > 10 else ''}"
        
        elif query_lower in ["help", "commands", "?"]:
            return self.show_help()
        
        return None  # Let Grok handle it
    
    def show_help(self) -> str:
        """Show available commands and examples"""
        
        help_text = """
                    🤖 GROK LEAD ANALYZER - HELP

                    QUICK COMMANDS (processed locally):
                    • count leads - Show total number of leads
                    • qualified leads - Show count of qualified leads (score ≥70)
                    • hot leads - Show count of hot leads (score ≥85)  
                    • average score - Show average qualification score
                    • list companies - Show all companies in database

                    NATURAL LANGUAGE QUERIES (sent to Grok):
                    • "Who are the highest scoring leads?"
                    • "Show me leads from technology companies"
                    • "Which leads have immediate timeline?"
                    • "Analyze leads by company size"
                    • "What are the most common pain points?"
                    • "Find decision makers with budgets over $50k"
                    • "Which lead sources perform best?"
                    • "Summarize the pipeline status"

                    ADVANCED ANALYSIS:
                    • "Create a report on enterprise leads"
                    • "What's the conversion rate by lead source?"
                    • "Recommend follow-up actions for hot leads"
                    • "Compare leads by industry vertical"

                    SPECIAL COMMANDS:
                    • help - Show this help
                    • quit/exit - Exit the program
                    • clear - Clear conversation history
                    • stats - Show database statistics

                    Just ask in natural language - Grok will analyze your lead data!
                    """
        return help_text
    
    def show_stats(self) -> str:
        """Show comprehensive database statistics"""
        
        if not self.leads_data:
            return "No leads in database"
        
        # Calculate statistics
        total_leads = len(self.leads_data)
        scores = [lead.qualification_score for lead in self.leads_data]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Count by status
        status_counts = {}
        for lead in self.leads_data:
            status = lead.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count by lead source
        source_counts = {}
        for lead in self.leads_data:
            source = lead.lead_source
            source_counts[source] = source_counts.get(source, 0) + 1
        
        # Decision makers
        decision_makers = sum(1 for lead in self.leads_data if lead.decision_maker)
        
        # Budget analysis
        budgets = [lead.budget for lead in self.leads_data if lead.budget]
        avg_budget = sum(budgets) / len(budgets) if budgets else 0
        
        stats = f"""
                📊 LEAD DATABASE STATISTICS

                OVERVIEW:
                • Total Leads: {total_leads}
                • Average Score: {avg_score:.1f}
                • Decision Makers: {decision_makers} ({decision_makers/total_leads*100:.1f}%)
                • Average Budget: ${avg_budget:,.0f}

                STATUS BREAKDOWN:
                {chr(10).join(f'• {status.title()}: {count}' for status, count in status_counts.items())}

                LEAD SOURCES:
                {chr(10).join(f'• {source.title()}: {count}' for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True))}

                QUALIFICATION:
                • Qualified (≥70): {len([s for s in scores if s >= 70])}
                • Hot Leads (≥85): {len([s for s in scores if s >= 85])}
                • Score Range: {min(scores):.1f} - {max(scores):.1f}
                        """
        return stats
    
    def run_interactive_session(self):
        """Main interactive loop"""
        
        print("\n" + "="*60)
        print("🎯 Welcome to Grok Lead Analyzer!")
        print("Ask questions about your leads in natural language.")
        print("Type 'help' for commands or 'quit' to exit.")
        print("="*60 + "\n")
        
        while True:
            try:
                # Get user input
                user_input = input("🤔 Ask about your leads: ").strip()
                
                if not user_input:
                    continue
                
                # Handle exit commands
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Thanks for using Grok Lead Analyzer!")
                    break
                
                # Handle clear command
                if user_input.lower() == 'clear':
                    self.conversation_history.clear()
                    print("🧹 Conversation history cleared!")
                    continue
                
                # Handle stats command
                if user_input.lower() == 'stats':
                    print(self.show_stats())
                    continue
                
                print("🤖 Analyzing...")
                
                # Try local processing first
                local_response = self.process_local_query(user_input)
                
                if local_response:
                    print(f"\n{local_response}\n")
                else:                    
                    # Send to Grok for analysis
                    context_prompt = self.create_context_prompt(user_input)
                    response = self.query_grok(context_prompt)
                    
                    print(f"\n🎯 Grok Analysis:\n{response}\n")
                    
                    # Store in conversation history
                    self.conversation_history.append(response)
                
            except KeyboardInterrupt:
                print("\n👋 Exiting Grok Lead Analyzer...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                continue

def quick_lead_query(api_key: str, leads_data: List[Dict], query: str) -> str:
    """One-shot function for quick lead queries without interactive mode"""
    
    cli = GrokLeadCLI(api_key, leads_data)
    
    # Try local processing first
    local_response = cli.process_local_query(query)
    if local_response:
        return local_response
    
    # Send to Grok
    context_prompt = cli.create_context_prompt(query)
    return cli.query_grok(context_prompt)

