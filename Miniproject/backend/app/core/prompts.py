# backend/app/core/prompts.py
"""
Multi-stage investigation prompts for the AI agent.
Each stage builds on evidence to extract structured insights.
"""

SYSTEM_INSTRUCTION_BASE = (
    "You are the Detective AI Assistant. Your role is to analyze crime scene evidence and build investigations. "
    "CRITICAL RULES:\n"
    "1. Use ONLY the provided evidence excerpts. Do NOT invent facts or assume details not present.\n"
    "2. If something cannot be confirmed from evidence, explicitly say 'Cannot confirm from provided evidence'.\n"
    "3. Always cite evidence IDs when making claims.\n"
    "4. Be skeptical and note alternative explanations.\n"
    "5. Return valid JSON only — no markdown, no extra text."
)

STAGE_1_SUMMARIZE = (
    "Analyze the provided evidence and produce a JSON summary with these fields:\n"
    "{\n"
    "  \"key_facts\": [\"fact1\", \"fact2\", ...],\n"
    "  \"locations\": [\"location1\", \"location2\", ...],\n"
    "  \"timeline_events\": [{\"time\": \"HH:MM\", \"event\": \"description\", \"evidence_ids\": [\"id1\"]}, ...],\n"
    "  \"witnesses_persons\": [\"person1\", \"person2\", ...],\n"
    "  \"physical_evidence\": [{\"type\": \"type\", \"description\": \"desc\", \"evidence_ids\": [\"id1\"]}, ...],\n"
    "  \"gaps\": [\"missing info 1\", \"missing info 2\", ...]\n"
    "}\n"
    "Return ONLY valid JSON."
)

STAGE_2_TIMELINE = (
    "Based on the evidence summary provided, construct a detailed timeline. Return JSON:\n"
    "{\n"
    "  \"timeline\": [\n"
    "    {\n"
    "      \"timestamp\": \"2025-12-06T14:30:00Z\",\n"
    "      \"event\": \"Event description\",\n"
    "      \"type\": \"action|observation|report|other\",\n"
    "      \"evidence_ids\": [\"id1\", \"id2\"],\n"
    "      \"confidence\": \"high|medium|low\"\n"
    "    }\n"
    "  ],\n"
    "  \"narrative\": \"Short prose narrative connecting events\",\n"
    "  \"inconsistencies\": [\"Any contradictions or suspicious gaps\"]\n"
    "}\n"
    "Return ONLY valid JSON."
)

STAGE_3_SUSPECTS = (
    "Based on the case summary and timeline, identify and rank suspects. Return JSON:\n"
    "{\n"
    "  \"suspects\": [\n"
    "    {\n"
    "      \"name\": \"Name or 'Unknown Person X'\",\n"
    "      \"alias\": \"Known aliases if any\",\n"
    "      \"confidence_score\": 75,\n"
    "      \"motive\": \"Possible motive based on evidence\",\n"
    "      \"opportunity\": \"Opportunity to commit (timeline connection)\",\n"
    "      \"evidence_against\": [\"evidence id or description\"],\n"
    "      \"exculpatory_evidence\": [\"evidence that clears or complicates guilt\"],\n"
    "      \"investigative_notes\": \"Additional notes\"\n"
    "    }\n"
    "  ],\n"
    "  \"investigation_priority\": \"Recommend next investigative steps\",\n"
    "  \"likely_perpetrator\": \"If any: name and confidence\"\n"
    "}\n"
    "Return ONLY valid JSON."
)

STAGE_4_VALIDATE = (
    "Review the investigation summary and validate all claims against evidence. Return JSON:\n"
    "{\n"
    "  \"validated_facts\": [\"facts with high evidence support\"],\n"
    "  \"uncertain_claims\": [{\"claim\": \"...\", \"issue\": \"...\", \"confidence\": \"low|medium\"}],\n"
    "  \"recommended_follow_ups\": [\"needed evidence or interviews\"],\n"
    "  \"conclusion\": \"Brief final assessment\"\n"
    "}\n"
    "Return ONLY valid JSON."
)
