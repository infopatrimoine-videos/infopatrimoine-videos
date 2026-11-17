# Bento specs. Tiles are fixed slots, each with its widget type:
#  A1 big (white, count-up + orange bars)   A2 pill (black, neon counter start->value)   A3 stat (white)
#  B compare (green, big number + ratio bar)   C1 clock (white, label)   C2 mini (white, number + orange bars)
#  C3 grid (black, 8 circles red ring / lime filled + 2-line legend)
# reveal: tile -> [scene, sentence, delay]  ;  cam: [scene, sentence, delay, [tiles] | "full"]
CTA = "Abonne-toi à Info Patrimoine : une nouvelle notion chaque jour."
BENTO = {}
BENTO["pea"] = {
    "hook": {"title": "Le PEA", "sub": "le meilleur plan pour la Bourse ?"},
    "recap": {"big": "−1 920 €", "sub": "d'impôts économisés avec le PEA"},
    "tiles": {
        "A1": {"label": "Plafond du PEA", "value": 150000, "unit": "€", "note": "1 plan par personne majeure"},
        "A2": {"label": "Impôt sur le revenu", "label2": "après 5 ans", "start": 12.8, "value": 0, "unit": "%", "dec": 1, "note": "▼ 12,8 points"},
        "A3": {"label": "Prélèvements", "label2": "sociaux", "value": 18.6, "unit": "%", "dec": 1, "note": "seulement"},
        "B": {"label": "15 000 € de gains · dans le PEA", "value": 2790, "unit": "€", "suffix": "d'impôts", "ratio": 2790 / 4710,
              "note": "vs 4 710 € sur un compte-titres"},
        "C1": {"label": "5 ans"},
        "C2": {"label": "Compte-titres", "value": 4710, "unit": "€", "fill": 1.0},
        "C3": {"title": "Règle", "title2": "des 5 ans", "tag": "Ouverture",
               "cells": [[f"An {i}", "red" if i < 5 else "lime"] for i in range(1, 9)],
               "legend_red": "retrait = plan fermé", "legend_lime": "retraits libres, 0 % d'IR"},
    },
    "scenes": [
        {"type": "hook", "say": ["Le PEA : le meilleur plan pour investir en Bourse ?", "Réponse en trente secondes."]},
        {"type": "step", "num": 1, "kicker": "LE PLAFOND", "say": ["Un : le plafond.", "Tu peux y verser jusqu'à cent cinquante mille euros."]},
        {"type": "step", "num": 2, "kicker": "LA RÈGLE DES 5 ANS", "say": ["Deux : la règle des cinq ans.", "Avant cinq ans, un retrait ferme ton plan.",
                 "Après, zéro impôt sur le revenu : seulement dix-huit virgule six pour cent de prélèvements sociaux."]},
        {"type": "step", "num": 3, "kicker": "L'EXEMPLE", "say": ["Trois : l'exemple.",
                 "Quinze mille euros de gains : deux mille sept cent quatre-vingt-dix euros d'impôts dans le PEA.",
                 "Contre quatre mille sept cent dix sur un compte-titres."]},
        {"type": "recap", "say": ["À retenir : mille neuf cent vingt euros d'économie.", CTA]},
    ],
    "reveal": {"A1": [1, 0, 0.9], "C3": [2, 0, 0.6], "C1": [2, 0, 1.0], "A2": [2, 2, 0.0], "A3": [2, 2, 2.2], "B": [3, 1, 0.0], "C2": [3, 2, 0.0]},
    "cam": [[0, 0, 0.0, "full"], [1, 0, 0.0, ["A1"]], [2, 0, 0.0, ["C1", "C3"]], [2, 2, 0.0, ["A2", "A3"]], [3, 1, 0.0, ["B", "C2"]], [4, 0, 0.0, "full"]],
}
def script(name):
    return "\n\n".join(" ".join(s["say"]) for s in BENTO[name]["scenes"])
