#!/usr/bin/env python3
"""
Test Script — Inventory System Full Coverage

Teste le système d'inventaire via l'API REST :
  1. Add items
  2. List inventory (avec equipped_slot, item_level)
  3. Equip item (avec validation slot)
  4. Unequip item
  5. Get loadout
  6. Assemble item (gacha fusion)
  7. Slot validation (erreur si mauvais type)
  8. Remove items

Usage:
    docker exec echoes_backend python -m scripts.test_inventory
"""
import sys
import requests

BASE_URL = "http://localhost:6000"


class Colors:
    HEADER = '\033[95m'
    OK = '\033[92m'
    WARN = '\033[93m'
    FAIL = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


results = {"pass": 0, "fail": 0}


def header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== {text} ==={Colors.END}")

def section(text):
    print(f"\n{Colors.CYAN}--- {text} ---{Colors.END}")

def info(text):
    print(f"  {Colors.BOLD}ℹ️  {text}{Colors.END}")

def check(name, condition, details=""):
    if condition:
        print(f"  {Colors.OK}✅ {name}{Colors.END}" + (f" → {details}" if details else ""))
        results["pass"] += 1
    else:
        print(f"  {Colors.FAIL}❌ {name}{Colors.END}" + (f" → {details}" if details else ""))
        results["fail"] += 1

def api(method, path, **kwargs):
    url = f"{BASE_URL}{path}"
    try:
        r = requests.get(url, **kwargs) if method.lower() == "get" else requests.post(url, **kwargs)
        try:
            data = r.json()
        except Exception:
            data = r.text
        return {"status": r.status_code, "data": data}
    except Exception as e:
        print(f"  {Colors.FAIL}❌ {method.upper()} {path} → Exception: {e}{Colors.END}")
        return {"status": 0, "data": str(e)}


def cleanup(player_id=1):
    """Retire tous les couperet_noir du joueur pour repartir propre."""
    api("post", f"/inventory/remove?player_id={player_id}&item_id=couperet_noir&quantity=99")


# ─── Test 1: Add Items ───────────────────────────────────

def test_add_inventory():
    header("TEST 1: Add Items to Inventory")
    cleanup()

    res = api("post", "/inventory/add?player_id=1&item_id=couperet_noir&quantity=1")
    check("Added 1x couperet_noir", res["status"] == 200, f"status={res['status']}")

    # Ajouter des copies pour tester l'assemblage plus tard
    res = api("post", "/inventory/add?player_id=1&item_id=couperet_noir&quantity=4")
    check("Added 4 more copies (total 5)", res["status"] == 200, f"status={res['status']}")

    # Item inexistant doit échouer
    res = api("post", "/inventory/add?player_id=1&item_id=item_inexistant&quantity=1")
    check("Unknown item_id rejected (400)", res["status"] == 400, f"status={res['status']}")


# ─── Test 2: List Inventory ──────────────────────────────

def test_get_inventory():
    header("TEST 2: List Inventory — Champs complets")

    res = api("get", "/inventory/1")
    check("GET /inventory/1 → 200", res["status"] == 200, f"status={res['status']}")

    if res["status"] != 200:
        return

    data = res["data"]
    info(f"Inventory: {len(data)} entrée(s)")

    found = next((e for e in data if e.get("item_id") == "couperet_noir"), None)
    check("couperet_noir trouvé dans l'inventaire", found is not None)

    if found:
        check("Champ equipped_slot présent", "equipped_slot" in found, f"val={found.get('equipped_slot')}")
        check("Champ item_level présent", "item_level" in found, f"val={found.get('item_level')}")
        check("Champ item_xp présent", "item_xp" in found, f"val={found.get('item_xp')}")
        check("item_details présent", found.get("item_details") is not None)
        check("item_level = 1 par défaut", found.get("item_level") == 1, f"level={found.get('item_level')}")


# ─── Test 3: Equip Item ──────────────────────────────────

def test_equip_item():
    header("TEST 3: Equip Item — slot weapon_1")

    res = api("get", "/inventory/1")
    if res["status"] != 200:
        return

    inv_id = next(
        (e["inventory_id"] for e in res["data"]
         if e.get("item_id") == "couperet_noir" and e.get("equipped_slot") is None),
        None
    )
    if not inv_id:
        info("Aucun couperet_noir non-équipé trouvé.")
        return

    res = api("post", f"/inventory/{inv_id}/equip?slot=weapon_1")
    check("Équipé sur weapon_1 → 200", res["status"] == 200, f"status={res['status']}")
    if res["status"] == 200:
        check("equipped_slot = weapon_1", res["data"].get("equipped_slot") == "weapon_1",
              f"val={res['data'].get('equipped_slot')}")


# ─── Test 4: Slot Validation ─────────────────────────────

def test_slot_validation():
    header("TEST 4: Slot Validation — WEAPON ne peut pas aller dans 'head'")

    res = api("get", "/inventory/1")
    if res["status"] != 200:
        return

    inv_id = next(
        (e["inventory_id"] for e in res["data"]
         if e.get("item_id") == "couperet_noir" and e.get("equipped_slot") is None),
        None
    )
    if not inv_id:
        info("Pas de copie non-équipée pour tester la validation.")
        return

    res = api("post", f"/inventory/{inv_id}/equip?slot=head")
    check("WEAPON sur slot 'head' rejeté (400)", res["status"] == 400,
          f"status={res['status']} detail={res['data'].get('detail', '')[:60]}")

    res = api("post", f"/inventory/{inv_id}/equip?slot=armor")
    check("WEAPON sur slot 'armor' rejeté (400)", res["status"] == 400,
          f"status={res['status']}")


# ─── Test 5: Get Loadout ─────────────────────────────────

def test_get_loadout():
    header("TEST 5: GET /inventory/1/loadout")

    res = api("get", "/inventory/1/loadout")
    check("GET /loadout → 200", res["status"] == 200, f"status={res['status']}")

    if res["status"] != 200:
        return

    data = res["data"]
    slots = ["weapon_1", "weapon_2", "echo_1", "echo_2", "head", "armor", "artifact", "blessing", "consumable"]

    check("Tous les 9 slots présents", all(s in data for s in slots),
          f"slots présents: {list(data.keys())}")

    weapon1 = data.get("weapon_1")
    check("weapon_1 est occupé (couperet_noir équipé)", weapon1 is not None)

    if weapon1:
        check("weapon_1 a item_level", "item_level" in weapon1)
        check("weapon_1 a item_details", weapon1.get("item_details") is not None)
        info(f"weapon_1: {weapon1.get('item_id')} lvl {weapon1.get('item_level')}")

    check("weapon_2 est vide (None)", data.get("weapon_2") is None)


# ─── Test 6: Unequip Item ────────────────────────────────

def test_unequip_item():
    header("TEST 6: Unequip Item")

    res = api("get", "/inventory/1")
    if res["status"] != 200:
        return

    inv_id = next(
        (e["inventory_id"] for e in res["data"]
         if e.get("item_id") == "couperet_noir" and e.get("equipped_slot") == "weapon_1"),
        None
    )
    if not inv_id:
        info("Aucun couperet_noir équipé en weapon_1.")
        return

    res = api("post", f"/inventory/{inv_id}/unequip")
    check("Déséquipé → 200", res["status"] == 200, f"status={res['status']}")

    # Vérifier que le loadout est vide
    res = api("get", "/inventory/1/loadout")
    if res["status"] == 200:
        check("weapon_1 vide après unequip", res["data"].get("weapon_1") is None)


# ─── Test 7: Assemble (Gacha Fusion) ────────────────────

def test_assemble():
    header("TEST 7: Assemble — Fusion gacha (lvl 1 → lvl 2 coûte 2 copies)")

    # On a 5 copies en inventaire, coût = item_level(1) + 1 = 2 copies
    res = api("post", "/inventory/assemble?player_id=1&item_id=couperet_noir")
    check("Assemblage → 200", res["status"] == 200, f"status={res['status']}, data={res['data']}")

    if res["status"] == 200:
        data = res["data"]
        check("new_level = 2", data.get("new_level") == 2, f"level={data.get('new_level')}")
        check("copies_consumed = 1", data.get("copies_consumed") == 1,
              f"consumed={data.get('copies_consumed')}")
        info(f"Item après assemblage : {data}")

    # Vérifier que l'item en inventaire a bien item_level=2
    res = api("get", "/inventory/1")
    if res["status"] == 200:
        lvl2 = next((e for e in res["data"]
                     if e.get("item_id") == "couperet_noir" and e.get("item_level") == 2), None)
        check("item_level = 2 dans l'inventaire", lvl2 is not None)

    section("Assemblage lvl 2 → lvl 3 (coût = 3 copies)")
    # Il reste ~3 copies (5 - 2 consommées). Coût lvl2→lvl3 = 3. On est juste.
    res = api("post", "/inventory/assemble?player_id=1&item_id=couperet_noir")
    check("Assemblage lvl 2 → 3 → 200", res["status"] == 200,
          f"status={res['status']}, data={res['data']}")
    if res["status"] == 200:
        check("new_level = 3", res["data"].get("new_level") == 3)

    section("Assemblage avec pas assez de copies (doit échouer)")
    res = api("post", "/inventory/assemble?player_id=1&item_id=couperet_noir")
    check("Pas assez de copies → 400", res["status"] == 400,
          f"status={res['status']}, detail={res['data'].get('detail', '')[:80]}")


# ─── Test 8: Remove Items ────────────────────────────────

def test_remove_inventory():
    header("TEST 8: Remove Items")

    cleanup()
    res = api("get", "/inventory/1")
    if res["status"] == 200:
        remaining = [e for e in res["data"] if e.get("item_id") == "couperet_noir"]
        check("Aucun couperet_noir restant après cleanup", len(remaining) == 0,
              f"restants: {len(remaining)}")

    # Supprimer un item inexistant doit retourner 400
    res = api("post", "/inventory/remove?player_id=1&item_id=couperet_noir&quantity=1")
    check("Remove sur quantité nulle → 400", res["status"] == 400)


# ─── Main ────────────────────────────────────────────────

def main():
    global BASE_URL

    if "--host" in sys.argv:
        idx = sys.argv.index("--host")
        BASE_URL = sys.argv[idx + 1]

    header("🎒 ECHOES INVENTORY SYSTEM — FULL TEST SUITE")
    info(f"Target: {BASE_URL}")
    print()

    test_add_inventory()
    test_get_inventory()
    test_equip_item()
    test_slot_validation()
    test_get_loadout()
    test_unequip_item()
    test_assemble()
    test_remove_inventory()

    # ─── Summary ─────────────────────────────────────
    header("📊 RESULTS")
    total = results["pass"] + results["fail"]
    print(f"  {Colors.OK}PASS: {results['pass']}{Colors.END}")
    print(f"  {Colors.FAIL}FAIL: {results['fail']}{Colors.END}")
    print(f"  Total: {total}")
    print()

    if results["fail"] == 0:
        print(f"  {Colors.OK}{Colors.BOLD}🏆 ALL TESTS PASSED!{Colors.END}")
    else:
        print(f"  {Colors.WARN}{Colors.BOLD}⚠️  {results['fail']} test(s) failed — see above{Colors.END}")

    return 0 if results["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
