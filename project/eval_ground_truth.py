import sys
from dotenv import load_dotenv
from src.orchestration.router.model_router import ModelRouter
from src.storage.db import StorageManager, Evidence
from src.intelligence.extraction.pain_extractor import PainExtractor

# Ensure UTF-8 output and load API keys
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

def run_ground_truth_eval():
    print("=== RUNNING GROUND TRUTH EVALUATION ===")
    
    # 1. Initialize our intelligent router
    router = ModelRouter()
    
    # 2. Hardcode a realistic "Ground Truth" Reddit post
    # We KNOW the pain point here is "Restaurant inventory sync is manual and slow"
    raw_text = """
    Title: I am losing my mind trying to manage inventory across our 3 locations.
    
    We use Toast for POS, but their inventory module is so clunky for tracking raw ingredients. 
    I end up exporting everything to Excel, manually counting onions and flour every Sunday night, 
    and emailing a spreadsheet to my manager. I spend like 6 hours a week just doing data entry. 
    Why isn't there a simple app where my kitchen staff can just tap a button on an iPad 
    when they open a new bag of flour, and it auto-syncs?
    """
    
    mock_evidence = Evidence(
        id="gt_test_001",
        source="reddit",
        source_id="mock123",
        url="https://reddit.com/r/restaurantowners/comments/mock123",
        timestamp="2026-09-26T00:00:00",
        author="angry_chef",
        text=raw_text.strip(),
        metadata={}
    )
    
    print("\n[Input] Raw Evidence Text:")
    print(mock_evidence.text)
    
    # 3. Run it through the PainExtractor (Phase 3.5)
    print("\n[Processing] Running ModelRouter Extraction (System 1)...")
    extractor = PainExtractor(router=router)
    
    # We pass it to the extractor (which will hit Groq/Gemini Flash via the ModelRouter)
    pain_points = extractor.process_evidence([mock_evidence])
    
    # 4. Evaluate the Output
    print("\n=== EVALUATION RESULT ===")
    if not pain_points:
        print("[FAIL] The AI failed to extract a pain point from this text.")
    else:
        pp = pain_points[0]
        print("[SUCCESS] The AI extracted a Pain Point!")
        print(f"Problem:       {pp.problem}")
        print(f"Affected User: {pp.affected_user}")
        print(f"Category:      {pp.category}")
        print(f"Severity:      {pp.severity}/10")
        print(f"Workaround:    {pp.workaround}")
        
        # Simple manual assertion
        if "inventory" in pp.problem.lower() or "excel" in pp.workaround.lower():
            print("\n✅ Ground Truth Match: The AI correctly identified the inventory/sync issue.")
        else:
            print("\n❌ Ground Truth Miss: The AI extracted something, but it missed the core inventory issue.")

if __name__ == "__main__":
    run_ground_truth_eval()
