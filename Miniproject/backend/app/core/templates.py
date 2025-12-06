# backend/app/core/templates.py
"""
Custom investigation prompt templates.
Allows jurisdiction-specific, crime-type-specific, and custom prompts.
"""
from typing import Dict, Any
from enum import Enum

class CrimeType(str, Enum):
    """Enumeration of crime types for template selection."""
    HOMICIDE = "homicide"
    THEFT = "theft"
    FRAUD = "fraud"
    ASSAULT = "assault"
    CYBERCRIME = "cybercrime"
    ARSON = "arson"
    GENERIC = "generic"

class Jurisdiction(str, Enum):
    """Enumeration of jurisdictions for template selection."""
    US_FEDERAL = "us_federal"
    US_STATE = "us_state"
    US_LOCAL = "us_local"
    UK = "uk"
    INTERNATIONAL = "international"

class InvestigationTemplate:
    """Base template for investigation."""
    
    def __init__(self, name: str, description: str, stages: Dict[str, str]):
        self.name = name
        self.description = description
        self.stages = stages
    
    def get_stage(self, stage_name: str) -> str:
        """Get prompt for a specific stage."""
        return self.stages.get(stage_name, "")

# ============ Homicide Template ============
HOMICIDE_TEMPLATE = InvestigationTemplate(
    name="Homicide Investigation",
    description="Specialized for homicide cases",
    stages={
        "summarize": """Analyze the homicide case evidence. Extract:
1. Victim: Name, age, occupation, relationships
2. Crime scene: Location, time of death, cause of death (if determined)
3. Physical evidence: Weapon, blood evidence, forensic findings
4. Witness statements: Who saw what, when, and where
5. Suspect list: Names mentioned, motives, access to weapon
6. Timeline: Chronological reconstruction from evidence
7. Inconsistencies: Conflicting statements, timeline gaps
Return JSON: {victim, crime_scene, physical_evidence, witnesses, suspects, timeline, inconsistencies}""",
        
        "timeline": """Build a detailed homicide timeline:
- When was victim last seen alive?
- When was victim discovered?
- Where could suspect have been at each time?
- Evidence placement timeline
Include time of death estimation, alibi verification, and suspicious gaps.
Return JSON: {timeline: [{timestamp, event, evidence_ids, confidence}], narrative, investigative_gaps}""",
        
        "suspects": """Rank suspects by motive, means, opportunity:
For each suspect:
- Motive: Financial gain, revenge, crime of passion, other
- Means: Access to weapon, physical capability
- Opportunity: Lack of alibi, presence at scene
- Evidence against: Physical, testimonial, circumstantial
- Evidence for innocence: Strong alibi, exculpatory evidence
Calculate confidence score (0-100) based on evidence weight.
Return JSON: {suspects: [{name, motive, means, opportunity, evidence_against, exculpatory_evidence, confidence_score}], primary_suspect}""",
        
        "validate": """Validate homicide investigation findings:
- Confirm victim identification
- Validate time of death (medical examiner conclusions vs evidence)
- Verify alibi claims against timeline
- Assess physical evidence reliability
- Identify missing evidence needed for prosecution
Return JSON: {validated_facts, uncertain_findings, missing_evidence, prosecution_strength}"""
    }
)

# ============ Theft Template ============
THEFT_TEMPLATE = InvestigationTemplate(
    name="Theft Investigation",
    description="Specialized for theft/larceny cases",
    stages={
        "summarize": """Analyze the theft case. Extract:
1. Item(s) stolen: Description, value, serial numbers, distinguishing marks
2. Timeline: When last seen, when theft discovered, opportunity window
3. Access: Who had access to location, security measures, lock status
4. Suspects: Who had motive (financial need, grudge), access, opportunity
5. Witnesses: Anyone who saw suspect, items, suspicious activity
6. Evidence: Security footage, fingerprints, tool marks, witness ID
7. Pattern: Is this part of a series? Similar thefts?
Return JSON: {items_stolen, timeline, access_control, suspects, witnesses, physical_evidence, pattern_analysis}""",
        
        "timeline": """Build theft timeline:
- When item was last confirmed present
- Window of opportunity for theft
- When theft was discovered
- Movement of suspect(s) before/after theft
- Recovery attempts or sales of stolen items
Return JSON: {opportunity_window, suspect_movements, discovery_timeline, item_disposition}""",
        
        "suspects": """Rank suspects by motive and opportunity:
- Financial motive: Debt, poverty, greed, need for specific item
- Opportunity: Was at location, had access, no strong alibi
- Capability: Physical ability, skills to steal item, knowledge of security
- History: Prior theft arrests, known associates
Calculate score based on strength of each factor.
Return JSON: {suspects: [{name, financial_motive, opportunity_strength, capability, criminal_history, confidence_score}]}""",
        
        "validate": """Validate theft investigation:
- Is item identification certain?
- Can value be authenticated?
- Are timeline estimates based on solid evidence?
- Is suspect access actually established?
- Could theft be internal (employee) vs external?
Recommend follow-up: Pawn shops, fences, social media sales, recovered item searches.
Return JSON: {validated_facts, disputed_facts, missing_evidence, recovery_prospects}"""
    }
)

# ============ Generic/Flexible Template ============
GENERIC_TEMPLATE = InvestigationTemplate(
    name="Generic Investigation",
    description="Flexible template for any crime type",
    stages={
        "summarize": """Summarize key facts from evidence:
- What happened? (narrative of alleged crime)
- Who was involved? (victims, witnesses, suspects)
- Where did it happen? (location details, geography)
- When did it happen? (timeline, duration)
- Why might it have happened? (potential motives)
- Evidence present? (physical, testimonial, documentary)
- Evidence missing? (gaps in investigation)
Return JSON: {narrative, people_involved, location, timeline_sketch, potential_motives, evidence_present, gaps}""",
        
        "timeline": """Build detailed chronological timeline:
For each event:
- Timestamp or timeframe
- What happened (action/observation)
- Who was involved
- Physical location
- Supporting evidence (IDs of evidence items)
- Confidence level (high/medium/low) based on evidence strength
Include commentary on timeline consistency and suspicious gaps.
Return JSON: {timeline: [{timestamp, event, people, location, evidence_ids, confidence}], narrative_summary, inconsistencies}""",
        
        "suspects": """Identify and rank potential suspects:
For each suspect evaluate:
- Connection to crime (victim, location, evidence)
- Motive (financial, personal, other)
- Opportunity (access, alibi assessment)
- Capability (skills, resources needed)
- Evidence against: direct, circumstantial, behavioral
- Evidence for innocence: alibis, exculpatory evidence
Assign confidence score 0-100.
Return JSON: {suspects: [{name, connection, motive, opportunity, capability, evidence_against, exculpatory_evidence, confidence_score}], investigation_priority}""",
        
        "validate": """Validate investigation findings:
Cross-check all major claims against evidence:
- Are timeline events based on reliable sources?
- Are suspect identifications solid (ID, witness recognition)?
- Do physical evidence links hold up (no contamination, proper chain of custody)?
- Are alternative explanations ruled out?
Identify:
- Strongest evidence
- Weakest links
- Critical missing evidence
- Prosecution challenges
Return JSON: {strongest_evidence, weakest_links, missing_evidence, prosecution_viability, next_steps}"""
    }
)

# ============ Template Registry ============
TEMPLATES: Dict[str, InvestigationTemplate] = {
    CrimeType.HOMICIDE: HOMICIDE_TEMPLATE,
    CrimeType.THEFT: THEFT_TEMPLATE,
    CrimeType.GENERIC: GENERIC_TEMPLATE,
    # Others default to generic
}

def get_template(crime_type: str = None, custom_template: Dict[str, str] = None) -> InvestigationTemplate:
    """
    Get investigation template by crime type.
    
    Args:
        crime_type: Type of crime (homicide, theft, etc.)
        custom_template: Optional custom stages dict to override default
    
    Returns:
        InvestigationTemplate instance
    """
    # Return custom if provided
    if custom_template:
        return InvestigationTemplate(
            name="Custom Investigation",
            description="User-provided custom template",
            stages=custom_template
        )
    
    # Lookup by crime type
    if crime_type:
        template = TEMPLATES.get(crime_type.lower())
        if template:
            return template
    
    # Default to generic
    return GENERIC_TEMPLATE

def list_available_templates() -> Dict[str, str]:
    """List all available template names and descriptions."""
    return {
        name: template.description
        for name, template in TEMPLATES.items()
    }
