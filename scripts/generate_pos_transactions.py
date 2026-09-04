import csv
import json
import os
import random
from datetime import datetime, timedelta

def load_own_restaurant_products(csv_path):
    items_list = []
    if not os.path.exists(csv_path):
        print(f"Eroare: Nu exista fisierul {csv_path}")
        return items_list

    with open(csv_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rest = row["restaurant_name"]
            try:
                price = float(row["price_ron"])
            except (ValueError, TypeError):
                continue
            if price <= 0:
                continue

            items_list.append({
                "nume_produs": row["item_name"],
                "categorie_standard": row["standard_category"],
                "pret_unitar_ron": price,
                "nume_restaurant": rest
            })
    return items_list

def generate_pos_transactions(catalog, total_orders=2500):
    # Set timeframe to 1 month (1 August 2026 - 31 August 2026) for internal POS
    start_date = datetime(2026, 8, 1, 10, 0, 0)
    end_date = datetime(2026, 8, 31, 23, 30, 0)
    total_seconds = int((end_date - start_date).total_seconds())

    restaurant_name = "Restaurantul Nostru"

    tipuri_comanda = ["La Masa", "Pachet", "Livrare"]
    tipuri_comanda_weights = [0.70, 0.15, 0.15]

    metode_plata = ["Card", "Numerar", "Bonuri de Masa"]
    metode_plata_weights = [0.65, 0.25, 0.10]

    ospatari = [f"OSP-{i:02d}" for i in range(1, 13)]

    orders = []
    order_items = []

    print(f"Generare {total_orders} tranzactii POS interne exclusiv pentru '{restaurant_name}' (August 2026)...")

    for i in range(1, total_orders + 1):
        order_id = f"ORD-202608-{i:05d}"

        random_second = random.randint(0, total_seconds)
        dt = start_date + timedelta(seconds=random_second)

        # Peak hours simulation (Pranz 12-14, Cina 18-22)
        hour = dt.hour
        if hour < 10 or hour > 23:
            hour = random.choice([12, 13, 14, 19, 20, 21, 22])
            dt = dt.replace(hour=hour, minute=random.randint(0, 59))

        tip_comanda = random.choices(tipuri_comanda, weights=tipuri_comanda_weights)[0]
        metoda_plata = random.choices(metode_plata, weights=metode_plata_weights)[0]
        id_ospatar = random.choice(ospatari) if tip_comanda == "La Masa" else "SYS-ONLINE"
        numar_masa = f"Masa {random.randint(1, 35)}" if tip_comanda == "La Masa" else "N/A"

        # 2 to 5 items per order
        basket_size = random.randint(2, 5)
        selected_items = random.sample(catalog, min(basket_size, len(catalog)))

        order_total = 0.0

        for item in selected_items:
            qty = random.choices([1, 2, 3], weights=[0.80, 0.16, 0.04])[0]
            unit_price = item["pret_unitar_ron"]
            line_total = round(qty * unit_price, 2)
            order_total += line_total

            order_items.append({
                "id_comanda": order_id,
                "nume_restaurant": restaurant_name,
                "nume_produs": item["nume_produs"],
                "categorie_standard": item["categorie_standard"],
                "cantitate": qty,
                "pret_unitar_ron": unit_price,
                "total_linie_ron": line_total
            })

        orders.append({
            "id_comanda": order_id,
            "data_ora": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "nume_restaurant": restaurant_name,
            "tip_comanda": tip_comanda,
            "metoda_plata": metoda_plata,
            "numar_masa": numar_masa,
            "id_ospatar": id_ospatar,
            "total_produse": len(selected_items),
            "total_bon_ron": round(order_total, 2)
        })

    orders.sort(key=lambda x: x["data_ora"])
    return orders, order_items

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    own_csv = os.path.join(base_dir, "data", "processed", "restaurant_classified.csv")
    output_dir = os.path.join(base_dir, "data", "processed")

    catalog = load_own_restaurant_products(own_csv)
    if not catalog:
        print(f"Eroare: Nu s-au putut incarca produsele din {own_csv}")
        return

    orders, order_items = generate_pos_transactions(catalog, total_orders=2500)

    orders_csv_path = os.path.join(output_dir, "pos_orders.csv")
    items_csv_path = os.path.join(output_dir, "pos_order_items.csv")
    flat_csv_path = os.path.join(output_dir, "pos_transactions_flat.csv")

    # 1. pos_orders.csv
    print(f"Scriere {len(orders)} comenzi in {orders_csv_path}...")
    with open(orders_csv_path, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id_comanda", "data_ora", "nume_restaurant", "tip_comanda", 
            "metoda_plata", "numar_masa", "id_ospatar", "total_produse", "total_bon_ron"
        ])
        writer.writeheader()
        writer.writerows(orders)

    # 2. pos_order_items.csv
    print(f"Scriere {len(order_items)} linii comanda in {items_csv_path}...")
    with open(items_csv_path, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id_comanda", "nume_restaurant", "nume_produs", "categorie_standard",
            "cantitate", "pret_unitar_ron", "total_linie_ron"
        ])
        writer.writeheader()
        writer.writerows(order_items)

    # 3. pos_transactions_flat.csv
    print(f"Scriere set de date plat in {flat_csv_path}...")
    orders_dict = {o["id_comanda"]: o for o in orders}
    flat_rows = []
    for item in order_items:
        o = orders_dict.get(item["id_comanda"], {})
        flat_rows.append({
            "id_comanda": item["id_comanda"],
            "data_ora": o.get("data_ora", ""),
            "nume_restaurant": item["nume_restaurant"],
            "tip_comanda": o.get("tip_comanda", ""),
            "metoda_plata": o.get("metoda_plata", ""),
            "numar_masa": o.get("numar_masa", ""),
            "id_ospatar": o.get("id_ospatar", ""),
            "nume_produs": item["nume_produs"],
            "categorie_standard": item["categorie_standard"],
            "cantitate": item["cantitate"],
            "pret_unitar_ron": item["pret_unitar_ron"],
            "total_linie_ron": item["total_linie_ron"]
        })

    with open(flat_csv_path, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id_comanda", "data_ora", "nume_restaurant", "tip_comanda", "metoda_plata",
            "numar_masa", "id_ospatar", "nume_produs", "categorie_standard", "cantitate",
            "pret_unitar_ron", "total_linie_ron"
        ])
        writer.writeheader()
        writer.writerows(flat_rows)

    print("SUCCES: Tranzactiile POS au fost generate EXCLUSIV pentru Restaurantul Nostru!")

if __name__ == "__main__":
    main()
