# Ballon solaire – contacteur Legrand Drivia with Netatmo

Coupe le ballon d'eau chaude la nuit quand la production photovoltaïque prévue le lendemain suffit à le chauffer.
Le ballon chauffe alors en journée, avec l'énergie des panneaux.

## Principe

| Qui | Quoi |
|---|---|
| **App Home + Control** (planning) | allume le contacteur la nuit (ex. 23h–6h) **et** pendant la fenêtre solaire (ex. 11h–15h) |
| **Ce script**, chaque soir à 23h05 | regarde la production prévue le lendemain entre 11h et 15h ; si elle couvre le besoin → **force OFF** |
| **App**, le lendemain à 11h | rallume le contacteur : le ballon chauffe au soleil |

Le planning de l'app sert de **secours** : si le script, la machine ou Internet tombe, le ballon chauffe comme
avant, la nuit et en journée. Le pire cas est une chauffe sur le réseau, jamais une eau froide.

## Règle de décision

```
production prévue (kWh) = kWc × rayonnement sur les panneaux 11h–15h (kWh/m²) × rendement
soleil  ⇔  production prévue ≥ besoin du ballon + consommation de fond de la maison × 4 h
```

Valeurs par défaut (`config.json`) : 3 kWc plein sud incliné à 30°, rendement 0,8, ballon 4 kWh/jour,
maison 0,3 kW → seuil ≈ **5,2 kWh entre 11h et 15h**, soit ≈ 1,3 kW de moyenne.
En pratique : coupure presque tous les jours d'avril à septembre, rarement en hiver.

À ajuster : `pv.kwc`, `pv.inclinaison`, `pv.azimut` (0 = sud, −90 = est, 90 = ouest), `ballon.besoin_kwh`,
`fenetre_solaire`. Lancer `prevision` plusieurs jours de suite et comparer avec la production réelle.

## Mise en route

1. **App Home + Control** : contacteur en mode **ON/OFF** et planning « 23h–6h ON, 11h–15h ON, sinon OFF ».
2. **Créer une app** sur <https://dev.netatmo.com> → *My apps* → *Create*. Redirect URI : `http://localhost:8765/callback`.
3. `cp config.example.json config.json`, puis mettre ta latitude/longitude, tes panneaux, `client_id` et `client_secret`
   (ou les variables d'environnement `NETATMO_CLIENT_ID` / `NETATMO_CLIENT_SECRET`).
4. `python3 ballon_solaire.py auth`, puis accepter dans le navigateur (droits `read_magellan write_magellan`).
5. `python3 ballon_solaire.py list`, puis copier `home_id`, `module_id` et `bridge` dans `config.json`.
6. Tester : `status`, `off`, `on`, `prevision`, `nuit --essai`.
7. Tâche planifiée (machine allumée en permanence : Raspberry Pi, NAS, box…) :
   ```
   5 23 * * *  cd /chemin/legrand-ballon-solaire && python3 ballon_solaire.py nuit
   ```

`config.json`, `tokens.json` et le journal `ballon_solaire.log` restent locaux (`.gitignore`) : ils contiennent
tes secrets et ta position.

## À vérifier au premier essai

- Quand le script force OFF à 23h05, le planning de l'app reprend-il bien la main à 11h le lendemain ?
- Ton ballon a-t-il un thermostat qui le coupe une fois chaud ? (La consommation mesurée par le contacteur,
  visible dans l'app, montre combien de kWh il a vraiment pris au soleil.)
