import json
import os
import re
import csv
import sys
from datetime import datetime
from typing import List, Dict, Any, TypedDict
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Taxonomy Categories (STRICTLY IN ROMANIAN - 11 CATEGORIES)
CATEGORIES = [
    "Preparate la Grătar & Mici",
    "Cârnați & Platouri",
    "Mâncăruri Gătite & Specialități",
    "Ciorbe & Supe",
    "Aperitive & Gustări",
    "Garnituri",
    "Salate",
    "Desert",
    "Băuturi Alcoolice & Bere",
    "Băuturi Răcoritoare & Cafea",
    "Sosuri & Extra"
]

ITEM_TYPES = [
    "Mici", "Cârnați", "Friptură / Grătar", "Platou", "Ciorbă / Supă",
    "Aperitiv / Gustare", "Mâncare Gătită", "Garnitură", "Salată",
    "Desert", "Bere", "Vin / Alcool", "Răcoritoare / Cafea", "Sos / Extra"
]


class ClassifiedItem(BaseModel):
    restaurant_name: str = Field(description="Numele restaurantului")
    original_category: str = Field(description="Categoria originală de pe site")
    standard_category: str = Field(description="Categoria standardizată ALESĂ STRICT DIN LISTA ÎN LIMBA ROMÂNĂ")
    item_type: str = Field(description="Tipul produsului ALES STRICT ÎN ROMÂNĂ")
    item_name: str = Field(description="Denumirea curațată a preparatului")
    grammage: str = Field(description="Gramajul sau volumul extras sau dedus (ex: 200g, 400ml, 750ml, 330ml, 1 buc). Folosește g pentru masă solidă și ml pentru lichide. Fără kg sau L.")
    description: str = Field(default="", description="Descrierea preparatului")
    price_ron: float = Field(description="Prețul în RON")
    currency: str = Field(default="RON", description="Valuta")
    scraped_at: str = Field(description="Data colectării")


class RefinedGrammage(BaseModel):
    item_name: str
    inferred_grammage: str = Field(description="Gramajul sau porția standardizată dedusă de AI în g, ml sau buc (ex: 200g, 400ml, 750ml, 330ml, 50g, 1 buc)")


class GraphState(TypedDict):
    raw_items: List[Dict[str, Any]]
    classified_items: List[Dict[str, Any]]
    items_to_refine: List[Dict[str, Any]]
    retry_count: int
    stats: Dict[str, Any]


def normalize_grammage_string(gram: Any) -> str:
    if not gram or str(gram).strip().upper() in ["NONE", "NULL", "N/A", ""]:
        return "N/A"
    
    s = str(gram).strip()
    # Remove leading/trailing '+' or noise symbols
    s = re.sub(r'[\+\,\;\:]', ' ', s).strip()
    
    # 1. Convert kg to g (e.g. 5 kg -> 5000g, 7.4 kg -> 7400g)
    match_kg = re.search(r'(\d+(?:\.\d+)?)\s*kg\b', s, re.IGNORECASE)
    if match_kg:
        val = float(match_kg.group(1))
        return f"{int(val * 1000)}g"

    # 2. Convert liters L to ml (e.g. 0.33L -> 330ml, 0.5L -> 500ml, 0.75L -> 750ml)
    match_l = re.search(r'(\d+(?:\.\d+)?)\s*l\b', s, re.IGNORECASE)
    if match_l:
        val = float(match_l.group(1))
        if val <= 2.5:
            return f"{int(round(val * 1000))}ml"
        else:
            return f"{int(val * 1000)}ml"

    # 3. Clean gr -> g (e.g. 300gr -> 300g)
    match_gr = re.search(r'(\d+)\s*gr\b', s, re.IGNORECASE)
    if match_gr:
        return f"{match_gr.group(1)}g"

    # 4. Standard g (e.g. 200g, 400g)
    match_g = re.search(r'(\d+)\s*g\b', s, re.IGNORECASE)
    if match_g:
        return f"{match_g.group(1)}g"

    # 5. Standard ml (e.g. 400ml, 250ml)
    match_ml = re.search(r'(\d+)\s*ml\b', s, re.IGNORECASE)
    if match_ml:
        return f"{match_ml.group(1)}ml"

    # 6. Standard buc (e.g. 1 buc, 2 buc)
    match_buc = re.search(r'(\d+)\s*buc', s, re.IGNORECASE)
    if match_buc:
        return f"{match_buc.group(1)} buc"

    # Fallback clean string
    s_clean = re.sub(r'[^\w\.\s]', '', s).strip()
    return s_clean.upper() if s_clean else "N/A"


def extract_grammage_fallback(name: str, desc: str, raw_gram: str) -> str:
    if raw_gram and str(raw_gram).strip() and str(raw_gram).strip().upper() not in ["NONE", "NULL", "N/A"]:
        return normalize_grammage_string(raw_gram)
    
    combined = f"{name} {desc}"
    match = re.search(r'(\d+(?:\.\d+)?\s*(?:g|gr|kg|ml|l|cl|l|buc|bucati))\b', combined, re.IGNORECASE)
    if match:
        return normalize_grammage_string(match.group(1))
    
    return "N/A"


def classify_single_item_rulebased(item: Dict[str, Any]) -> Dict[str, Any]:
    orig_cat = (item.get("category") or "").strip()
    name = (item.get("item_name") or "").strip()
    desc = (item.get("description") or "").strip()
    price = float(item.get("price") or 0.0)
    raw_grammage = item.get("grammage")
    scraped_at = item.get("scraped_at") or datetime.now().isoformat()
    rest_name = item.get("restaurant_name") or "Competitor"

    grammage = extract_grammage_fallback(name, desc, str(raw_grammage or ""))

    name_lower = name.lower()
    cat_lower = orig_cat.lower()
    combined_text = f"{orig_cat} {name} {desc}".lower()

    # Default category & type in Romanian
    std_cat = "Mâncăruri Gătite & Specialități"
    item_type = "Mâncare Gătită"

    if re.search(r'\bmici\b|\bmititei\b|\bplescavita\b|\bceafa\b|\bpiept de pui\b|\bfrigaru\b|\bmuschi\b|\bsnitel\b|\bgratar\b', name_lower) or re.search(r'\bgratar\b', cat_lower):
        std_cat = "Preparate la Grătar & Mici"
        item_type = "Mici" if re.search(r'\bmici\b|\bmititei\b', name_lower) else "Friptură / Grătar"

    elif re.search(r'carnat|carna[tț]i|cârna[tț]i|kaesekrainer|thuringer|weisswurst', name_lower) or re.search(r'carnat', cat_lower):
        std_cat = "Cârnați & Platouri"
        item_type = "Cârnați"

    elif re.search(r'\bplatou\b|\bgloria berii\b|\bplatoul\b', name_lower) or re.search(r'\bplatou\b', cat_lower):
        std_cat = "Cârnați & Platouri"
        item_type = "Platou"

    elif re.search(r'\bciorba\b|\bsupa\b|\bborş\b|\bcrema de\b', name_lower) or re.search(r'\bciorba\b|\bsupa\b', cat_lower):
        std_cat = "Ciorbe & Supe"
        item_type = "Ciorbă / Supă"

    elif re.search(r'\baperitiv\b|\bzacusc\b|\bvinete\b|\bchiftelu\b|\bbulz\b|\bbranza\b|\bcașcaval\b', name_lower) or re.search(r'\baperitiv\b', cat_lower):
        std_cat = "Aperitive & Gustări"
        item_type = "Aperitiv / Gustare"

    elif re.search(r'\bgarnitur\b|\bcartof\b|\bpiure\b|\borez\b|\bmamaliga\b|\blegume la gratar\b', name_lower) or re.search(r'\bgarnitur\b|\bcartof\b', cat_lower):
        std_cat = "Garnituri"
        item_type = "Garnitură"

    elif re.search(r'\bsalat\b|\bardei cop\b|\bmuraturi\b|\bcoleslaw\b|\bvarza\b', name_lower) or re.search(r'\bsalat\b', cat_lower):
        std_cat = "Salate"
        item_type = "Salată"

    elif re.search(r'\bdesert\b|\bcake\b|\bclatite\b|\becler\b|\bpapanas\b|\bbrownie\b|\binghetat\b|\bstrudel\b', name_lower) or re.search(r'\bdesert\b', cat_lower):
        std_cat = "Desert"
        item_type = "Desert"

    elif re.search(r'\bsos\b|\bmustar\b|\bsmantana\b|\bmujdei\b|\bardei iute\b|\bketchup\b|\bmaionez\b|\btopping\b|\bpaine\b|\bcovrig\b', name_lower):
        std_cat = "Sosuri & Extra"
        item_type = "Sos / Extra"

    elif re.search(r'\bbere\b|\bwine\b|\bvin\b|\bwhiskey\b|\bvodka\b|\bgin\b|\btequila\b|\brom\b|\bcocktail\b|\bpalinca\b|\btuica\b|\bliqueur\b|\bbrandy\b|\bcognac\b|\baperitivo\b|\bciuc\b|\bursus\b|\bheineken\b|\bkozel\b|\bazuga\b', name_lower) or re.search(r'\bbere\b|\bbauturi\b|\balcohol\b|\bwine\b', cat_lower):
        std_cat = "Băuturi Alcoolice & Bere"
        item_type = "Bere" if re.search(r'\bbere\b|\bciuc\b|\bursus\b|\bheineken\b|\bkozel\b|\bazuga\b', combined_text) else "Vin / Alcool"

    elif re.search(r'\bapa\b|\bpepsi\b|\bcola\b|\bprigat\b|\b7up\b|\bmirinda\b|\bceai\b|\bcafea\b|\bespresso\b|\bcappuccino\b|\blatte\b|\blimonad\b|\bciocolata calda\b|\bsoft drinks\b', name_lower) or re.search(r'\bcafea\b|\bsoft drinks\b', cat_lower):
        std_cat = "Băuturi Răcoritoare & Cafea"
        item_type = "Răcoritoare / Cafea"

    classified = ClassifiedItem(
        restaurant_name=rest_name,
        original_category=orig_cat or "General",
        standard_category=std_cat,
        item_type=item_type,
        item_name=name,
        grammage=normalize_grammage_string(grammage),
        description=desc,
        price_ron=price,
        currency="RON",
        scraped_at=scraped_at
    )

    return classified.model_dump()


def get_llm_model():
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if gemini_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        print("Using Google Gemini API LLM for classification (gemini-1.5-flash)...")
        return ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=gemini_key)
    elif openai_key:
        from langchain_openai import ChatOpenAI
        print("Using OpenAI GPT-4o-mini LLM for classification...")
        return ChatOpenAI(model="gpt-4o-mini", api_key=openai_key)
    else:
        print("No GEMINI_API_KEY or OPENAI_API_KEY found in .env. Using Rule-Based NLP Classifier.")
        return None


# --- LangGraph Nodes ---

def ingest_node(state: GraphState) -> GraphState:
    input_path = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "competitors_scraped.json")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found at {input_path}")
    
    with open(input_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    print(f"Loaded {len(raw_data)} raw menu items from {input_path}")
    state["raw_items"] = raw_data
    state["classified_items"] = []
    state["items_to_refine"] = []
    state["retry_count"] = 0
    state["stats"] = {}
    return state


def classify_node(state: GraphState) -> GraphState:
    raw_items = state.get("raw_items", [])
    classified = []
    llm = get_llm_model()

    if llm:
        structured_llm = llm.with_structured_output(ClassifiedItem)
        prompt_template = (
            "Ești un expert în taxonomii de restaurante HoReCa. Clasifică preparatul și extrage/deduce gramajul:\n\n"
            "REGULI STRICTE:\n"
            "1. 'standard_category' TREBUIE aleasă STRICT în limba română dintre: {categories}.\n"
            "2. 'item_type' TREBUIE ales STRICT în limba română (Mici, Cârnați, Friptură / Grătar, Platou, Ciorbă / Supă, Aperitiv / Gustare, Mâncare Gătită, Garnitură, Salată, Desert, Bere, Vin / Alcool, Răcoritoare / Cafea, Sos / Extra).\n"
            "3. 'grammage': Extrage sau deduce gramajul/volumul în unități standardizate (ex: 200g, 400ml, 750ml, 330ml, 1 buc). Folosește 'g' pentru grame (nu kg) și 'ml' pentru volum (nu L). Dacă nu e menționat, deduce un gramaj standard pentru porția respectivă.\n\n"
            "Restaurant: {restaurant}\n"
            "Categorie originală: {orig_cat}\n"
            "Nume preparat: {item_name}\n"
            "Gramaj brut: {raw_grammage}\n"
            "Descriere: {description}\n"
            "Preț: {price} RON\n"
        )
        
        print(f"Starting LLM semantic classification for {len(raw_items)} items...")
        for i, item in enumerate(raw_items):
            try:
                res = structured_llm.invoke(prompt_template.format(
                    categories=", ".join(CATEGORIES),
                    restaurant=item.get("restaurant_name", ""),
                    orig_cat=item.get("category", ""),
                    item_name=item.get("item_name", ""),
                    raw_grammage=item.get("grammage", ""),
                    description=item.get("description", ""),
                    price=item.get("price", 0)
                ))
                item_dict = res.model_dump()
                item_dict["grammage"] = normalize_grammage_string(item_dict.get("grammage"))
                if item_dict["grammage"] == "N/A":
                    item_dict["grammage"] = extract_grammage_fallback(
                        item.get("item_name", ""), item.get("description", ""), str(item.get("grammage", ""))
                    )
                classified.append(item_dict)
            except Exception as e:
                classified.append(classify_single_item_rulebased(item))
            
            if (i + 1) % 50 == 0:
                print(f"Classified {i + 1}/{len(raw_items)} items via LLM...")
    else:
        for item in raw_items:
            classified_item = classify_single_item_rulebased(item)
            classified.append(classified_item)

    state["classified_items"] = classified
    return state


def validate_node(state: GraphState) -> GraphState:
    items = state.get("classified_items", [])
    retry_count = state.get("retry_count", 0)
    
    missing_grammage = []
    category_counts = {}
    restaurant_counts = {}

    for idx, item in enumerate(items):
        item["grammage"] = normalize_grammage_string(item.get("grammage"))
        cat = item["standard_category"]
        rest = item["restaurant_name"]
        category_counts[cat] = category_counts.get(cat, 0) + 1
        restaurant_counts[rest] = restaurant_counts.get(rest, 0) + 1

        gram = str(item.get("grammage") or "").strip()
        if gram in ["", "N/A", "None", "null"]:
            missing_grammage.append((idx, item))

    print(f"VALIDATION NODE: Found {len(missing_grammage)} items with missing grammage (N/A) out of {len(items)} items.")

    if missing_grammage and retry_count < 1:
        print(f"VALIDATION LOOP TRIGGERED: Sending {len(missing_grammage)} items back to AI Refinement Node (Retry {retry_count + 1})...")
        state["items_to_refine"] = [item_tuple[1] for item_tuple in missing_grammage]
        state["retry_count"] = retry_count + 1
    else:
        state["items_to_refine"] = []

    stats = {
        "total_items": len(items),
        "restaurant_breakdown": restaurant_counts,
        "category_breakdown": category_counts,
        "missing_grammage_count": len(missing_grammage)
    }

    state["stats"] = stats
    return state


def refine_grammage_node(state: GraphState) -> GraphState:
    to_refine = state.get("items_to_refine", [])
    classified = state.get("classified_items", [])
    llm = get_llm_model()

    if not to_refine:
        return state

    print(f"AI REFINEMENT NODE: Deducting standard portion grammages for {len(to_refine)} items...")

    refined_map = {}
    if llm:
        structured_refiner = llm.with_structured_output(RefinedGrammage)
        refine_prompt = (
            "Deduce gramajul/volumul/porția standard (în g sau ml sau buc) pentru un preparat dintr-un restaurant românesc "
            "unde gramajul nu a fost specificat de client.\n"
            "Ghid de deducere:\n"
            "- Ciorbe / Supe: 400ml\n"
            "- Mâncăruri Gătite / Grătar / Fripturi: 200g - 350g\n"
            "- Garnituri / Salate: 150g - 200g\n"
            "- Aperitive / Gustări: 150g - 250g\n"
            "- Sosuri / Muștar / Smântână: 50g\n"
            "- Desert (Păpănași, Clătite, Cakes): 150g - 250g\n"
            "- Bere / Răcoritoare: 330ml sau 500ml\n"
            "- Vin / Alcool: 50ml (tărie) sau 750ml (sticlă vin) sau 150ml (pahar vin)\n"
            "- Pâine / Chiflă: 1 buc sau 150g\n\n"
            "Nume preparat: {item_name}\n"
            "Categorie: {category}\n"
            "Descriere: {description}\n"
        )

        for i, item in enumerate(to_refine):
            try:
                res = structured_refiner.invoke(refine_prompt.format(
                    item_name=item.get("item_name", ""),
                    category=item.get("standard_category", ""),
                    description=item.get("description", "")
                ))
                refined_map[item.get("item_name")] = normalize_grammage_string(res.inferred_grammage)
            except Exception:
                cat = item.get("standard_category", "")
                if "Ciorbe" in cat:
                    refined_map[item.get("item_name")] = "400ml"
                elif "Bere" in cat or "Răcoritoare" in cat:
                    refined_map[item.get("item_name")] = "500ml"
                elif "Sosuri" in cat:
                    refined_map[item.get("item_name")] = "50g"
                elif "Salate" in cat or "Garnituri" in cat:
                    refined_map[item.get("item_name")] = "150g"
                else:
                    refined_map[item.get("item_name")] = "200g"

    for item in classified:
        if item.get("grammage") in ["", "N/A", "None", "null"] and item.get("item_name") in refined_map:
            item["grammage"] = refined_map[item.get("item_name")]

    state["classified_items"] = classified
    state["items_to_refine"] = []
    print(f"AI REFINEMENT NODE COMPLETED: Updated grammages for {len(refined_map)} items.")
    return state


def export_node(state: GraphState) -> GraphState:
    items = state.get("classified_items", [])
    
    # Final cleanup of all grammages before saving
    for item in items:
        item["grammage"] = normalize_grammage_string(item.get("grammage"))

    processed_dir = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)

    json_path = os.path.join(processed_dir, "competitors_classified.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

    csv_path = os.path.join(processed_dir, "competitors_classified.csv")
    if items:
        fieldnames = list(items[0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(items)

    print(f"Exported JSON dataset to: {json_path}")
    print(f"Exported CSV dataset to:  {csv_path}")

    stats = state.get("stats", {})
    print("\n========================================")
    print("LangGraph Self-Correcting Summary:")
    print(f"- Total Items Processed: {stats.get('total_items', 0)}")
    print(f"- Remaining N/A Grammages: {stats.get('missing_grammage_count', 0)}")
    print("- Breakdown by Restaurant:")
    for rest, count in stats.get("restaurant_breakdown", {}).items():
        print(f"  * {rest}: {count} items")
    print("- Breakdown by Standard Category:")
    for cat, count in stats.get("category_breakdown", {}).items():
        print(f"  * {cat}: {count} items")
    print("========================================\n")

    return state


def should_refine(state: GraphState) -> str:
    if state.get("items_to_refine") and state.get("retry_count", 0) <= 1:
        return "refine"
    return "export"


def build_classification_graph():
    from langgraph.graph import StateGraph, END
    builder = StateGraph(GraphState)

    builder.add_node("ingest", ingest_node)
    builder.add_node("classify", classify_node)
    builder.add_node("validate", validate_node)
    builder.add_node("refine_grammage", refine_grammage_node)
    builder.add_node("export", export_node)

    builder.set_entry_point("ingest")
    builder.add_edge("ingest", "classify")
    builder.add_edge("classify", "validate")
    
    # Conditional LangGraph Loop: Validate -> Refine -> Validate -> Export
    builder.add_conditional_edges("validate", should_refine, {
        "refine": "refine_grammage",
        "export": "export"
    })
    builder.add_edge("refine_grammage", "validate")
    builder.add_edge("export", END)

    return builder.compile()


if __name__ == "__main__":
    app = build_classification_graph()
    app.invoke({
        "raw_items": [],
        "classified_items": [],
        "items_to_refine": [],
        "retry_count": 0,
        "stats": {}
    })
