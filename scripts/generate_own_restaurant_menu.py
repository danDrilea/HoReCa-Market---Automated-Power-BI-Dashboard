import csv
import os
import re
from datetime import datetime

def determine_item_type(category: str, name: str) -> str:
    name_lower = name.lower()
    
    if category == "Preparate la Grătar & Mici":
        if "mici" in name_lower or "mititei" in name_lower:
            return "Mici"
        return "Friptură / Grătar"
    elif category == "Cârnați & Platouri":
        if "platou" in name_lower:
            return "Platou"
        return "Cârnați"
    elif category == "Ciorbe & Supe":
        return "Ciorbă / Supă"
    elif category == "Aperitive & Gustări":
        return "Aperitiv / Gustare"
    elif category == "Garnituri":
        return "Garnitură"
    elif category == "Salate":
        return "Salată"
    elif category == "Desert":
        return "Desert"
    elif category == "Sosuri & Extra":
        return "Sos / Extra"
    elif category == "Băuturi Alcoolice & Bere":
        if "bere" in name_lower or "draught" in name_lower or "lager" in name_lower:
            return "Bere"
        return "Vin / Alcool"
    elif category == "Băuturi Răcoritoare & Cafea":
        return "Răcoritoare / Cafea"
    return "Mâncare Gătită"

def generate_own_menu():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    competitors_csv = os.path.join(base_dir, "data", "processed", "competitors_classified.csv")
    output_csv = os.path.join(base_dir, "data", "processed", "restaurant_classified.csv")

    if not os.path.exists(competitors_csv):
        print(f"Error: {competitors_csv} not found.")
        return

    own_items = [
        # Preparate la Grătar & Mici
        {"cat": "Preparate la Grătar & Mici", "name": "Mici Românești de Vită-Porc (1 buc)", "gram": "80g", "desc": "Mici zemoși preparați pe grătar cu cărbuni, serviți cu muștar", "price": 7.5},
        {"cat": "Preparate la Grătar & Mici", "name": "Mici de Oaie și Vită (1 buc)", "gram": "80g", "desc": "Mici tradiționali din carne de oaie și vită la grătar", "price": 8.5},
        {"cat": "Preparate la Grătar & Mici", "name": "Ceafă de Porc la Grătar", "gram": "250g", "desc": "Fragedă și marinat în mirodenii tradiționale", "price": 38.0},
        {"cat": "Preparate la Grătar & Mici", "name": "Piept de Pui la Grătar", "gram": "220g", "desc": "Piept de pui suculent la grătar cu ierburi aromatice", "price": 34.0},
        {"cat": "Preparate la Grătar & Mici", "name": "Frăție de Mici & Cârnați", "gram": "450g", "desc": "4 mici românești, cârnați afumați, cartofi prăjiți și muștar", "price": 54.0},
        {"cat": "Preparate la Grătar & Mici", "name": "Frigărui de Berbecuț", "gram": "250g", "desc": "Carne fragedă de berbecuț cu ardei și ceapă la grătar", "price": 58.0},

        # Ciorbe & Supe
        {"cat": "Ciorbe & Supe", "name": "Ciorbă de Perișoare", "gram": "400ml", "desc": "Ciorbă acrișoară cu perișoare din carne de vită și porc", "price": 24.0},
        {"cat": "Ciorbe & Supe", "name": "Ciorbă Rădăuțeană de Pui", "gram": "400ml", "desc": "Ciorbă cremoasă cu pui, smântână, usturoi și ardei iute", "price": 26.0},
        {"cat": "Ciorbe & Supe", "name": "Ciorbă de Burtiță Tradițională", "gram": "400ml", "desc": "Servită cu smântână proaspătă și ardei iute", "price": 28.0},
        {"cat": "Ciorbe & Supe", "name": "Ciorbă de Văcuță", "gram": "400ml", "desc": "Bogată în legume proaspete și bucăți fragede de mânzat", "price": 25.0},
        {"cat": "Ciorbe & Supe", "name": "Supă Cremă de Legume cu Crutoane", "gram": "350ml", "desc": "Supă fină de legume proaspete cu crutoane aromate", "price": 22.0},

        # Cârnați & Platouri
        {"cat": "Cârnați & Platouri", "name": "Platou Boieresc (2-3 persoane)", "gram": "1200g", "desc": "Ceafă de porc, mici, cârnați afumați, cartofi berărești, varză murată", "price": 145.0},
        {"cat": "Cârnați & Platouri", "name": "Platou Cârnați Asortați", "gram": "800g", "desc": "Cârnați de casă, cârnați picanți și cârnați de oaie cu hrean", "price": 95.0},
        {"cat": "Cârnați & Platouri", "name": "Platou Gustări Rece Tradiționale", "gram": "700g", "desc": "Toboșar, slăninuță, șuncă de casă, brânză de burduf, ceapă roșie", "price": 85.0},
        {"cat": "Cârnați & Platouri", "name": "Cârnați Picanți de Pleșcoi", "gram": "250g", "desc": "Cârnați tradiționali din carne de oaie și vită, uscați și afumați", "price": 42.0},

        # Mâncăruri Gătite & Specialități
        {"cat": "Mâncăruri Gătite & Specialități", "name": "Tochitură Moldovenească cu Mămăligă", "gram": "450g", "desc": "Carne de porc, cârnați, ou ochi și brânză rasa peste mămăligă", "price": 48.0},
        {"cat": "Mâncăruri Gătite & Specialități", "name": "Ciolan de Porc Rumexit la Cuptor", "gram": "750g", "desc": "Ciolan rumenit cu crustă crocantă, servit cu iahnie de fasole", "price": 78.0},
        {"cat": "Mâncăruri Gătite & Specialități", "name": "Sarmale Românești în Foi de Varză (4 buc)", "gram": "400g", "desc": "Sarmale din carne tocată cu mămăligă, ardei iute și smântână", "price": 44.0},
        {"cat": "Mâncăruri Gătite & Specialități", "name": "Șnițel Gigant de Pui Pane", "gram": "300g", "desc": "Crispy și auriu, preparat din piept proaspăt de pui", "price": 36.0},
        {"cat": "Mâncăruri Gătite & Specialități", "name": "Pastramă de Oaie la Tigaie cu Mămăligă", "gram": "350g", "desc": "Pastramă fragedă trasă în vin și usturoi cu mămăligă caldă", "price": 56.0},
        {"cat": "Mâncăruri Gătite & Specialități", "name": "Burger Casei cu Cartofi Prăjiți", "gram": "400g", "desc": "Chiftea din carne de vită Black Angus, cheddar, bacon și sos special", "price": 49.0},

        # Aperitive & Gustări
        {"cat": "Aperitive & Gustări", "name": "Salată de Vinete Coapte pe Plită", "gram": "200g", "desc": "Servită cu ceapă roșie tocată și pâine prăjită", "price": 24.0},
        {"cat": "Aperitive & Gustări", "name": "Fasole Bătută cu Ceapă Călită", "gram": "200g", "desc": "Fasole frecată cu usturoi și ceapă prăjită aurie", "price": 20.0},
        {"cat": "Aperitive & Gustări", "name": "Cașcaval Pane Crocant", "gram": "200g", "desc": "Feliuțe de cașcaval ruminate în pesmet auriu", "price": 28.0},
        {"cat": "Aperitive & Gustări", "name": "Bulz Ardelenesc la Grătar", "gram": "300g", "desc": "Mămăligă umplută cu brânză de burduf, kaiser și ou ochi", "price": 32.0},

        # Salate
        {"cat": "Salate", "name": "Salată Caesar cu Pui la Grătar", "gram": "350g", "desc": "Salată iceberg, piept de pui, crutoane, parmesan și sos Caesar", "price": 38.0},
        {"cat": "Salate", "name": "Salată Grecească", "gram": "350g", "desc": "Roșii, castraveți, ardei, brânză feta, măsline calamata și oregano", "price": 34.0},
        {"cat": "Salate", "name": "Salată de Murături Asortate", "gram": "200g", "desc": "Gogoșari, castraveți și gogonele murate în casă", "price": 14.0},
        {"cat": "Salate", "name": "Salată de Ardei Copți", "gram": "200g", "desc": "Ardei copți pe grătar în sos de oțet și usturoi", "price": 16.0},

        # Garnituri
        {"cat": "Garnituri", "name": "Cartofi Prăjiți cu Usturoi și Parmezan", "gram": "200g", "desc": "Cartofi proaspeți prăjiți, stropiți cu ulei de usturoi și parmezan", "price": 18.0},
        {"cat": "Garnituri", "name": "Piure de Cartofi cu Unt", "gram": "200g", "desc": "Piure cremos din cartofi proaspeți și unt fin", "price": 16.0},
        {"cat": "Garnituri", "name": "Iahnie de Fasole cu Bacon", "gram": "200g", "desc": "Fasole scăzută în sos de roșii cu boia dulce", "price": 16.0},
        {"cat": "Garnituri", "name": "Varză Călită în Vin cu Chimen", "gram": "200g", "desc": "Varză albă opărită și călită în vin alb", "price": 15.0},
        {"cat": "Garnituri", "name": "Mămăliguță Caldă", "gram": "200g", "desc": "Mămăligă din mălai proaspăt mocinat", "price": 8.0},

        # Sosuri & Extra
        {"cat": "Sosuri & Extra", "name": "Muștar Clasic", "gram": "50g", "desc": "Muștar de masă fin", "price": 4.0},
        {"cat": "Sosuri & Extra", "name": "Mujdei de Usturoi Tradițional", "gram": "50g", "desc": "Usturoi frecat cu apă minerală și ulei", "price": 5.0},
        {"cat": "Sosuri & Extra", "name": "Smântână Proaspătă 20%", "gram": "50g", "desc": "Smântână cremoasă", "price": 5.0},
        {"cat": "Sosuri & Extra", "name": "Sos Barbeque", "gram": "50g", "desc": "Sos dulce-afumat BBQ", "price": 6.0},
        {"cat": "Sosuri & Extra", "name": "Coș de Pâine de Casă", "gram": "150g", "desc": "Pâine proaspăt coaptă în cuptor", "price": 7.0},

        # Desert
        {"cat": "Desert", "name": "Papanași cu Smântână și Dulceață de Afine (2 buc)", "gram": "300g", "desc": "Papanași prăjiți, pufoși, cu smântână fină și dulceață de afine", "price": 32.0},
        {"cat": "Desert", "name": "Clătite cu Finetti și Banane (2 buc)", "gram": "200g", "desc": "Clătite subțiri umplute generos", "price": 22.0},
        {"cat": "Desert", "name": "Ștrudel de Mere cu Sos de Vanilie", "gram": "200g", "desc": "Ștrudel cald cu mere caramelizate și scorțișoară", "price": 25.0},
        {"cat": "Desert", "name": "Lava Cake cu Înghețată de Vanilie", "gram": "180g", "desc": "Prăjitură de ciocolată neagră cu inimă lichidă", "price": 28.0},

        # Băuturi Alcoolice & Bere
        {"cat": "Băuturi Alcoolice & Bere", "name": "Bere Ciuc Premium la Draught 0.4L", "gram": "400ml", "desc": "Bere blondă proaspătă la halbă", "price": 14.0},
        {"cat": "Băuturi Alcoolice & Bere", "name": "Bere Heineken 0.33L", "gram": "330ml", "desc": "Bere lager sticlă", "price": 16.0},
        {"cat": "Băuturi Alcoolice & Bere", "name": "Bere Nepasteurizată Zăganu 0.5L", "gram": "500ml", "desc": "Bere artizanală românească", "price": 22.0},
        {"cat": "Băuturi Alcoolice & Bere", "name": "Țuică de Prune Ardelenească 50ml", "gram": "50ml", "desc": "Țuică bătrână dublu distilată 45%", "price": 18.0},
        {"cat": "Băuturi Alcoolice & Bere", "name": "Pachet Vinul Casei Fetească Regală 1L", "gram": "1000ml", "desc": "Vin alb sec carafă", "price": 55.0},
        {"cat": "Băuturi Alcoolice & Bere", "name": "Vin Purcari Rară Neagră Sticlă 0.75L", "gram": "750ml", "desc": "Vin roșu sec de colecție", "price": 95.0},

        # Băuturi Răcoritoare & Cafea
        {"cat": "Băuturi Răcoritoare & Cafea", "name": "Coca-Cola / Coca-Cola Zero 0.33L", "gram": "330ml", "desc": "Sticlă de sticlă", "price": 12.0},
        {"cat": "Băuturi Răcoritoare & Cafea", "name": "Limonadă Proaspătă cu Miere și Mentă 0.5L", "gram": "500ml", "desc": "Limonadă preparată pe loc", "price": 20.0},
        {"cat": "Băuturi Răcoritoare & Cafea", "name": "Apă Minerală / Plată Borsec 0.5L", "gram": "500ml", "desc": "Sticlă minerală Borsec", "price": 10.0},
        {"cat": "Băuturi Răcoritoare & Cafea", "name": "Espresso Scurt / Lung Julius Meinl", "gram": "60ml", "desc": "100% Arabica", "price": 12.0},
        {"cat": "Băuturi Răcoritoare & Cafea", "name": "Cappuccino cu Spumă de Lapte", "gram": "150ml", "desc": "Espresso cu spumă densă de lapte", "price": 15.0}
    ]

    now_str = datetime.now().isoformat()
    rows = []
    for item in own_items:
        item_type = determine_item_type(item["cat"], item["name"])
        rows.append({
            "restaurant_name": "Restaurantul Nostru",
            "original_category": item["cat"],
            "standard_category": item["cat"],
            "item_type": item_type,
            "item_name": item["name"],
            "grammage": item["gram"],
            "description": item["desc"],
            "price_ron": str(item["price"]),
            "currency": "RON",
            "scraped_at": now_str
        })

    fieldnames = [
        "restaurant_name", "original_category", "standard_category",
        "item_type", "item_name", "grammage", "description",
        "price_ron", "currency", "scraped_at"
    ]

    with open(output_csv, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"SUCCESS: Generated own menu ({len(rows)} items) at {output_csv}")

if __name__ == "__main__":
    generate_own_menu()
