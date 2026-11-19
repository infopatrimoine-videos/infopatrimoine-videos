# Specs du style PICTO. Chaque vidéo = scenes (texte parlé, même format que le kit bento) + panels (visuels).
# panel["at"] = [scène, phrase, délai_s] : le panneau entre (transition « whip ») au début de cette phrase.
# Types : hook, words, icon, duo, save, grid, trap, counter, flow, compare, recap (voir README_picto.md).
# Icônes : target, piggy, building, bust, padlock, hourglass, clock, warning, warning_red, pie, stick, coin:<texte>, coinw:<texte>
CTA = "Abonne-toi à Info Patrimoine : une nouvelle notion chaque jour."
PICTO = {}

def script(name):
    return "\n\n".join(" ".join(s["say"]) for s in PICTO[name]["scenes"])

def est_timing(name, cps=17.5):
    out = []; st = 0.0
    for S_ in PICTO[name]["scenes"]:
        B = []; t = 0.0
        for s in S_["say"]: B.append(t); t += len(s) / cps + 0.25
        out.append((st, t + 0.3, B)); st += t + 0.3
    return out

# Modèle : épargne salariale (19/11/2026), validé par Tomas.
PICTO["epargne_salariale"] = {
    "scenes": [
        {"type": "hook", "say": ["Ta prime : l'encaisser ou la placer ?", "Réponse en une minute."]},
        {"type": "step", "num": 1, "kicker": "C'EST QUOI ?", "say": ["Un : c'est quoi ?",
                 "L'intéressement : une prime facultative, liée à des objectifs.",
                 "La participation : une part des bénéfices, obligatoire dès cinquante salariés.",
                 "L'abondement : le complément de ton employeur."]},
        {"type": "step", "num": 2, "kicker": "OÙ LA PLACER ?", "say": ["Deux : où placer ta prime ?",
                 "Le PEE, plan d'épargne entreprise : bloqué cinq ans, sauf déblocage anticipé.",
                 "Le PERECO, plan retraite collectif, jusqu'à la retraite.",
                 "Piège : sans réponse dans le délai, ta prime est placée d'office, donc bloquée."]},
        {"type": "step", "num": 3, "kicker": "LES PLAFONDS", "say": ["Trois : les plafonds.",
                 "Ta prime : jusqu'à trente-six mille quarante-cinq euros par an.",
                 "L'abondement : trois mille huit cent quarante-quatre euros quatre-vingts maximum en PEE."]},
        {"type": "step", "num": 4, "kicker": "LA FISCALITÉ", "say": ["Quatre : la fiscalité.",
                 "Prime placée : zéro impôt sur le revenu.",
                 "Juste neuf virgule sept pour cent de prélèvements sociaux à l'entrée.",
                 "À la sortie, dix-huit virgule six pour cent sur les gains seulement."]},
        {"type": "step", "num": 5, "kicker": "L'EXEMPLE", "say": ["Cinq : l'exemple.",
                 "Trois mille euros de prime, tranche d'impôt à trente pour cent, abondement à cent pour cent.",
                 "Encaissée : mille huit cent soixante-dix euros vingt net d'impôt.",
                 "Placée : cinq mille quatre cent dix-huit euros investis, zéro impôt sur le revenu."]},
        {"type": "recap", "say": ["À retenir : si tu peux attendre, place ta prime. Et réponds dans le délai !", CTA]},
    ],
    "panels": [
        {"type": "hook", "ghost": "TA PRIME", "title": ["ÉPARGNE", "SALARIALE"], "sub": "ENCAISSER OU PLACER ?", "coin": "€"},
        {"at": [1, 0, 0], "type": "words", "words": ["C'EST", "QUOI ?"], "sizes": [190, 190]},
        {"at": [1, 1, 0], "type": "icon", "icon": "target", "accent": "€", "title": "INTÉRESSEMENT", "size": 120,
         "caption": "prime liée à des objectifs", "pill": "FACULTATIVE", "pill_at": 1.8},
        {"at": [1, 2, 0], "type": "icon", "icon": "pie", "icon_label": "BÉNÉFICES", "title": "PARTICIPATION", "size": 120,
         "caption": "une part des bénéfices", "people": 50, "pill": "OBLIGATOIRE DÈS 50 SALARIÉS", "pill_at": 2.4},
        {"at": [1, 3, 0], "type": "duo", "left": ["bust", "TOI"], "right": ["building", "EMPLOYEUR"], "coin_left": "€", "coin_right": "+",
         "title": "ABONDEMENT", "caption": "le complément de ton employeur"},
        {"at": [2, 0, 0], "type": "save", "words": ["OÙ PLACER", "TA PRIME ?"]},
        {"at": [2, 1, 0], "type": "grid", "title": "PEE", "caption": "plan d'épargne entreprise", "pill": "BLOQUÉ 5 ANS", "note": "sauf déblocage anticipé"},
        {"at": [2, 2, 0], "type": "icon", "icon": "hourglass", "figure": True, "title": "PERECO", "caption": "plan retraite collectif",
         "pill": "BLOQUÉ JUSQU'À LA RETRAITE", "pill_at": 1.2},
        {"at": [2, 3, 0], "type": "trap", "title": "PIÈGE", "cause": ["pas de réponse", "dans le délai"], "effect": ["PLACÉE D'OFFICE", "= BLOQUÉE"]},
        {"at": [3, 0, 0], "type": "words", "words": ["LES", "PLAFONDS"], "sizes": [120, 160]},
        {"at": [3, 1, 0], "type": "counter", "value": 36045, "unit": "€", "chart": True, "caption": "prime max par salarié et par an",
         "note": "intéressement ou participation"},
        {"at": [3, 2, 0], "type": "counter", "value": 3844.8, "dec": 2, "unit": "€", "accent": "+", "size": 170, "caption": "abondement max dans le PEE"},
        {"at": [4, 0, 0], "type": "flow", "words": ["LA", "FISCALITÉ"], "sizes": [110, 150], "steps": [[4, 1], [4, 2], [4, 3]],
         "top": {"old": "30 %", "new": "0 %", "label": "D'IMPÔT SUR LE REVENU"}, "inp": ["9,7 %", "À L'ENTRÉE"], "out": ["18,6 %", "À LA SORTIE"],
         "pill": "SUR LES GAINS SEULEMENT"},
        {"at": [5, 0, 0], "type": "compare", "words": ["L'EXEMPLE"], "sizes": [160], "steps": [[5, 1], [5, 2], [5, 3]],
         "coin": "3 000 €", "pills": ["TRANCHE 30 %", "ABONDEMENT 100 %"], "left": ["1 870,20 €", "ENCAISSÉE"], "right": ["5 418 €", "PLACÉE"],
         "heavier": "right", "caption": "zéro impôt sur le revenu"},
        {"at": [6, 0, 0], "type": "recap", "lines": [["piggy", "PLACE", "TA PRIME"], ["clock", "RÉPONDS", "DANS LE DÉLAI"]], "cta": [6, 1]},
    ],
}
