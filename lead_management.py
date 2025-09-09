from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
import json
import uuid

class LeadStatus(Enum):
    NEW = "new"
    QUALIFIED = "qualified"
    CONTACTED = "contacted"
    MEETING_SCHEDULED = "meeting_scheduled"
    PROPOSAL_SENT = "proposal_sent"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    UNQUALIFIED = "unqualified"

class LeadSource(Enum):
    WEBSITE = "website"
    LINKEDIN = "linkedin"
    EMAIL_CAMPAIGN = "email_campaign"
    REFERRAL = "referral"
    COLD_OUTREACH = "cold_outreach"
    TRADE_SHOW = "trade_show"
    WEBINAR = "webinar"
    OTHER = "other"

@dataclass
class ScoringCriteria:
    """Configuration for lead scoring weights and thresholds"""
    company_size_weight: float = 0.25
    budget_weight: float = 0.30
    authority_weight: float = 0.20
    need_weight: float = 0.15
    timeline_weight: float = 0.10
    
    # Thresholds for qualification
    qualified_threshold: float = 70.0
    hot_lead_threshold: float = 85.0
    
    def validate_weights(self) -> bool:
        """Ensure weights sum to 1.0"""
        total = (self.company_size_weight + self.budget_weight + 
                self.authority_weight + self.need_weight + self.timeline_weight)
        return abs(total - 1.0) < 0.001

@dataclass
class Lead:
    """Core lead data structure"""
    # Basic Information
    first_name: str
    last_name: str
    email: str
    company: str
    phone: Optional[str] = None
    title: Optional[str] = None
    
    # Lead Details
    lead_source: LeadSource = LeadSource.OTHER
    status: LeadStatus = LeadStatus.NEW
    created_at: str = None
    updated_at: str = None
    
    # Qualification Data
    company_size: Optional[int] = None  # Number of employees
    annual_revenue: Optional[int] = None  # In dollars
    budget: Optional[int] = None  # Budget for solution
    decision_maker: bool = False  # Is this person a decision maker
    pain_points: List[str] = field(default_factory=list)
    timeline: Optional[str] = None  # "immediate", "3_months", "6_months", "next_year"
    
    # Scoring and Notes
    qualification_score: float = 0.0
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    
    # System Fields
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    last_contacted: Optional[str] = None
    next_follow_up: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_qualified(self) -> bool:
        return self.qualification_score >= 70.0
    
    @property
    def is_hot_lead(self) -> bool:
        return self.qualification_score >= 85.0
    
    def to_dict(self):
        return {
            "name": self.name,
            "id": self.id
        }

class LeadManager:
    """Lead management and qualification system"""
    
    def __init__(self, scoring_criteria: Optional[ScoringCriteria] = None):
        self.leads: Dict[str, Lead] = {}
        self.scoring_criteria = scoring_criteria or ScoringCriteria()
        self.interaction_history: Dict[str, List[Dict]] = {}
        
        if not self.scoring_criteria.validate_weights():
            raise ValueError("Scoring criteria weights must sum to 1.0")
    
    def add_lead(self, lead: Lead) -> str:
        """Add a new lead to the system"""
        if not lead.id:
            lead.id = str(uuid.uuid4())
        
        # Validate required fields
        if not all([lead.first_name, lead.last_name, lead.email, lead.company]):
            raise ValueError("Lead must have first_name, last_name, email, and company")
        
        # Check for duplicate email
        if self.find_lead_by_email(lead.email):
            raise ValueError(f"Lead with email {lead.email} already exists")
        
        lead.updated_at = str(datetime.now())
        self.leads[lead.id] = lead
        self.interaction_history[lead.id] = []
        
        # Auto-qualify the lead
        self.qualify_lead(lead.id)
        
        return lead.id
    
    def get_lead(self, lead_id: str) -> Optional[Lead]:
        """Get a lead by ID"""
        return self.leads.get(lead_id)
    
    def update_lead(self, lead_id: str, **updates) -> bool:
        """Update lead information"""
        if lead_id not in self.leads:
            return False
        
        lead = self.leads[lead_id]
        
        # Update fields
        for key, value in updates.items():
            if hasattr(lead, key):
                setattr(lead, key, value)
        
        lead.updated_at = str(datetime.now())
        
        # Re-qualify if qualification data changed
        qualification_fields = {
            'company_size', 'annual_revenue', 'budget', 
            'decision_maker', 'timeline', 'pain_points'
        }
        if any(field in updates for field in qualification_fields):
            self.qualify_lead(lead_id)
        
        return True
    
    def delete_lead(self, lead_id: str) -> bool:
        """Delete a lead"""
        if lead_id in self.leads:
            del self.leads[lead_id]
            if lead_id in self.interaction_history:
                del self.interaction_history[lead_id]
            return True
        return False
    
    def find_lead_by_email(self, email: str) -> Optional[Lead]:
        """Find lead by email address"""
        for lead in self.leads.values():
            if lead.email.lower() == email.lower():
                return lead
        return None
    
    def search_leads(self, query: str) -> List[Lead]:
        """Search leads by name, company, or email"""
        query = query.lower()
        results = []
        
        for lead in self.leads.values():
            searchable_text = f"{lead.full_name} {lead.company} {lead.email}".lower()
            if query in searchable_text:
                results.append(lead)
        
        return results
    
    def qualify_lead(self, lead_id: str) -> float:
        """Calculate qualification score for a lead"""
        lead = self.leads.get(lead_id)
        if not lead:
            return 0.0
        
        score = 0.0
        
        # Company Size Score (0-100)
        company_score = self._score_company_size(lead.company_size)
        score += company_score * self.scoring_criteria.company_size_weight
        
        # Budget Score (0-100)
        budget_score = self._score_budget(lead.budget, lead.annual_revenue)
        score += budget_score * self.scoring_criteria.budget_weight
        
        # Authority Score (0-100)
        authority_score = self._score_authority(lead.decision_maker, lead.title)
        score += authority_score * self.scoring_criteria.authority_weight
        
        # Need Score (0-100)
        need_score = self._score_need(lead.pain_points)
        score += need_score * self.scoring_criteria.need_weight
        
        # Timeline Score (0-100)
        timeline_score = self._score_timeline(lead.timeline)
        score += timeline_score * self.scoring_criteria.timeline_weight
        
        lead.qualification_score = round(score, 2)
        
        # Auto-update status based on score
        if lead.status == LeadStatus.NEW:
            if lead.qualification_score >= self.scoring_criteria.qualified_threshold:
                lead.status = LeadStatus.QUALIFIED
            else:
                lead.status = LeadStatus.UNQUALIFIED
        
        return lead.qualification_score
    
    def _score_company_size(self, company_size: Optional[int]) -> float:
        """Score based on company size (employees)"""
        if not company_size:
            return 50.0  # Default/unknown
        
        if company_size >= 1000:
            return 100.0
        elif company_size >= 500:
            return 85.0
        elif company_size >= 100:
            return 70.0
        elif company_size >= 50:
            return 55.0
        elif company_size >= 10:
            return 40.0
        else:
            return 25.0
    
    def _score_budget(self, budget: Optional[int], annual_revenue: Optional[int]) -> float:
        """Score based on budget and company revenue"""
        if budget:
            if budget >= 100000:
                return 100.0
            elif budget >= 50000:
                return 80.0
            elif budget >= 25000:
                return 60.0
            elif budget >= 10000:
                return 40.0
            else:
                return 20.0
        
        # Estimate budget from revenue if available
        if annual_revenue:
            estimated_budget = annual_revenue * 0.05  # Assume 5% of revenue
            return self._score_budget(int(estimated_budget), None)
        
        return 30.0  # Default when no budget info
    
    def _score_authority(self, is_decision_maker: bool, title: Optional[str]) -> float:
        """Score based on decision-making authority"""
        if is_decision_maker:
            return 100.0
        
        if not title:
            return 40.0
        
        title_lower = title.lower()
        
        # C-level executives
        if any(word in title_lower for word in ['ceo', 'cto', 'cfo', 'cmo', 'president']):
            return 95.0
        
        # Directors and VPs
        if any(word in title_lower for word in ['director', 'vp', 'vice president']):
            return 80.0
        
        # Managers
        if 'manager' in title_lower:
            return 65.0
        
        # Senior roles
        if 'senior' in title_lower:
            return 50.0
        
        return 35.0
    
    def _score_need(self, pain_points: List[str]) -> float:
        """Score based on identified pain points"""
        if not pain_points:
            return 30.0
        
        # More pain points = higher need
        base_score = min(len(pain_points) * 25, 100)
        
        # Boost for specific high-value pain points
        high_value_keywords = [
            'efficiency', 'cost', 'revenue', 'growth', 'scale', 
            'competition', 'manual', 'time', 'error'
        ]
        
        pain_text = ' '.join(pain_points).lower()
        keyword_matches = sum(1 for keyword in high_value_keywords if keyword in pain_text)
        
        bonus = min(keyword_matches * 10, 30)
        return min(base_score + bonus, 100.0)
    
    def _score_timeline(self, timeline: Optional[str]) -> float:
        """Score based on purchase timeline"""
        if not timeline:
            return 40.0
        
        timeline_scores = {
            'immediate': 100.0,
            '3_months': 80.0,
            '6_months': 60.0,
            'next_year': 30.0
        }
        
        return timeline_scores.get(timeline, 40.0)
    
    def get_qualified_leads(self) -> List[Lead]:
        """Get all qualified leads"""
        return [lead for lead in self.leads.values() if lead.is_qualified]
    
    def get_hot_leads(self) -> List[Lead]:
        """Get high-scoring leads"""
        return [lead for lead in self.leads.values() if lead.is_hot_lead]
    
    def get_leads_by_status(self, status: LeadStatus) -> List[Lead]:
        """Get leads by status"""
        return [lead for lead in self.leads.values() if lead.status == status]
    
    def add_interaction(self, lead_id: str, interaction_type: str, details: str) -> bool:
        """Log an interaction with a lead"""
        if lead_id not in self.leads:
            return False
        
        interaction = {
            'id': str(uuid.uuid4()),
            'timestamp': str(datetime.now().isoformat()),
            'type': interaction_type,
            'details': details
        }
        
        self.interaction_history[lead_id].append(interaction)
        
        # Update last_contacted if it's a contact interaction
        if interaction_type in ['email', 'call', 'meeting']:
            self.leads[lead_id].last_contacted = str(datetime.now())
        
        return True
    
    def get_interaction_history(self, lead_id: str) -> List[Dict]:
        """Get interaction history for a lead"""
        return self.interaction_history.get(lead_id, [])
    
    def update_scoring_criteria(self, new_criteria: ScoringCriteria) -> bool:
        """Update scoring criteria and re-score all leads"""
        if not new_criteria.validate_weights():
            return False
        
        self.scoring_criteria = new_criteria
        
        # Re-qualify all leads with new criteria
        for lead_id in self.leads.keys():
            self.qualify_lead(lead_id)
        
        return True
    
    def get_pipeline_summary(self) -> Dict[str, Any]:
        """Get pipeline summary statistics"""
        total_leads = len(self.leads)
        
        if total_leads == 0:
            return {'total_leads': 0}
        
        status_counts = {}
        for status in LeadStatus:
            status_counts[status.value] = len(self.get_leads_by_status(status))
        
        qualified_count = len(self.get_qualified_leads())
        hot_leads_count = len(self.get_hot_leads())
        
        avg_score = sum(lead.qualification_score for lead in self.leads.values()) / total_leads
        
        return {
            'total_leads': total_leads,
            'qualified_leads': qualified_count,
            'hot_leads': hot_leads_count,
            'qualification_rate': (qualified_count / total_leads) * 100,
            'average_score': round(avg_score, 2),
            'status_breakdown': status_counts
        }
    
    def export_leads_json(self) -> str:
        """Export all leads as JSON"""
        export_data = {
            'leads': {},
            'scoring_criteria': {
                'company_size_weight': self.scoring_criteria.company_size_weight,
                'budget_weight': self.scoring_criteria.budget_weight,
                'authority_weight': self.scoring_criteria.authority_weight,
                'need_weight': self.scoring_criteria.need_weight,
                'timeline_weight': self.scoring_criteria.timeline_weight,
                'qualified_threshold': self.scoring_criteria.qualified_threshold,
                'hot_lead_threshold': self.scoring_criteria.hot_lead_threshold
            },
            'export_timestamp': str(datetime.now().isoformat())
        }
        
        for lead_id, lead in self.leads.items():
            export_data['leads'][lead_id] = {
                'first_name': lead.first_name,
                'last_name': lead.last_name,
                'email': lead.email,
                'company': lead.company,
                'phone': lead.phone,
                'title': lead.title,
                'lead_source': lead.lead_source.value,
                'status': lead.status.value,
                'created_at': lead.created_at.isoformat(),
                'updated_at': lead.updated_at.isoformat(),
                'company_size': lead.company_size,
                'annual_revenue': lead.annual_revenue,
                'budget': lead.budget,
                'decision_maker': lead.decision_maker,
                'pain_points': lead.pain_points,
                'timeline': lead.timeline,
                'qualification_score': lead.qualification_score,
                'notes': lead.notes,
                'tags': lead.tags,
                'last_contacted': lead.last_contacted.isoformat() if lead.last_contacted else None,
                'next_follow_up': lead.next_follow_up.isoformat() if lead.next_follow_up else None
            }
        
        return json.dumps(export_data, indent=2)

    def create_lead_objects_from_data(self, synthetic_data: List[Dict]) -> List[str]:
        """Convert synthetic data to Lead objects and add to LeadManager"""
        lead_ids = []
        for data in synthetic_data:
            try:
                # Map string values to enums
                lead_source = LeadSource(data.get('lead_source', 'other'))
                status = LeadStatus(data.get('status', 'new'))
                
                # Create Lead object
                lead = Lead(
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    email=data['email'],
                    company=data['company'],
                    phone=data.get('phone'),
                    title=data.get('title'),
                    lead_source=data.get('lead_source', 'other'),
                    status=data.get('status', 'new'),
                    company_size=data.get('company_size'),
                    annual_revenue=data.get('annual_revenue'),
                    budget=data.get('budget'),
                    decision_maker=data.get('decision_maker', False),
                    pain_points=data.get('pain_points', []),
                    timeline=data.get('timeline'),
                    notes=data.get('notes', ''),
                    tags=data.get('tags', [])
                )
                
                # Add to lead manager
                lead_ids.append(self.add_lead(lead))
            except Exception as e:
                print(f"Error creating lead from data {data.get('email', 'unknown')}: {e}")
                continue
        
        return lead_ids    
