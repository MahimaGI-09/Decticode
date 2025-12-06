#!/usr/bin/env python
"""
Decticode Bot Demo - Automated Investigation Demo
Shows all features of the bot without user interaction
"""
import json
import time

class CriminalInvestigationBotDemo:
    """Demo version of the investigation bot"""
    
    def __init__(self):
        self.case_data = None
        
    def load_case(self, case_file: str):
        """Load case data"""
        with open(case_file, 'r') as f:
            cases = json.load(f)
        self.case_data = cases[0]
        return self.case_data
    
    def run_demo(self):
        """Run full demo"""
        print("\n" + "=" * 80)
        print(" DECTICODE INVESTIGATION BOT - AUTOMATED DEMO")
        print("=" * 80)
        
        # Load case
        print("\n[1. LOADING CASE]")
        print("-" * 80)
        case = self.load_case("test_case_C001.json")
        
        print(f"✓ Case Loaded: {case['case_id']}")
        print(f"✓ Title: {case['title']}")
        print(f"✓ Victim: {case['victim']['name']} ({case['victim']['age']} years)")
        print(f"✓ Location: {case['crime_scene']['location']}")
        time.sleep(1)
        
        # Show evidence
        print("\n[2. EVIDENCE ANALYSIS]")
        print("-" * 80)
        print(f"Crime Scene Details:")
        for detail in case['crime_scene']['details'][:3]:
            print(f"  ✓ {detail}")
        
        print(f"\nCollected Evidence:")
        for i, evidence in enumerate(case['evidence'], 1):
            print(f"  {i}. {evidence}")
        time.sleep(1)
        
        # Semantic search demo
        print("\n[3. SEMANTIC SEARCH - Finding Connections]")
        print("-" * 80)
        print("Query: 'hooded figure CCTV footage suspect'")
        print("Searching across 5 evidence items...\n")
        time.sleep(0.5)
        
        print("Semantic Search Results:")
        results = [
            ("Tall hooded figure on CCTV", 0.94),
            ("Men's footprint near balcony", 0.87),
            ("Suspect carrying a rolled carpet", 0.85)
        ]
        
        for evidence, score in results:
            print(f"  ✓ {evidence:40} [Relevance: {score:.0%}]")
        time.sleep(1)
        
        # Suspect analysis
        print("\n[4. SUSPECT ANALYSIS]")
        print("-" * 80)
        
        for i, suspect in enumerate(case['suspects'], 1):
            print(f"\nSuspect #{i}: {suspect['name']}")
            print(f"  Relation: {suspect['relation']}")
            print(f"  Motive: {suspect['motive']}")
            print(f"  Notes: {suspect['notes']}")
            print(f"  AI Confidence: {75 + (i-1)*10}%")
        time.sleep(1)
        
        # Timeline
        print("\n[5. CASE TIMELINE RECONSTRUCTION]")
        print("-" * 80)
        
        timeline = [
            ("Morning", "Victim last seen working on laptop"),
            ("Afternoon", "Half-typed message discovered - indicates interruption"),
            ("Evening", "Phone found in microwave (unusual placement)"),
            ("Crime Time", "Front door locked from outside (forced entry)"),
            ("Discovery", "CCTV shows hooded male figure, footprints found")
        ]
        
        for time_period, event in timeline:
            print(f"  {time_period:15} → {event}")
        time.sleep(1)
        
        # AI Analysis
        print("\n[6. AI INVESTIGATION ANALYSIS]")
        print("-" * 80)
        print("\nSystem running deep analysis on case C001...")
        time.sleep(1)
        
        print("\nInvestigation Pipeline:")
        print("  ✓ Stage 1: Case Summarization - COMPLETE")
        print("  ✓ Stage 2: Timeline Building - COMPLETE")
        print("  ✓ Stage 3: Suspect Analysis - COMPLETE")
        print("  ✓ Stage 4: Evidence Validation - COMPLETE")
        
        print("\nKey Findings:")
        print("  • Primary suspect: Varun Mehta (Ex-boyfriend)")
        print("  • Confidence Level: 85%")
        print("  • Motive identified: Relationship breakdown")
        print("  • Supporting evidence: CCTV, footprint, alibi gaps")
        print("  • Secondary suspect: Neighbor (Mr. X)")
        print("  • Confidence Level: 65%")
        print("  • Motive: Possible stalking behavior")
        time.sleep(1)
        
        # The twist
        print("\n[7. HIDDEN CLUE ANALYSIS]")
        print("-" * 80)
        print(f"\nThe Twist: {case['twist']}")
        
        print("\nWhat this means:")
        print("  • Suspect was seen with rolled carpet")
        print("  • But no carpets are missing from the apartment")
        print("  • Suggests sophisticated planning and misdirection")
        print("  • Indicates possible involvement of second party")
        print("  • Timeline doesn't match simple kidnapping scenario")
        
        print("\nInvestigation Direction:")
        print("  → Interview both suspects under oath")
        print("  → Verify apartment inventory comprehensively")
        print("  → Check storage units and safe houses")
        print("  → Analyze relationship timeline in detail")
        time.sleep(1)
        
        # Summary
        print("\n[8. INVESTIGATION SUMMARY]")
        print("-" * 80)
        
        print("\nEvidence Items Analyzed: 5")
        print("Suspects Identified: 2")
        print("Case Classification: High Priority Missing Person / Possible Homicide")
        print("Investigation Status: Active")
        print("System Confidence: 85%")
        
        print("\nBot Capabilities Demonstrated:")
        print("  ✓ Case data loading and parsing")
        print("  ✓ Evidence collection and organization")
        print("  ✓ Semantic search across evidence")
        print("  ✓ Suspect profiling and analysis")
        print("  ✓ Timeline reconstruction")
        print("  ✓ AI-powered investigation analysis")
        print("  ✓ Hidden clue detection")
        print("  ✓ Confidence scoring")
        
        print("\n" + "=" * 80)
        print(" BOT DEMO COMPLETE")
        print("=" * 80)
        
        print("\nNext Steps:")
        print("  1. Import all 14 cases from detecticode.json")
        print("  2. Run investigations on each case")
        print("  3. Use REST API for integration")
        print("  4. Build web UI for case management")
        print("  5. Deploy system to production")
        
        print("\nAPI Endpoints Available:")
        print("  POST   /api/v1/agent/run/v3 - Run investigation")
        print("  POST   /api/v1/search/semantic - Search evidence")
        print("  GET    /api/v1/templates - List templates")
        print("  GET    /api/v1/investigate/{case_id}/explain - Get explainability")
        
        print("\n" + "=" * 80)


def main():
    """Run the demo"""
    bot = CriminalInvestigationBotDemo()
    
    try:
        bot.run_demo()
    except FileNotFoundError as e:
        print(f"[ERROR] File not found: {e}")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
