"""
Test Script — Combat System Full Coverage

Teste le système de combat via l'API REST :
  1. Start Battle
  2. Spell Turns (damage, status, crit, cooldowns, echo cost)
  3. Status ticks (laceration bleed)
  4. Passives (on_hit)
  5. Battle State
  6. Abandon
  7. Multi-monster (different archetypes)

Usage:
    cd backend
    # Depuis la machine locale (le container écoute sur 6000)
    python scripts/test_combat.py

    # Ou depuis le container
    python scripts/test_combat.py --host http://localhost:6000
"""
import sys
import requests
import json
import time

BASE_URL = "http://localhost:6000"


# ─── Helpers ─────────────────────────────────────────────

class Colors:
    OK = "\033[92m"
    FAIL = "\033[91m"
    WARN = "\033[93m"
    INFO = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"

def header(text):
    print(f"\n{Colors.BOLD}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{Colors.END}\n")

def section(text):
    print(f"\n{Colors.INFO}--- {text} ---{Colors.END}")

def ok(msg):
    print(f"  {Colors.OK}✅ {msg}{Colors.END}")

def fail(msg):
    print(f"  {Colors.FAIL}❌ {msg}{Colors.END}")

def warn(msg):
    print(f"  {Colors.WARN}⚠️  {msg}{Colors.END}")

def info(msg):
    print(f"  {Colors.INFO}ℹ️  {msg}{Colors.END}")


results = {"pass": 0, "fail": 0}

def check(test_name: str, condition: bool, detail: str = ""):
    """Assert + compteur."""
    if condition:
        ok(f"{test_name}" + (f" → {detail}" if detail else ""))
        results["pass"] += 1
    else:
        fail(f"{test_name}" + (f" → {detail}" if detail else ""))
        results["fail"] += 1


def api(method: str, path: str, **kwargs) -> dict:
    """Appel API avec gestion d'erreur."""
    url = f"{BASE_URL}{path}"
    try:
        resp = getattr(requests, method)(url, **kwargs)
        data = resp.json()
        if resp.status_code >= 400:
            warn(f"{method.upper()} {path} → {resp.status_code}: {data.get('detail', data)}")
        return {"status": resp.status_code, "data": data}
    except Exception as e:
        fail(f"{method.upper()} {path} → Exception: {e}")
        return {"status": 0, "data": {}}


def print_logs(battle_data: dict, last_n: int = 10):
    """Affiche les derniers logs de combat."""
    logs = battle_data.get("log", [])
    if logs:
        recent = logs[-last_n:]
        for log in recent:
            print(f"    📝 {log}")


def get_hp(battle_data: dict, entity: str) -> int:
    """Récupère les HP d'une entité."""
    e = battle_data.get(entity, {})
    return e.get("stats", {}).get("HP", e.get("hp", 0))


def get_statuses(battle_data: dict, entity: str) -> dict:
    """Récupère les statuts d'une entité."""
    e = battle_data.get(entity, {})
    return e.get("statuses", {})


def cleanup_active_battle(battle_id):
    """Abandonne un combat actif."""
    if battle_id:
        api("post", f"/battle/{battle_id}/abandon")


def start_fresh_battle(player_id=1, monster_id=2, level=1):
    """Start a battle, auto-abandoning any existing active one."""
    res = api("post", f"/battle/start?player_id={player_id}&monster_id={monster_id}&monster_level={level}")
    # If player has active battle, abandon it and retry
    if res["status"] == 400 and "active battle" in str(res["data"].get("detail", "")).lower():
        # Extract battle id from message
        msg = str(res["data"].get("detail", ""))
        import re
        m = re.search(r'id=(\d+)', msg)
        if m:
            api("post", f"/battle/{m.group(1)}/abandon")
        res = api("post", f"/battle/start?player_id={player_id}&monster_id={monster_id}&monster_level={level}")
    return res


# ─── Test 1: Server Health ───────────────────────────────

def test_server_alive():
    header("TEST 1: Server Connectivity")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        check("Server reachable", resp.status_code in [200, 500],
              f"status={resp.status_code}")
    except requests.ConnectionError:
        fail("Server not reachable! Make sure uvicorn is running on :6000")
        print(f"\n  Essaye: docker compose -f docker-compose.dev.yml exec backend uvicorn main:app --reload --host 0.0.0.0 --port 6000")
        sys.exit(1)


# ─── Test 2: Start Battle ───────────────────────────────

def test_start_battle(player_id=1, monster_id=2, level=1):
    header("TEST 2: Start Battle (Lycans, Lv1)")

    res = start_fresh_battle(player_id, monster_id, level)
    data = res["data"]

    check("POST /battle/start returns 200", res["status"] == 200, f"status={res['status']}")
    check("Response has battle_id", "battle_id" in data, f"keys={list(data.keys())}")

    battle_id = data.get("battle_id")
    battle = data.get("battle", {})

    check("Battle has player", "player" in battle)
    check("Battle has monster", "monster" in battle)
    check("Player HP = 800", get_hp(battle, "player") == 800, f"HP={get_hp(battle, 'player')}")
    check("Monster HP = 500", get_hp(battle, "monster") == 500, f"HP={get_hp(battle, 'monster')}")
    check("Battle status is active", battle.get("status") in ["IN_PROGRESS", "PLAYER_TURN", "PENDING"])

    info(f"Battle #{battle_id} created")
    print_logs(battle)

    return battle_id


# ─── Test 3: Execute Turn — Coup-peret (Physical Damage) ─

def test_turn_coup_peret(battle_id):
    header("TEST 3: Turn — Coup-peret (Physical Damage + Crit check)")

    section("Casting Coup-peret")
    res = api("post", f"/battle/{battle_id}/turn?spell_code=coup_peret&item_id=couperet_noir")
    data = res["data"]

    check("POST /turn returns 200", res["status"] == 200, f"status={res['status']}")

    battle = data.get("battle", {})
    monster_hp = get_hp(battle, "monster")

    check("Monster took damage", monster_hp < 500, f"Monster HP: {monster_hp}/500")
    check("Turn count advanced", battle.get("turn", 0) >= 1, f"turn={battle.get('turn')}")

    # Check logs for damage
    logs = battle.get("log", [])
    has_damage_log = any("coup-peret" in str(l).lower() or "takes" in str(l).lower() for l in logs)
    check("Damage log present", has_damage_log)

    # Check if crit happened (informational)
    has_crit = any("crit" in str(l).lower() for l in logs)
    if has_crit:
        info("Critical hit occurred!")
    else:
        info("No critical hit (normal)")

    # Check physical mitigation (monster Lycans has 20 armor)
    info(f"Monster took {500 - monster_hp} damage (physical, mitigated by 20 armor)")

    print_logs(battle)
    return monster_hp


# ─── Test 4: Cooldown Check ─────────────────────────────

def test_cooldown(battle_id):
    header("TEST 4: Cooldown Enforcement")

    section("Re-casting Coup-peret (should fail — 3 turn CD)")
    res = api("post", f"/battle/{battle_id}/turn?spell_code=coup_peret&item_id=couperet_noir")

    # Should return an error because coup_peret is on cooldown
    has_error = "error" in res["data"] or res["status"] >= 400
    check("Cooldown prevents re-cast", has_error,
          f"response: {res['data'].get('detail', res['data'].get('error', 'ok'))}")


def test_echo_gain(battle_id):
    header("TEST 4.5: Echo Generation")
    
    section("Checking Echo Gauge")
    res = api("get", f"/battle/{battle_id}")
    battle = res["data"].get("battle", {})
    player = battle.get("player", {})
    echo = player.get("echo_current", player.get("gauges", {}).get("echo", 0))
    
    check("Echo gauge increased after cast", echo > 0, f"Echo gauge is now {echo}")
    info(f"Generated echo: {echo}")


# ─── Test 5: Entaille Profonde (Apply Status) ───────────

def test_entaille_profonde(battle_id):
    header("TEST 5: Entaille Profonde (apply_status opcode)")

    section("Casting Entaille Profonde — applies Lacération")
    res = api("post", f"/battle/{battle_id}/turn?spell_code=entaille_profonde&item_id=couperet_noir")
    data = res["data"]

    check("POST /turn returns 200", res["status"] == 200, f"status={res['status']}")

    battle = data.get("battle", {})
    monster_statuses = get_statuses(battle, "monster")

    check("Monster has laceration status", "laceration" in monster_statuses,
          f"statuses: {list(monster_statuses.keys())}")

    if "laceration" in monster_statuses:
        lac = monster_statuses["laceration"]
        check("Laceration has remaining turns", lac.get("remaining", 0) > 0,
              f"remaining={lac.get('remaining')}")

    # Check logs for status application
    logs = battle.get("log", [])
    has_status_log = any("laceration" in str(l).lower() or "gains" in str(l).lower() for l in logs)
    check("Status application logged", has_status_log)

    # Check for bleed tick (laceration ticks on_turn_end)
    has_bleed = any("saignement" in str(l).lower() for l in logs)
    if has_bleed:
        ok("Laceration DOT ticked (end of turn)")
    else:
        info("No bleed tick yet (will tick next turn end)")

    print_logs(battle)


# ─── Test 6: Passive — Écho Lacérant (on_hit) ───────────

def test_passive_echo_lacerant(battle_id):
    header("TEST 6: Passive — Écho Lacérant (on_hit trigger)")

    section("Getting battle state to check")
    res = api("get", f"/battle/{battle_id}")
    battle = res["data"].get("battle", {})

    # Check previous logs for passive trigger
    logs = battle.get("log", [])
    has_passive = any("passive" in str(l).lower() or "écho lacérant" in str(l).lower() for l in logs)
    check("Passive triggered in logs", has_passive, "Écho Lacérant should fire on_hit when target has laceration")

    # Check echo gauge
    player = battle.get("player", {})
    echo = player.get("echo_current", player.get("gauges", {}).get("echo", 0))
    info(f"Player Echo gauge: {echo}")

    print_logs(battle, last_n=5)


# ─── Test 7: Status Tick — Laceration Bleed ──────────────

def test_status_tick(battle_id):
    header("TEST 7: Status Tick — Laceration Bleed (on_turn_end)")

    section("Getting battle state")
    res = api("get", f"/battle/{battle_id}")
    battle = res["data"].get("battle", {})

    logs = battle.get("log", [])
    bleed_ticks = [l for l in logs if "saignement" in str(l).lower()]
    check("Laceration bleed ticked at least once", len(bleed_ticks) > 0,
          f"found {len(bleed_ticks)} bleed tick(s)")

    for tick in bleed_ticks:
        info(f"Bleed: {tick}")


# ─── Test 8: Battle State (GET) ─────────────────────────

def test_battle_state(battle_id):
    header("TEST 8: GET Battle State")

    res = api("get", f"/battle/{battle_id}")
    check("GET /battle/{id} returns 200", res["status"] == 200)

    battle = res["data"].get("battle", {})
    check("State has player", "player" in battle)
    check("State has monster", "monster" in battle)
    check("State has log", "log" in battle)
    check("State has turn count", "turn" in battle)
    check("State has status field", "status" in battle)

    info(f"Turn: {battle.get('turn')}, Status: {battle.get('status')}")
    info(f"Player HP: {get_hp(battle, 'player')}, Monster HP: {get_hp(battle, 'monster')}")


# ─── Test 9: Fight to Death ─────────────────────────────

def test_fight_to_death():
    header("TEST 9: Fight to Death (full combat loop)")

    # Start fresh against Carapateur (1 HP)
    section("Starting battle vs Carapateur (1 HP)")
    res = start_fresh_battle(1, 1, 1)
    battle_id = res["data"].get("battle_id")

    check("Battle started", battle_id is not None, f"battle_id={battle_id}")

    if not battle_id:
        return

    section("One-shotting Carapateur with Coup-peret")
    res = api("post", f"/battle/{battle_id}/turn?spell_code=coup_peret&item_id=couperet_noir")
    battle = res["data"].get("battle", {})

    monster_hp = get_hp(battle, "monster")
    status = battle.get("status", "")

    check("Monster killed (HP=0)", monster_hp == 0, f"Monster HP={monster_hp}")
    check("Battle status = VICTORY", status.upper() in ["VICTORY", "FINISHED"],
          f"status='{status}'")

    # Check victory log
    logs = battle.get("log", [])
    has_victory = any("win" in str(l).lower() or "victory" in str(l).lower() for l in logs)
    check("Victory logged", has_victory)

    print_logs(battle)


# ─── Test 10: Abandon Battle ────────────────────────────

def test_abandon():
    header("TEST 10: Abandon Battle")

    section("Starting battle vs Krugs")
    res = start_fresh_battle(1, 4, 1)
    battle_id = res["data"].get("battle_id")

    check("Battle started", battle_id is not None)

    if not battle_id:
        return

    section(f"Abandoning battle #{battle_id}")
    res = api("post", f"/battle/{battle_id}/abandon")
    check("POST /abandon returns 200", res["status"] == 200, f"status={res['status']}")

    # Check status by fetching the battle state
    res_state = api("get", f"/battle/{battle_id}")
    battle = res_state["data"].get("battle", {})
    status = battle.get("status", "")
    check("Status = ABANDONED", status.upper() == "ABANDONED", f"status='{status}'")

    section("Trying to play on abandoned battle")
    res = api("post", f"/battle/{battle_id}/turn?spell_code=coup_peret&item_id=couperet_noir")
    check("Turn on abandoned battle rejected", res["status"] >= 400)


# ─── Test 11: Invalid Inputs ────────────────────────────

def test_invalid_inputs():
    header("TEST 11: Error Handling")

    section("Non-existent battle")
    res = api("get", "/battle/99999")
    check("404 on missing battle", res["status"] == 404)

    section("Invalid spell code")
    res = start_fresh_battle(1, 2, 1)
    bid = res["data"].get("battle_id")
    if bid:
        res = api("post", f"/battle/{bid}/turn?spell_code=fake_spell&item_id=couperet_noir")
        check("Error on invalid spell", res["status"] >= 400)

        section("Invalid item")
        res = api("post", f"/battle/{bid}/turn?spell_code=coup_peret&item_id=fake_item")
        check("Error on invalid item", res["status"] >= 400)

        # Cleanup
        api("post", f"/battle/{bid}/abandon")

    section("Invalid player / monster")
    res = api("post", "/battle/start?player_id=99999&monster_id=1&monster_level=1")
    check("Error on invalid player", res["status"] >= 400)

    res = api("post", "/battle/start?player_id=1&monster_id=99999&monster_level=1")
    check("Error on invalid monster", res["status"] >= 400)


# ─── Test 12: Execution (cannot_crit + high damage) ─────

def test_execution_spell():
    header("TEST 12: Exécution (cannot_crit, physical, high ratio)")

    section("Starting battle vs Lycans")
    res = start_fresh_battle(1, 2, 1)
    battle_id = res["data"].get("battle_id")

    if not battle_id:
        return

    section("Casting Exécution (200 + 160% AD, cannot crit)")
    res = api("post", f"/battle/{battle_id}/turn?spell_code=execution&item_id=couperet_noir")
    battle = res["data"].get("battle", {})

    check("Turn executed", res["status"] == 200)

    monster_hp = get_hp(battle, "monster")
    damage_dealt = 500 - monster_hp if monster_hp < 500 else 0

    # Expected: 200 + 120*1.6 = 392 raw, mitigated by 20 armor
    info(f"Damage dealt: {damage_dealt} (expected ~350-380 after armor)")

    logs = battle.get("log", [])
    has_crit = any("crit" in str(l).lower() for l in logs)
    check("No critical hit (cannot_crit flag)", not has_crit, "should never crit")

    print_logs(battle)

    # Cleanup
    api("post", f"/battle/{battle_id}/abandon")


# ─── Test 13: Tank Monster (high armor/MR mitigation) ───

def test_vs_tank():
    header("TEST 13: Tank Monster — Armor Mitigation (Krugs: 50 Armor, 50 MR)")

    section("Starting battle vs Krugs (900 HP, 80 AD, 50 ARM/MR)")
    res = start_fresh_battle(1, 4, 1)
    battle_id = res["data"].get("battle_id")

    if not battle_id:
        return

    section("Coup-peret vs 50 armor")
    res = api("post", f"/battle/{battle_id}/turn?spell_code=coup_peret&item_id=couperet_noir")
    battle = res["data"].get("battle", {})
    monster_hp = get_hp(battle, "monster")
    damage_dealt = 900 - monster_hp if monster_hp < 900 else 0

    # Raw = 140 + 120*0.9 = 248, after 50 armor -> ~220. Crits can go to ~370.
    info(f"Damage vs 50 armor: {damage_dealt} (expected ~200-230, crits ~370)")
    check("Damage mitigated by armor", damage_dealt < 450, f"damage={damage_dealt}")

    # Check monster attacks player too
    player_hp = get_hp(battle, "player")
    if player_hp < 800:
        ok(f"Monster attacked back: Player HP {player_hp}/800")
    else:
        info("Monster didn't attack (may have been stunned or HP check issue)")

    print_logs(battle)
    api("post", f"/battle/{battle_id}/abandon")


# ─── Test 14: Simulate Spell (no persistence) ───────────

def test_simulate():
    header("TEST 14: Simulate Spell (non-persistent)")

    res = api("post", "/battle/simulate?player_id=1&target_id=1&item_id=couperet_noir&spell_code=coup_peret")
    check("POST /simulate returns 200", res["status"] == 200, f"status={res['status']}")

    if res["status"] == 200:
        data = res["data"]
        info(f"Simulate result: {json.dumps(data, indent=2)[:200]}")


# ─── Test 15: Damage Calculation ─────────────────────────

def test_damage_calculation():
    header("TEST 15: Damage Calculation (no crit)")

    res = api("get", "/battle/damages-calculation?item_id=couperet_noir&spell_code=coup_peret&player_id=1&target_id=1&crit=false")
    check("GET /damages-calculation returns 200", res["status"] == 200, f"status={res['status']}")

    if res["status"] == 200:
        data = res["data"]
        info(f"Damage calc result: {json.dumps(data, indent=2)[:200]}")

    section("With crit = true")
    res = api("get", "/battle/damages-calculation?item_id=couperet_noir&spell_code=coup_peret&player_id=1&target_id=1&crit=true")
    check("Crit calculation returns 200", res["status"] == 200)

    if res["status"] == 200:
        data = res["data"]
        info(f"Crit damage: {json.dumps(data, indent=2)[:200]}")


# ─── Main ────────────────────────────────────────────────

def main():
    global BASE_URL

    if "--host" in sys.argv:
        idx = sys.argv.index("--host")
        BASE_URL = sys.argv[idx + 1]

    header("🎮 ECHOES COMBAT SYSTEM — FULL TEST SUITE")
    info(f"Target: {BASE_URL}")
    print()

    # Core flow
    test_server_alive()
    battle_id = test_start_battle()
    if battle_id:
        test_turn_coup_peret(battle_id)
        test_cooldown(battle_id)
        test_echo_gain(battle_id)
        test_entaille_profonde(battle_id)
        test_passive_echo_lacerant(battle_id)
        test_status_tick(battle_id)
        test_battle_state(battle_id)

    # Edge cases
    test_fight_to_death()
    test_abandon()
    test_invalid_inputs()

    # Damage verification
    test_execution_spell()
    test_vs_tank()

    # Non-persistent endpoints
    test_simulate()
    test_damage_calculation()

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
