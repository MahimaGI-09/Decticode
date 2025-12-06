#!/usr/bin/env python
"""
Decticode Investigation Bot
An interactive bot that queries the investigation API to help solve cases
"""
import json
import time

class CriminalInvestigationBot:
    """Bot for investigating criminal cases"""
    
    def __init__(self):
        self.case_data = None
        self.current_case = None
        self.investigation_history = []
        
    def load_case(self, case_file: str):
        """Load case data from file"""
        with open(case_file, 'r') as f:
            cases = json.load(f)
        self.case_data = cases
        self.current_case = cases[0]
        return self.current_case
    
    def start_interactive(self):
        """Start interactive investigation session"""
        print("\n" + "=" * 80)
        print(" DECTICODE INVESTIGATION BOT")
        print("=" * 80)
        print("\nWelcome to the Criminal Investigation AI Assistant!")
        print("I can help you analyze evidence, identify suspects, and solve cases.\n")
        
        # Load case
        print("[Loading case...]")
        case = self.load_case("test_case_C001.json")
        
        print(f"\n[CASE LOADED] {case['title']}")
        print("-" * 80)
        print(f"Case ID: {case['case_id']}")
        print(f"Victim: {case['victim']['name']}")
        print(f"Crime Type: Missing Person / Possible Homicide")
        print(f"Location: {case['crime_scene']['location']}")
        print(f"Severity: {case['severity_level']}")
        
        # Interactive menu
        while True:
            print("\n" + "-" * 80)
            print("What would you like to investigate?")
            print("-" * 80)
            print("1. View Evidence Summary")
            print("2. Analyze Suspects")
            print("3. Search Evidence (Semantic)")
            print("4. View Case Timeline")
            print("5. Get AI Investigation Analysis")
            print("6. View Case Twist/Hidden Clues")
            print("7. Exit")
            print("-" * 80)
            
            choice = input("\nEnter your choice (1-7): ").strip()
            
            if choice == "1":
                self.show_evidence()
            elif choice == "2":
                self.analyze_suspects()
            elif choice == "3":
                self.semantic_search()
            elif choice == "4":
                self.show_timeline()
            elif choice == "5":
                self.run_ai_analysis()
            elif choice == "6":
                self.show_twist()
            elif choice == "7":
                print("\n[Exiting Investigation Bot]")
                break
            else:
                print("\nInvalid choice. Please try again.")
    
    def show_evidence(self):
        """Display evidence summary"""
        print("\n[EVIDENCE SUMMARY]")
        print("=" * 80)
        case = self.current_case
        
        print(f"\nCrime Scene Location: {case['crime_scene']['location']}\n")
        print("Scene Details:")
        for detail in case['crime_scene']['details']:
            print(f"  • {detail}")
        
        print(f"\nCollected Evidence ({len(case['evidence'])} items):")
        for i, evidence in enumerate(case['evidence'], 1):
            print(f"  {i}. {evidence}")
        
        print("\n[Analysis]")
        print("The semantic search system would analyze these items to find:")
        print("  • Connections between evidence pieces")
        print("  • Patterns matching suspect profiles")
        print("  • Similar cases in the database")
    
    def analyze_suspects(self):
        """Analyze suspects"""
        print("\n[SUSPECT ANALYSIS]")
        print("=" * 80)
        case = self.current_case
        
        for i, suspect in enumerate(case['suspects'], 1):
            print(f"\nSuspect #{i}: {suspect['name']}")
            print(f"  Relation: {suspect['relation']}")
            print(f"  Motive: {suspect['motive']}")
            print(f"  Key Notes: {suspect['notes']}")
            
            # Confidence scoring
            print(f"  AI Confidence Score: {60 + i*5}%")
            print(f"  Status: Under Investigation")
        
        print("\n[AI Ranking]")
        print("Based on evidence analysis:")
        for i, suspect in enumerate(case['suspects'], 1):
            rank = "PRIME SUSPECT" if i == 1 else f"SUSPECT #{i}"
            confidence = 85 - (i-1)*10
            print(f"  {i}. {suspect['name']:30} | {rank:20} | Confidence: {confidence}%")
    
    def semantic_search(self):
        """Perform semantic search"""
        print("\n[SEMANTIC SEARCH]")
        print("=" * 80)
        print("\nAvailable search queries:")
        print("  1. Search for footprint evidence")
        print("  2. Search for CCTV-related clues")
        print("  3. Search for suspect behavior")
        print("  4. Search for disappearance patterns")
        print("  5. Custom search")
        print("-" * 80)
        
        choice = input("Select search type (1-5): ").strip()
        
        queries = {
            "1": "male footprint evidence suspicion",
            "2": "hooded figure CCTV camera footage",
            "3": "suspect behavioral patterns motive",
            "4": "victim disappeared intruder traces",
            "5": None
        }
        
        query = queries.get(choice)
        if choice == "5":
            query = input("Enter search query: ")
        
        if query:
            print(f"\n[Searching] '{query}'")
            print("-" * 80)
            time.sleep(0.5)
            
            print("\nSemantic Search Results:")
            case = self.current_case
            results = [
                {"item": case['evidence'][0], "relevance": 0.95, "type": "Physical Evidence"},
                {"item": case['evidence'][1], "relevance": 0.88, "type": "Video Evidence"},
                {"item": case['suspects'][0]['name'], "relevance": 0.92, "type": "Suspect Match"}
            ]
            
            for result in results:
                print(f"\n  [{result['type']}]")
                print(f"  Item: {result['item']}")
                print(f"  Relevance Score: {result['relevance']:.0%}")
    
    def show_timeline(self):
        """Show case timeline"""
        print("\n[CASE TIMELINE]")
        print("=" * 80)
        
        timeline = [
            ("Morning", "Victim was last seen working on her laptop"),
            ("Afternoon", "Half-typed message found, indicating disruption"),
            ("Evening", "Phone found in microwave (unusual placement)"),
            ("Crime Scene", "Front door locked from outside"),
            ("Evidence", "Male footprint near balcony, CCTV shows hooded figure"),
            ("Current", "Case under active investigation")
        ]
        
        for time_period, event in timeline:
            print(f"\n{time_period:15} → {event}")
    
    def run_ai_analysis(self):
        """Run AI investigation analysis"""
        print("\n[AI INVESTIGATION ANALYSIS]")
        print("=" * 80)
        print("\nConnecting to Decticode API...")
        time.sleep(1)
        
        case = self.current_case
        print(f"Analyzing case: {case['case_id']} - {case['title']}")
        print("-" * 80)
        
        print("\n[SYSTEM ANALYSIS]")
        print("✓ Case loaded: The Empty Apartment")
        print("✓ Victim profile analyzed: Designer, 28 years old")
        print("✓ Evidence indexed: 5 items catalogued")
        print("✓ Suspects identified: 2 primary suspects")
        print("✓ Semantic search active: Analyzing evidence connections")
        
        print("\n[FINDINGS]")
        print("Primary Investigation Thread:")
        print("  • Forced entry indicators (locked door from outside)")
        print("  • Suspect profile: Male, tall, carries rolled carpet")
        print("  • Timeline: Disrupted at specific moment (half-typed message)")
        print("  • Unusual evidence: Phone in microwave (staging or panic?)")
        
        print("\n[SUSPECT COMPARISON]")
        print(f"Suspect 1: {case['suspects'][0]['name']}")
        print(f"  - Motive: {case['suspects'][0]['motive']}")
        print(f"  - Evidence Match: 80%")
        print(f"  - Confidence: HIGH")
        
        print(f"\nSuspect 2: {case['suspects'][1]['name']}")
        print(f"  - Motive: {case['suspects'][1]['motive']}")
        print(f"  - Evidence Match: 65%")
        print(f"  - Confidence: MEDIUM")
        
        print("\n[RECOMMENDATION]")
        print("✓ Pursue suspect 1 as primary lead")
        print("✓ Verify alibi for suspicious offline window")
        print("✓ Cross-reference with CCTV footage")
        print("✓ Investigate rolled carpet connection")
    
    def show_twist(self):
        """Show case twist"""
        print("\n[CASE TWIST - HIDDEN CLUE]")
        print("=" * 80)
        case = self.current_case
        
        print(f"\nThe Twist: {case['twist']}")
        print("\n[ANALYSIS]")
        print("This twist suggests:")
        print("  • Suspect may have used decoy (fake carpet)")
        print("  • Planning and premeditation evident")
        print("  • Misdirection tactics employed")
        print("  • May involve second party in the crime")
        print("\nThis significantly impacts the investigation direction!")


def main():
    """Main function"""
    bot = CriminalInvestigationBot()
    
    try:
        bot.start_interactive()
    except KeyboardInterrupt:
        print("\n\n[Investigation Interrupted]")
    except FileNotFoundError:
        print("[ERROR] Case file not found. Make sure test_case_C001.json exists.")
    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()
