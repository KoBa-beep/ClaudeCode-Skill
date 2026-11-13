#!/usr/bin/env python3
"""Ballon solaire : coupe le ballon d'eau chaude la nuit quand le soleil du lendemain suffit.

Contacteur connecté Legrand Drivia with Netatmo (type NLPO), piloté par l'API Netatmo Connect.
Prévision : Open-Meteo (gratuit, sans clé), rayonnement sur le plan des panneaux.

Principe (le planning de l'app Home + Control fait le reste) :
  - l'app allume le ballon la nuit ET pendant la fenêtre solaire (planning de secours) ;
  - chaque soir, juste après l'allumage de nuit, ce script regarde la production prévue
    du lendemain dans la fenêtre solaire ; si elle couvre le besoin du ballon, il force OFF ;
  - le lendemain, le planning rallume le ballon en début de fenêtre solaire.
  Si le script ou la machine tombe en panne, le ballon chauffe comme avant : jamais d'eau froide.

Commandes :
  python3 ballon_solaire.py auth            # autoriser l'app sur ton compte (une seule fois)
  python3 ballon_solaire.py list            # trouver home_id / module_id / bridge du contacteur
  python3 ballon_solaire.py prevision       # voir la prévision et la décision, sans rien commander
  python3 ballon_solaire.py nuit            # tâche du soir : force OFF si demain est ensoleillé
  python3 ballon_solaire.py status|on|off   # état / commande manuelle

Seule la bibliothèque standard de Python 3.8+ est utilisée.
"""

import argparse
import datetime as dt
import http.server
import json
import logging
import os
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ICI = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(ICI, "config.json")
TOKENS = os.path.join(ICI, "tokens.json")
JOURNAL = os.path.join(ICI, "ballon_solaire.log")

NETATMO = "https://api.netatmo.com"
SCOPES = "read_magellan write_magellan"
OPEN_METEO = "https://api.open-meteo.com/v1/forecast"

log = logging.getLogger("ballon")


# ---------------------------------------------------------------- outils

def charger(chemin, defaut=None):
    try:
        with open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        if defaut is not None:
            return defaut
        sys.exit(f"Fichier manquant : {chemin} (copie config.example.json en config.json)")


def sauver(chemin, data):
    tmp = chemin + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.chmod(tmp, 0o600)
    os.replace(tmp, chemin)  # remplacement atomique : jamais de fichier de jetons à moitié écrit


def http(methode, url, params=None, json_body=None, headers=None, form=None):
    headers = dict(headers or {})
    data = None
    if params:
        url += "?" + urllib.parse.urlencode(params)
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if json_body is not None:
        data = json.dumps(json_body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=methode)
    for essai in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            corps = e.read().decode(errors="replace")
            if e.code >= 500 and essai < 2:
                time.sleep(5 * (essai + 1))
                continue
            raise RuntimeError(f"HTTP {e.code} sur {url.split('?')[0]} : {corps}") from None
        except urllib.error.URLError:
            if essai < 2:
                time.sleep(5 * (essai + 1))
                continue
            raise


# ---------------------------------------------------------------- Netatmo

def secrets_app(cfg):
    cid = os.environ.get("NETATMO_CLIENT_ID") or cfg.get("client_id")
    csec = os.environ.get("NETATMO_CLIENT_SECRET") or cfg.get("client_secret")
    if not cid or not csec:
        sys.exit("client_id / client_secret absents (config.json ou variables NETATMO_CLIENT_ID / NETATMO_CLIENT_SECRET)")
    return cid, csec


def jeton(cfg):
    """Renvoie un access_token valide, en le rafraîchissant si besoin."""
    tok = charger(TOKENS, {})
    if not tok.get("refresh_token"):
        sys.exit("Pas encore autorisé : lance d'abord  python3 ballon_solaire.py auth")
    if tok.get("expires_at", 0) - 120 > time.time():
        return tok["access_token"]
    cid, csec = secrets_app(cfg)
    rep = http("POST", f"{NETATMO}/oauth2/token", form={
        "grant_type": "refresh_token", "refresh_token": tok["refresh_token"],
        "client_id": cid, "client_secret": csec})
    # Netatmo fait tourner le refresh_token : l'ancien est invalidé immédiatement.
    tok = {"access_token": rep["access_token"], "refresh_token": rep["refresh_token"],
           "expires_at": time.time() + rep.get("expires_in", 10800)}
    sauver(TOKENS, tok)
    return tok["access_token"]


def api(cfg, methode, chemin, **kw):
    kw.setdefault("headers", {})["Authorization"] = "Bearer " + jeton(cfg)
    return http(methode, NETATMO + chemin, **kw)


def contacteur(cfg):
    c = cfg.get("contacteur") or {}
    if not all(c.get(k) for k in ("home_id", "module_id", "bridge")):
        sys.exit("Renseigne contacteur.home_id / module_id / bridge dans config.json (voir la commande list)")
    return c


def commander(cfg, allume):
    c = contacteur(cfg)
    rep = api(cfg, "POST", "/api/setstate", json_body={"home": {
        "id": c["home_id"],
        "modules": [{"id": c["module_id"], "on": bool(allume), "bridge": c["bridge"]}]}})
    erreurs = (rep.get("body") or {}).get("errors") if isinstance(rep.get("body"), dict) else None
    if rep.get("status") != "ok" or erreurs:
        raise RuntimeError(f"setstate refusé : {rep}")
    log.info("Contacteur %s", "ALLUMÉ" if allume else "COUPÉ")


def etat(cfg):
    c = contacteur(cfg)
    rep = api(cfg, "GET", "/api/homestatus", params={"home_id": c["home_id"]})
    for m in rep["body"]["home"].get("modules", []):
        if m.get("id") == c["module_id"]:
            return m
    raise RuntimeError("Contacteur introuvable dans homestatus")


# ---------------------------------------------------------------- prévision

def prevision(cfg, jour):
    """Production PV prévue (kWh) dans la fenêtre solaire du jour donné."""
    pv = cfg["pv"]
    debut, fin = cfg["fenetre_solaire"]
    rep = http("GET", OPEN_METEO, params={
        "latitude": cfg["latitude"], "longitude": cfg["longitude"],
        "hourly": "global_tilted_irradiance,cloud_cover",
        "tilt": pv["inclinaison"], "azimuth": pv["azimut"],
        "timezone": cfg.get("timezone", "Europe/Paris"),
        "start_date": jour.isoformat(), "end_date": jour.isoformat()})
    h = rep["hourly"]
    gti_wh, nuages = 0.0, []
    for t, g, n in zip(h["time"], h["global_tilted_irradiance"], h["cloud_cover"]):
        heure = int(t[11:13])
        # Open-Meteo : valeur à HH = moyenne de l'heure précédente (HH-1 -> HH)
        if debut < heure <= fin and g is not None:
            gti_wh += g
            nuages.append(n)
    kwh_pv = pv["kwc"] * gti_wh / 1000 * pv["rendement"]
    heures = fin - debut
    besoin = cfg["ballon"]["besoin_kwh"] + cfg["maison_kw"] * heures
    return {
        "jour": jour.isoformat(), "fenetre": f"{debut}h-{fin}h",
        "rayonnement_kwh_m2": round(gti_wh / 1000, 2),
        "production_kwh": round(kwh_pv, 1),
        "puissance_moy_kw": round(kwh_pv / heures, 2),
        "nuages_moy_pct": round(sum(nuages) / len(nuages)) if nuages else None,
        "besoin_kwh": round(besoin, 1),
        "soleil": kwh_pv >= besoin,
    }


def jour_solaire(maintenant=None):
    """Le soir, on décide pour demain ; après minuit, pour aujourd'hui."""
    maintenant = maintenant or dt.datetime.now()
    return maintenant.date() + dt.timedelta(days=1 if maintenant.hour >= 12 else 0)


def resume(p):
    verdict = "SOLEIL -> coupure de nuit" if p["soleil"] else "pas assez -> chauffe de nuit"
    return (f"{p['jour']} {p['fenetre']} : {p['production_kwh']} kWh PV prévus "
            f"(moy. {p['puissance_moy_kw']} kW, nuages {p['nuages_moy_pct']} %) "
            f"pour un besoin de {p['besoin_kwh']} kWh => {verdict}")


# ---------------------------------------------------------------- commandes

def cmd_auth(cfg, args):
    cid, csec = secrets_app(cfg)
    redirect = cfg.get("redirect_uri", "http://localhost:8765/callback")
    etat_oauth = secrets.token_urlsafe(16)
    url = f"{NETATMO}/oauth2/authorize?" + urllib.parse.urlencode({
        "client_id": cid, "redirect_uri": redirect, "scope": SCOPES, "state": etat_oauth})
    print("1) Ouvre cette adresse dans ton navigateur et accepte :\n\n   " + url + "\n")
    code = None
    u = urllib.parse.urlparse(redirect)
    if u.hostname in ("localhost", "127.0.0.1") and not args.manuel:
        recu = {}

        class H(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                recu.update({k: v[0] for k, v in q.items()})
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write("<h2>C'est bon, tu peux fermer cet onglet.</h2>".encode())

            def log_message(self, *a):
                pass

        print(f"2) J'attends le retour sur {redirect} ...")
        srv = http.server.HTTPServer((u.hostname, u.port or 80), H)
        while "code" not in recu and "error" not in recu:
            srv.handle_request()
        if recu.get("state") != etat_oauth:
            sys.exit("Réponse inattendue (state différent), recommence.")
        code = recu.get("code") or sys.exit(f"Refusé : {recu}")
    else:
        retour = input("2) Colle ici l'adresse complète de la page où tu as été redirigé : ").strip()
        q = urllib.parse.parse_qs(urllib.parse.urlparse(retour).query)
        if q.get("state", [""])[0] != etat_oauth:
            sys.exit("Réponse inattendue (state différent), recommence.")
        code = q.get("code", [None])[0] or sys.exit("Pas de code dans l'adresse.")
    rep = http("POST", f"{NETATMO}/oauth2/token", form={
        "grant_type": "authorization_code", "client_id": cid, "client_secret": csec,
        "code": code, "redirect_uri": redirect, "scope": SCOPES})
    sauver(TOKENS, {"access_token": rep["access_token"], "refresh_token": rep["refresh_token"],
                    "expires_at": time.time() + rep.get("expires_in", 10800)})
    print(f"OK, jetons enregistrés dans {TOKENS}. Lance maintenant : python3 ballon_solaire.py list")


def cmd_list(cfg, args):
    rep = api(cfg, "GET", "/api/homesdata")
    trouve = False
    for home in rep["body"]["homes"]:
        for m in home.get("modules", []):
            if m.get("type") == "NLPO" or args.tout:
                trouve = trouve or m.get("type") == "NLPO"
                print(json.dumps({"home_id": home["id"], "maison": home.get("name"),
                                  "module_id": m["id"], "nom": m.get("name"), "type": m.get("type"),
                                  "bridge": m.get("bridge")}, ensure_ascii=False))
    if not trouve:
        print("Aucun contacteur NLPO trouvé (essaie --tout pour voir tous les modules).")
    else:
        print("\nCopie home_id, module_id et bridge du ballon dans la section \"contacteur\" de config.json.")


def cmd_prevision(cfg, args):
    jour = dt.date.fromisoformat(args.jour) if args.jour else jour_solaire()
    p = prevision(cfg, jour)
    print(resume(p))
    if args.json:
        print(json.dumps(p, indent=2, ensure_ascii=False))


def cmd_nuit(cfg, args):
    try:
        p = prevision(cfg, jour_solaire())
    except Exception as e:  # pas de prévision = on ne touche à rien, le ballon chauffe
        log.error("Prévision indisponible (%s) : on laisse le ballon chauffer", e)
        return 1
    log.info(resume(p))
    if p["soleil"]:
        if args.essai:
            log.info("[essai] on aurait coupé le contacteur")
        else:
            commander(cfg, False)
    return 0


def cmd_status(cfg, args):
    print(json.dumps(etat(cfg), indent=2, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("auth"); a.add_argument("--manuel", action="store_true", help="coller l'URL de retour à la main")
    a = sub.add_parser("list"); a.add_argument("--tout", action="store_true")
    a = sub.add_parser("prevision"); a.add_argument("--jour", help="AAAA-MM-JJ"); a.add_argument("--json", action="store_true")
    a = sub.add_parser("nuit"); a.add_argument("--essai", action="store_true", help="décide sans commander")
    sub.add_parser("status"); sub.add_parser("on"); sub.add_parser("off")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(JOURNAL, encoding="utf-8"), logging.StreamHandler()])
    cfg = charger(CONFIG)
    actions = {"auth": cmd_auth, "list": cmd_list, "prevision": cmd_prevision, "nuit": cmd_nuit,
               "status": cmd_status,
               "on": lambda c, a: commander(c, True), "off": lambda c, a: commander(c, False)}
    try:
        sys.exit(actions[args.cmd](cfg, args) or 0)
    except RuntimeError as e:
        log.error("%s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
