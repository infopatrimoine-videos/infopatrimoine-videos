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

BENTO["foncier"] = {
    "hook": {"title": "Micro-foncier", "sub": "ou régime réel : lequel choisir ?"},
    "recap": {"big": "−953 €", "sub": "d'impôts avec le régime réel"},
    "tiles": {
        "A1": {"label": "Plafond du micro-foncier", "value": 15000, "unit": "€", "note": "de loyers bruts par an"},
        "A2": {"label": "Part imposable", "label2": "en micro-foncier", "start": 100, "value": 70, "unit": "%", "note": "−30 % d'abattement"},
        "A3": {"label": "Le réel gagne", "label2": "si charges >", "value": 30, "unit": "%", "note": "des loyers"},
        "B": {"label": "Loyers 9 600 € · charges 4 900 €", "value": 953.44, "dec": 2, "unit": "€", "suffix": "gagnés", "ratio": 2218.40 / 3171.84,
              "note": "2 218 € au réel vs 3 172 € en micro (TMI 30 %)"},
        "C1": {"label": "3 ans"},
        "C2": {"label": "Déficit imputable", "value": 10700, "unit": "€", "fill": 0.8},
        "C3": {"title": "Option réel", "title2": "irrévocable", "tag": "3 ans",
               "cells": [[f"An {i}", "red" if i < 4 else "lime"] for i in range(1, 9)],
               "legend_red": "engagé au régime réel", "legend_lime": "retour au micro possible"},
    },
    "scenes": [
        {"type": "hook", "say": ["Logement loué vide : micro-foncier ou régime réel ?", "On fait le calcul."]},
        {"type": "step", "num": 1, "kicker": "LE MICRO-FONCIER", "say": ["Un : le micro-foncier.",
                 "Jusqu'à quinze mille euros de loyers par an, il s'applique tout seul.",
                 "Tu es imposé sur soixante-dix pour cent des loyers."]},
        {"type": "step", "num": 2, "kicker": "LE RÉGIME RÉEL", "say": ["Deux : le régime réel.",
                 "Tu déduis tes vraies charges, avec un déficit possible jusqu'à dix mille sept cents euros.",
                 "Mais l'option t'engage pour trois ans."]},
        {"type": "step", "num": 3, "kicker": "L'EXEMPLE", "say": ["Trois : l'exemple.",
                 "Neuf mille six cents euros de loyers, quatre mille neuf cents de charges, tranche à trente pour cent.",
                 "Au réel, tu paies neuf cent cinquante-trois euros de moins."]},
        {"type": "recap", "say": ["À retenir : le réel gagne quand tes charges dépassent trente pour cent des loyers.", CTA]},
    ],
    "reveal": {"A1": [1, 1, 0.0], "A2": [1, 2, 0.0], "C2": [2, 1, 0.0], "C1": [2, 2, 0.0], "C3": [2, 2, 0.3],
               "A3": [3, 0, 0.3], "B": [3, 1, 0.0]},
    "cam": [[0, 0, 0.0, "full"], [1, 1, 0.0, ["A1"]], [1, 2, 0.0, ["A2", "A3"]], [2, 1, 0.0, ["B", "C2"]], [2, 2, 0.0, ["C1", "C3"]],
            [3, 0, 0.0, ["A2", "A3"]], [3, 1, 0.0, ["B", "C2"]], [4, 0, 0.0, "full"]],
}

# Modèle « vidéo complète » (60-75 s) : 1 hook + 5 steps + recap, 1 100 à 1 300 caractères parlés.
BENTO["epargne_logement"] = {
    "hook": {"title": "PEL ou CEL ?", "sub": "l'épargne logement en 1 minute"},
    "recap": {"big": "3,20 %", "sub": "taux de prêt garanti (PEL 2026)"},
    "tiles": {
        "A1": {"label": "Plafond du PEL", "value": 61200, "unit": "€", "note": "225 € à l'ouverture, 540 € par an min."},
        "A2": {"label": "Taux du PEL 2026", "label2": "brut → net", "start": 2, "value": 1.4, "unit": "%", "dec": 2, "note": "−30 % d'impôt"},
        "A3": {"label": "Plafond du CEL", "label2": "argent disponible", "value": 15300, "unit": "€", "note": "1,25 % brut"},
        "B": {"label": "10 000 € pendant 1 an · PEL 2026", "value": 140, "unit": "€", "suffix": "net", "ratio": 140 / 170,
              "note": "87,50 € en CEL · 170 € sur un Livret A"},
        "C1": {"label": "4 ans"},
        "C2": {"label": "Livret A", "value": 170, "unit": "€", "fill": 1.0},
        "C3": {"title": "Retrait", "title2": "dans le PEL", "tag": "4 ans",
               "cells": [[f"An {i}", "red" if i < 5 else "lime"] for i in range(1, 9)],
               "legend_red": "retrait = plan fermé", "legend_lime": "échéance : prêt possible"},
    },
    "scenes": [
        {"type": "hook", "say": ["PEL ou CEL : l'épargne logement, ça vaut encore le coup ?", "On fait le tour en une minute."]},
        {"type": "step", "num": 1, "kicker": "C'EST QUOI ?", "say": ["Un : c'est quoi ?",
                 "Deux placements réglementés : c'est l'État qui fixe les règles.",
                 "Le principe : tu mets de l'argent de côté, puis tu empruntes à un taux connu d'avance pour ta résidence principale."]},
        {"type": "step", "num": 2, "kicker": "LE PEL", "say": ["Deux : le PEL.",
                 "Un seul par personne, jusqu'à soixante et un mille deux cents euros.",
                 "Et ton argent est bloqué quatre ans : un retrait avant ferme le plan."]},
        {"type": "step", "num": 3, "kicker": "LE CEL", "say": ["Trois : le CEL.",
                 "Là, ton argent reste disponible, jusqu'à quinze mille trois cents euros.",
                 "Il rapporte un virgule vingt-cinq pour cent brut."]},
        {"type": "step", "num": 4, "kicker": "CE QUE ÇA RAPPORTE", "say": ["Quatre : ce que ça rapporte.",
                 "Un PEL ouvert en deux mille vingt-six rapporte deux pour cent brut.",
                 "Mais les intérêts sont taxés à trente pour cent chaque année : il reste un virgule quarante pour cent net.",
                 "Son vrai atout : un prêt jusqu'à quatre-vingt-douze mille euros, à trois virgule vingt pour cent."]},
        {"type": "step", "num": 5, "kicker": "L'EXEMPLE", "say": ["Cinq : l'exemple.",
                 "Dix mille euros pendant un an : cent quarante euros net dans le PEL, quatre-vingt-sept euros cinquante dans le CEL.",
                 "Et cent soixante-dix euros sur un Livret A, sans impôt."]},
        {"type": "recap", "say": ["À retenir : le PEL rapporte moins qu'un Livret A. Garde-le pour un vrai projet de résidence principale.", CTA]},
    ],
    "reveal": {"A1": [2, 1, 0.3], "C1": [2, 3, 0.4], "C3": [2, 3, 1.0], "A3": [3, 1, 0.8], "A2": [4, 1, 0.0],
               "B": [5, 1, 0.0], "C2": [5, 2, 0.0]},
    "cam": [[0, 0, 0.0, "full"], [2, 1, 0.0, ["A1"]], [2, 3, 0.0, ["C1", "C3"]], [3, 1, 0.0, ["A2", "A3"]],
            [4, 1, 0.0, ["A2", "A3"]], [4, 3, 0.0, "full"], [5, 1, 0.0, ["B", "C2"]], [6, 0, 0.0, "full"]],
}
