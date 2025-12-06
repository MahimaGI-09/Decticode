# backend/app/core/explainability.py
"""
Explainability module for investigation results.
Generates detailed explanations with evidence citations and confidence scoring.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

class ExplainabilityReport:
    """Comprehensive explainability report for investigation findings."""
    
    def __init__(self, case_id: str, investigation_stage: str):
        self.case_id = case_id
        self.investigation_stage = investigation_stage
        self.generated_at = datetime.utcnow().isoformat()
        self.claims = []
        self.evidence_citations = {}
        self.confidence_breakdown = {}
    
    def add_claim(
        self,
        claim: str,
        confidence: float,
        supporting_evidence_ids: List[str],
        evidence_texts: List[str] = None,
        reasoning: str = "",
        alternative_explanations: List[str] = None
    ) -> None:
        """
        Add a claim with full explainability metadata.
        
        Args:
            claim: The claim being made
            confidence: Confidence score 0-100
            supporting_evidence_ids: List of evidence IDs supporting this claim
            evidence_texts: Actual excerpts from evidence
            reasoning: Explanation of how evidence supports claim
            alternative_explanations: Other possible explanations
        """
        claim_obj = {
            "claim": claim,
            "confidence": confidence,
            "supporting_evidence_ids": supporting_evidence_ids,
            "evidence_excerpts": evidence_texts or [],
            "reasoning": reasoning,
            "alternative_explanations": alternative_explanations or [],
            "added_at": datetime.utcnow().isoformat()
        }
        self.claims.append(claim_obj)
        
        # Track evidence usage
        for evidence_id in supporting_evidence_ids:
            if evidence_id not in self.evidence_citations:
                self.evidence_citations[evidence_id] = []
            self.evidence_citations[evidence_id].append(claim)
    
    def add_confidence_analysis(
        self,
        finding: str,
        factors: Dict[str, float],
        overall_confidence: float,
        caveats: List[str] = None
    ) -> None:
        """
        Record confidence breakdown for a finding.
        
        Args:
            finding: The finding being analyzed
            factors: Dict of {factor_name: contribution_weight} (sum to 1.0)
            overall_confidence: Final confidence 0-100
            caveats: Limitations or concerns
        """
        self.confidence_breakdown[finding] = {
            "confidence": overall_confidence,
            "factors": factors,
            "caveats": caveats or [],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "case_id": self.case_id,
            "investigation_stage": self.investigation_stage,
            "generated_at": self.generated_at,
            "claims": self.claims,
            "evidence_citations": self.evidence_citations,
            "confidence_breakdown": self.confidence_breakdown,
            "summary": {
                "total_claims": len(self.claims),
                "average_confidence": sum(c["confidence"] for c in self.claims) / len(self.claims) if self.claims else 0,
                "evidence_count": len(self.evidence_citations),
                "most_cited_evidence": sorted(
                    self.evidence_citations.items(),
                    key=lambda x: len(x[1]),
                    reverse=True
                )[:5]
            }
        }
    
    def to_json(self) -> str:
        """Convert report to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

class ExplainabilityDashboard:
    """Dashboard for viewing investigation findings with full explainability."""
    
    def __init__(self, case_id: str, investigation_results: Dict[str, Any]):
        self.case_id = case_id
        self.results = investigation_results
        self.reports = {}
        self._generate_reports()
    
    def _generate_reports(self) -> None:
        """Generate explainability reports from investigation stages."""
        if "stages" not in self.results:
            return
        
        # Create report for each stage
        for stage_name, stage_result in self.results["stages"].items():
            report = ExplainabilityReport(self.case_id, stage_name)
            
            if not stage_result.get("parsed"):
                continue
            
            parsed = stage_result["parsed"]
            
            # Extract and explain findings based on stage type
            if stage_name == "timeline":
                self._explain_timeline(parsed, report)
            elif stage_name == "suspects":
                self._explain_suspects(parsed, report)
            elif stage_name == "summarize":
                self._explain_summary(parsed, report)
            elif stage_name == "validation":
                self._explain_validation(parsed, report)
            
            self.reports[stage_name] = report
    
    def _explain_timeline(self, timeline_data: Dict, report: ExplainabilityReport) -> None:
        """Generate explainability for timeline stage."""
        if not isinstance(timeline_data.get("timeline"), list):
            return
        
        for event in timeline_data["timeline"]:
            evidence_ids = event.get("evidence_ids", [])
            confidence = 100 if event.get("confidence") == "high" else 70 if event.get("confidence") == "medium" else 40
            
            report.add_claim(
                claim=event.get("event", "Unknown event"),
                confidence=confidence,
                supporting_evidence_ids=evidence_ids,
                reasoning=f"Based on {event.get('type', 'evidence')} at {event.get('timestamp', 'unknown time')}"
            )
    
    def _explain_suspects(self, suspects_data: Dict, report: ExplainabilityReport) -> None:
        """Generate explainability for suspects stage."""
        if not isinstance(suspects_data.get("suspects"), list):
            return
        
        for suspect in suspects_data["suspects"]:
            evidence_against = suspect.get("evidence_against", [])
            evidence_for = suspect.get("exculpatory_evidence", [])
            confidence = suspect.get("confidence_score", 50)
            
            factors = {}
            if suspect.get("motive"):
                factors["motive"] = 0.3
            if suspect.get("opportunity"):
                factors["opportunity"] = 0.4
            if evidence_against:
                factors["evidence"] = 0.3
            
            report.add_claim(
                claim=f"{suspect.get('name')} is a suspect",
                confidence=confidence,
                supporting_evidence_ids=evidence_against,
                reasoning=f"Motive: {suspect.get('motive')}. Opportunity: {suspect.get('opportunity')}",
                alternative_explanations=evidence_for
            )
            
            # Add confidence analysis
            report.add_confidence_analysis(
                finding=f"Suspect confidence for {suspect.get('name')}",
                factors=factors if factors else {"general": 1.0},
                overall_confidence=confidence,
                caveats=["Based on available evidence", "Subject to further investigation"]
            )
    
    def _explain_summary(self, summary_data: Dict, report: ExplainabilityReport) -> None:
        """Generate explainability for summary stage."""
        # Add key facts
        for fact in summary_data.get("key_facts", []):
            report.add_claim(
                claim=fact,
                confidence=75,
                supporting_evidence_ids=[],
                reasoning="Extracted from evidence"
            )
        
        # Note gaps
        for gap in summary_data.get("gaps", []):
            report.add_claim(
                claim=f"Unknown: {gap}",
                confidence=0,
                supporting_evidence_ids=[],
                reasoning="Information not present in current evidence"
            )
    
    def _explain_validation(self, validation_data: Dict, report: ExplainabilityReport) -> None:
        """Generate explainability for validation stage."""
        for fact in validation_data.get("validated_facts", []):
            report.add_claim(
                claim=fact,
                confidence=90,
                supporting_evidence_ids=[],
                reasoning="Confirmed by validation stage"
            )
        
        for uncertain in validation_data.get("uncertain_claims", []):
            claim_text = uncertain.get("claim", "Unknown claim")
            issue = uncertain.get("issue", "")
            conf = 50 if uncertain.get("confidence") == "medium" else 30
            
            report.add_claim(
                claim=claim_text,
                confidence=conf,
                supporting_evidence_ids=[],
                reasoning=f"Issue: {issue}"
            )
    
    def get_report(self, stage: str) -> Optional[Dict[str, Any]]:
        """Get explainability report for a specific stage."""
        if stage in self.reports:
            return self.reports[stage].to_dict()
        return None
    
    def get_full_dashboard(self) -> Dict[str, Any]:
        """Get full dashboard with all stages and explainability."""
        return {
            "case_id": self.case_id,
            "investigation_overview": self.results,
            "explainability_reports": {
                stage: report.to_dict()
                for stage, report in self.reports.items()
            },
            "evidence_impact_analysis": self._analyze_evidence_impact(),
            "recommendation_summary": self._generate_recommendations()
        }
    
    def _analyze_evidence_impact(self) -> Dict[str, Any]:
        """Analyze which evidence items had the most impact."""
        impact = {}
        
        for stage, report in self.reports.items():
            for evidence_id, citations in report.evidence_citations.items():
                if evidence_id not in impact:
                    impact[evidence_id] = {
                        "citation_count": 0,
                        "supporting_claims": [],
                        "stages": []
                    }
                impact[evidence_id]["citation_count"] += len(citations)
                impact[evidence_id]["supporting_claims"].extend(citations)
                impact[evidence_id]["stages"].append(stage)
        
        # Rank by impact
        ranked = sorted(
            impact.items(),
            key=lambda x: x[1]["citation_count"],
            reverse=True
        )
        
        return {
            "total_unique_evidence": len(impact),
            "evidence_ranking": [
                {
                    "evidence_id": eid,
                    "impact_score": data["citation_count"],
                    "stages_used_in": data["stages"],
                    "claim_count": len(data["supporting_claims"])
                }
                for eid, data in ranked
            ]
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on investigation."""
        recommendations = []
        
        # Check if evidence is insufficient
        evidence_impact = self._analyze_evidence_impact()
        if evidence_impact["total_unique_evidence"] < 3:
            recommendations.append("Recommend collecting additional evidence for stronger case")
        
        # Check for validation issues
        if "validation" in self.reports:
            validation = self.reports["validation"].to_dict()
            if validation["summary"]["total_claims"] > 0:
                avg_conf = validation["summary"]["average_confidence"]
                if avg_conf < 60:
                    recommendations.append("Low confidence findings — recommend further investigation before prosecution")
        
        # Check for suspect confidence
        if "suspects" in self.reports:
            suspects = self.reports["suspects"].to_dict()
            if suspects["summary"]["total_claims"] > 0:
                avg_conf = suspects["summary"]["average_confidence"]
                if avg_conf > 80:
                    recommendations.append("Strong suspect identification — ready for arrest consideration")
        
        if not recommendations:
            recommendations.append("Investigation shows sufficient evidence for next phase")
        
        return recommendations
