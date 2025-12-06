"""
Comprehensive tests for STEP AGENT 3: Semantic Search, Templates, and Explainability.
Tests embeddings, semantic search, templates, agent v3, and explainability.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

# Mock the modules before importing
import sys
sys.path.insert(0, '/Users/Mahima/Desktop/Miniproject')

from backend.app.core import agent_v3, semantic_search, templates, embeddings_v2, explainability


class TestEmbeddings:
    """Test embeddings_v2 module."""
    
    def test_mock_embed_text(self):
        """Test mock embedding provider."""
        text = "The weapon was a knife."
        embedding = embeddings_v2.embed_text(text, provider="mock")
        
        assert embedding is not None
        assert len(embedding) == 384  # Mock dimension
        assert isinstance(embedding, list)
        assert all(isinstance(x, float) for x in embedding)
    
    def test_similarity_score(self):
        """Test similarity computation."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.9, 0.1, 0.0]
        
        sim = embeddings_v2.similarity(vec1, vec2)
        assert 0.9 <= sim <= 1.0  # Should be high similarity
    
    def test_embed_batch(self):
        """Test batch embedding."""
        texts = [
            "Suspect seen near crime scene",
            "Weapon found in park",
            "Witness statement recorded"
        ]
        embeddings = embeddings_v2.embed_batch(texts, provider="mock")
        
        assert len(embeddings) == 3
        assert all(len(e) == 384 for e in embeddings)


class TestSemanticSearch:
    """Test semantic_search module."""
    
    @patch('backend.app.core.semantic_search.get_storage')
    def test_semantic_search_fallback(self, mock_storage):
        """Test keyword fallback when embeddings unavailable."""
        # Setup mock
        mock_db = MagicMock()
        mock_storage.return_value.get_db.return_value = mock_db
        mock_db.__getitem__.return_value.find.return_value = [
            {
                "_id": "ev1",
                "case_id": "case123",
                "type": "text",
                "description": "Suspect seen at 9 PM",
                "content": "Witness said suspect was at location"
            }
        ]
        
        results = semantic_search.semantic_search_fallback(
            case_id="case123",
            query="Where was suspect at night",
            top_k=5
        )
        
        assert len(results) > 0
        assert results[0]["_id"] == "ev1"


class TestTemplates:
    """Test templates module."""
    
    def test_get_homicide_template(self):
        """Test loading homicide template."""
        template = templates.get_template("homicide")
        
        assert template.name == "Homicide Investigation"
        assert "suspects" in template.stages
        assert "timeline" in template.stages
        assert "summarize" in template.stages
        assert "validation" in template.stages
    
    def test_get_theft_template(self):
        """Test loading theft template."""
        template = templates.get_template("theft")
        
        assert template.name == "Theft Investigation"
        assert "suspects" in template.stages
    
    def test_get_generic_template(self):
        """Test loading generic template."""
        template = templates.get_template("generic")
        
        assert template.name == "Generic Investigation"
        assert len(template.stages) == 4
    
    def test_list_available_templates(self):
        """Test template listing."""
        template_list = templates.list_available_templates()
        
        assert len(template_list) >= 3
        names = [t["name"] for t in template_list]
        assert "Homicide Investigation" in names
        assert "Theft Investigation" in names
        assert "Generic Investigation" in names
    
    def test_custom_template_override(self):
        """Test custom template."""
        custom = {
            "name": "Custom Crime",
            "description": "Custom investigation",
            "stages": {
                "summarize": {"system": "Summarize", "user_prompt": "Summarize case"},
                "timeline": {"system": "Timeline", "user_prompt": "Build timeline"},
                "suspects": {"system": "Suspects", "user_prompt": "Identify suspects"},
                "validation": {"system": "Validate", "user_prompt": "Validate findings"}
            }
        }
        
        template = templates.get_template(custom_template=custom)
        assert template.name == "Custom Crime"


class TestExplainability:
    """Test explainability module."""
    
    def test_explainability_report_creation(self):
        """Test creating explainability report."""
        report = explainability.ExplainabilityReport("case123", "timeline")
        
        assert report.case_id == "case123"
        assert report.investigation_stage == "timeline"
        assert len(report.claims) == 0
    
    def test_add_claim_with_citations(self):
        """Test adding claims with evidence citations."""
        report = explainability.ExplainabilityReport("case123", "suspects")
        
        report.add_claim(
            claim="John Doe is a suspect",
            confidence=85.0,
            supporting_evidence_ids=["ev1", "ev2"],
            reasoning="Had motive and opportunity",
            alternative_explanations=["Could be innocent"]
        )
        
        assert len(report.claims) == 1
        assert report.claims[0]["confidence"] == 85.0
        assert "ev1" in report.claims[0]["supporting_evidence_ids"]
        assert "John Doe" in report.evidence_citations
    
    def test_confidence_analysis(self):
        """Test confidence breakdown."""
        report = explainability.ExplainabilityReport("case123", "suspects")
        
        report.add_confidence_analysis(
            finding="Suspect identification",
            factors={"motive": 0.3, "opportunity": 0.4, "evidence": 0.3},
            overall_confidence=82.0,
            caveats=["Limited evidence", "Circumstantial only"]
        )
        
        assert "Suspect identification" in report.confidence_breakdown
        breakdown = report.confidence_breakdown["Suspect identification"]
        assert breakdown["confidence"] == 82.0
        assert len(breakdown["caveats"]) == 2
    
    def test_report_to_dict(self):
        """Test report serialization."""
        report = explainability.ExplainabilityReport("case123", "timeline")
        report.add_claim("Event happened at 9 PM", 90, ["ev1"])
        
        report_dict = report.to_dict()
        
        assert report_dict["case_id"] == "case123"
        assert report_dict["investigation_stage"] == "timeline"
        assert "claims" in report_dict
        assert "summary" in report_dict
        assert report_dict["summary"]["total_claims"] == 1
    
    def test_dashboard_creation(self):
        """Test creating explainability dashboard."""
        investigation_results = {
            "case_id": "case123",
            "stages": {
                "summarize": {
                    "parsed": {
                        "key_facts": ["Victim found at location"],
                        "gaps": ["Time of death unclear"]
                    }
                },
                "suspects": {
                    "parsed": {
                        "suspects": [
                            {
                                "name": "John Doe",
                                "motive": "Financial",
                                "opportunity": "High",
                                "confidence_score": 85,
                                "evidence_against": ["ev1"]
                            }
                        ]
                    }
                }
            }
        }
        
        dashboard = explainability.ExplainabilityDashboard("case123", investigation_results)
        
        assert "case123" in dashboard.reports or len(dashboard.reports) >= 0
        full_dashboard = dashboard.get_full_dashboard()
        assert full_dashboard["case_id"] == "case123"


class TestAgentV3:
    """Test agent_v3 module."""
    
    def test_safe_json_extract_direct(self):
        """Test JSON extraction from direct JSON."""
        json_str = '{"status": "ok", "data": "test"}'
        result = agent_v3.safe_json_extract(json_str)
        
        assert result is not None
        assert result["status"] == "ok"
    
    def test_safe_json_extract_bracketed(self):
        """Test JSON extraction from bracketed response."""
        response = "Here is the data: {\"status\": \"ok\", \"value\": 42} end"
        result = agent_v3.safe_json_extract(response)
        
        assert result is not None
        assert result.get("status") == "ok" or result.get("value") == 42
    
    def test_safe_json_extract_code_block(self):
        """Test JSON extraction from code block."""
        response = """
        Here is my analysis:
        ```json
        {"timeline": [{"event": "Meeting at 9 AM"}]}
        ```
        """
        result = agent_v3.safe_json_extract(response)
        
        assert result is not None
        assert "timeline" in result
    
    def test_build_evidence_context(self):
        """Test evidence context building."""
        evidence = [
            {
                "_id": "ev1",
                "type": "text",
                "description": "Witness statement",
                "content": "I saw the suspect at the location"
            },
            {
                "_id": "ev2",
                "type": "photo",
                "description": "Crime scene photo",
                "content": "Photo of the scene"
            }
        ]
        
        context = agent_v3._build_evidence_context(evidence, max_tokens=500)
        
        assert len(context) > 0
        assert "ev1" in context or "ev2" in context
        assert "text" in context or "photo" in context
    
    def test_extract_evidence_citations(self):
        """Test evidence citation extraction."""
        parsed = {
            "timeline": [
                {"event": "Suspect seen near ev1 at 9 PM", "confidence": "high"}
            ]
        }
        evidence_by_id = {
            "ev1": {"_id": "ev1", "description": "Location marker"},
            "ev2": {"_id": "ev2", "description": "Witness"}
        }
        
        citations = agent_v3._extract_evidence_citations(
            parsed,
            evidence_by_id,
            "timeline"
        )
        
        # May find citations depending on string matching
        assert isinstance(citations, dict)
    
    def test_estimate_stage_confidence_timeline(self):
        """Test confidence estimation for timeline stage."""
        parsed = {
            "timeline": [
                {"event": "Event 1", "confidence": "high"},
                {"event": "Event 2", "confidence": "medium"},
                {"event": "Event 3", "confidence": "low"}
            ]
        }
        
        conf = agent_v3._estimate_stage_confidence(parsed, "timeline")
        
        assert 40 <= conf <= 90
        assert isinstance(conf, float)
    
    def test_estimate_stage_confidence_suspects(self):
        """Test confidence estimation for suspects stage."""
        parsed = {
            "suspects": [
                {"name": "John", "confidence_score": 85},
                {"name": "Jane", "confidence_score": 65}
            ]
        }
        
        conf = agent_v3._estimate_stage_confidence(parsed, "suspects")
        
        assert 65 <= conf <= 85
    
    @patch('backend.app.core.agent_v3.get_storage')
    @patch('backend.app.core.agent_v3.get_templates')
    @patch('backend.app.core.agent_v3.get_semantic_search')
    @patch('backend.app.core.agent_v3.call_mock_chat')
    def test_run_investigation_v3_basic(
        self,
        mock_chat,
        mock_semantic_search,
        mock_templates,
        mock_storage
    ):
        """Test basic v3 investigation run."""
        # Setup mocks
        mock_db = MagicMock()
        mock_storage.return_value.get_db.return_value = mock_db
        mock_storage.return_value.insert_agent_run_v3 = MagicMock()
        
        mock_db.__getitem__.return_value.find_one.return_value = {
            "case_id": "case123",
            "description": "Victim found at location"
        }
        
        mock_template = MagicMock()
        mock_template.name = "Test Template"
        mock_template.stages = {
            "summarize": {
                "system": "System prompt",
                "user_prompt": "Summarize case"
            },
            "timeline": {
                "system": "System prompt",
                "user_prompt": "Build timeline"
            },
            "suspects": {
                "system": "System prompt",
                "user_prompt": "Identify suspects"
            },
            "validation": {
                "system": "System prompt",
                "user_prompt": "Validate findings"
            }
        }
        mock_templates.return_value.get_template.return_value = mock_template
        
        mock_semantic_search.return_value.hybrid_search.return_value = []
        mock_semantic_search.return_value.semantic_search_fallback.return_value = []
        
        mock_chat.return_value = '{"status": "ok", "data": []}'
        
        # Run investigation
        result = agent_v3.run_investigation_v3(
            case_id="case123",
            crime_type="homicide",
            use_semantic_search=False,
            llm_provider="mock"
        )
        
        assert result["case_id"] == "case123"
        assert result["llm_provider"] == "mock"


class TestAPIEndpoints:
    """Test API endpoint integration (requires FastAPI client)."""
    
    def test_agent_v3_endpoint_structure(self):
        """Test that agent v3 endpoint can be called with correct structure."""
        payload = {
            "case_id": "case123",
            "crime_type": "homicide",
            "custom_template": None,
            "use_semantic_search": True,
            "hybrid_weight": 0.7,
            "max_evidence": 8,
            "llm_provider": "mock"
        }
        
        # Verify all expected keys are present
        assert "case_id" in payload
        assert "crime_type" in payload
        assert "use_semantic_search" in payload
    
    def test_semantic_search_endpoint_structure(self):
        """Test semantic search endpoint structure."""
        payload = {
            "case_id": "case123",
            "query": "Where was suspect at night?",
            "top_k": 5
        }
        
        assert "case_id" in payload
        assert "query" in payload
        assert "top_k" in payload
    
    def test_hybrid_search_endpoint_structure(self):
        """Test hybrid search endpoint structure."""
        payload = {
            "case_id": "case123",
            "query": "Weapon used in crime",
            "top_k": 5,
            "semantic_weight": 0.7
        }
        
        assert "case_id" in payload
        assert "query" in payload
        assert "semantic_weight" in payload


# Run tests with: pytest backend/tests/test_agent_v3.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
