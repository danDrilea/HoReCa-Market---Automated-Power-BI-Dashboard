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

# Define Taxonomy Categories & Types
CATEGORIES = [
    "Preparate la Grătar & Mici",
    "Cârnați & Platouri",
    "Mâncăruri Gătite & Specialități",
    "Ciorbe & Supe",
    "Aperitive & Gustări",
    "Garnituri",
    "Salate",
    "Pizza & Foietaje",
    "Desert",
    "Băuturi Alcoolice & Bere",
    "Băuturi Răcoritoare & Cafea",
    "Sosuri & Extra"
]

ITEM_TYPES = [
    "Mici", "Cârnați", "Friptură / Grătar", "Platou", "Ciorbă / Supă",
    "Aperitiv / Gustare", "Mâncare Gătită", "Garnitură", "Salată",
    "Pizza", "Desert", "Bere", "Vin / Alcool", "Răcoritoare / Cafea", "Sos / Extra"
]


class ClassifiedItem(BaseModel):
    restaurant_name: str = Field(description="Numele restaurantului")
    original_category: str = Field(description="Categoria originală")
    standard_category: str = Field(description="Categoria standardizată din lista de taxonomii")
    item_type: str = Field(description="Tipul produsului (Mici, Cârnați, Ciorbă, Bere, etc.)")
    item_name: str = Field(description="Denumirea preparatului")
    grammage: str | None = Field(default=None, description="Gramajul sau volumul (ex: 200g, 500ml)")
    description: str = Field(default="", description="Descrierea preparatului")
    price_ron: float = Field(description="Prețul în RON")
    currency: str = Field(default="RON", description="Valuta")
    scraped_at: str = Field(description="Data colectării")


class GraphState(TypedDict):
    raw_items: List[Dict[str, Any]]
    classified_items: List[Dict[str, Any]]
    stats: Dict[str, Any]


def classify_single_item_rulebased(item: Dict[str, Any]) -> Dict[str, Any]:
    orig_cat = (item.get("category") or "").strip()
    name = (item.get("item_name") or "").strip()
    desc = (item.get("description") or "").strip()
    price = float(item.get("price") or 0.0)
    grammage = item.get("grammage")
    scraped_at = item.get("scraped_at") or datetime.now().isoformat()
    rest_name = item.get("restaurant_name") or "Competitor"

    name_lower = name.lower()
    cat_lower = orig_cat.lower()
    combined_text = f"{orig_cat} {name} {desc}".lower()

    # Default category & type
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

    elif re.search(r'\bpizza\b|\bfocaccia\b', name_lower) or re.search(r'\bpizza\b', cat_lower):
        std_cat = "Pizza & Foietaje"
        item_type = "Pizza"

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
        grammage=grammage,
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
    state["stats"] = {}
    return state


def classify_node(state: GraphState) -> GraphState:
    raw_items = state.get("raw_items", [])
    classified = []
    llm = get_llm_model()

    if llm:
        structured_llm = llm.with_structured_output(ClassifiedItem)
        prompt_template = (
            "Ești un expert în taxonomii de restaurante HoReCa. Clasifică următorul preparat "
            "într-una din categoriile standardizabile: {categories}.\n\n"
            "Restaurant: {restaurant}\n"
            "Categorie originală: {orig_cat}\n"
            "Nume preparat: {item_name}\n"
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
                    description=item.get("description", ""),
                    price=item.get("price", 0)
                ))
                classified.append(res.model_dump())
            except Exception as e:
                # Fallback on single item error
                classified.append(classify_single_item_rulebased(item))
            
            if (i + 1) % 50 == 0:
                print(f"Classified {i + 1}/{len(raw_items)} items via LLM...")
    else:
        for item in raw_items:
            classified_item = classify_single_item_rulebased(item)
            classified.append(classified_item)

    print(f"Classified {len(classified)} items into standardized categories.")
    state["classified_items"] = classified
    return state


def validate_node(state: GraphState) -> GraphState:
    items = state.get("classified_items", [])
    category_counts = {}
    restaurant_counts = {}

    for item in items:
        cat = item["standard_category"]
        rest = item["restaurant_name"]
        category_counts[cat] = category_counts.get(cat, 0) + 1
        restaurant_counts[rest] = restaurant_counts.get(rest, 0) + 1

    stats = {
        "total_items": len(items),
        "restaurant_breakdown": restaurant_counts,
        "category_breakdown": category_counts
    }

    state["stats"] = stats
    return state


def export_node(state: GraphState) -> GraphState:
    items = state.get("classified_items", [])
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
    print("LangGraph Classification Summary:")
    print(f"- Total Items Classified: {stats.get('total_items', 0)}")
    print("- Breakdown by Restaurant:")
    for rest, count in stats.get("restaurant_breakdown", {}).items():
        print(f"  * {rest}: {count} items")
    print("- Breakdown by Standard Category:")
    for cat, count in stats.get("category_breakdown", {}).items():
        print(f"  * {cat}: {count} items")
    print("========================================\n")

    return state


def build_classification_graph():
    from langgraph.graph import StateGraph, END
    builder = StateGraph(GraphState)

    builder.add_node("ingest", ingest_node)
    builder.add_node("classify", classify_node)
    builder.add_node("validate", validate_node)
    builder.add_node("export", export_node)

    builder.set_entry_point("ingest")
    builder.add_edge("ingest", "classify")
    builder.add_edge("classify", "validate")
    builder.add_edge("validate", "export")
    builder.add_edge("export", END)

    return builder.compile()


if __name__ == "__main__":
    app = build_classification_graph()
    app.invoke({"raw_items": [], "classified_items": [], "stats": {}})
