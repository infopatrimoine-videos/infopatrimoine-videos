# Kit PICTO (style validé par Tomas le 19/11/2026)

Fond noir, pictogrammes blancs, gros mots en Inter Display Black, transitions « whip » avec flou de mouvement,
grain léger, sol en perspective. Un seul accent couleur : rouge, réservé au piège.

Fichiers : `picto.py` (moteur, ne pas modifier), `picto_specs.py` (specs ; `PICTO["epargne_salariale"]` = LE modèle),
`build_picto.py` (montage). Musique et mixage : `kit/bento/music.py` et `kit/bento/mixer.py` (à copier à côté).

## Spec
`PICTO["jour"] = {"scenes": [...], "panels": [...]}`
- `scenes` : même format que le kit bento (1 hook, 5 steps num 1-5 + kicker, 1 recap, champ `say`).
- `panels` : la suite des visuels. Chaque panneau (sauf `hook`) a `"at": [scène, phrase, délai]` et remplace le précédent
  par une transition whip au début de cette phrase. Prévoir 1 panneau par phrase importante (≈ 14-16 panneaux).

## Types de panneaux
| type | champs | usage |
|---|---|---|
| hook | ghost (mot en contour), title [1-2 lignes ≤ 11 car.], sub (≤ 26 car.), coin | 1re image = titre |
| words | words [1-3 mots], sizes | ouverture d'une step (« C'EST QUOI ? ») |
| icon | icon, title (≤ 14 car.), caption (≤ 34), pill (≤ 28), note (≤ 34), options : accent (glyphe de pièce), icon_label, figure (bonhomme), people (n ≤ 50), red, pill_at | définition, règle |
| duo | left [icône, label], right [icône, label], coin_left, coin_right, title, caption | qui verse quoi |
| save | words | « où placer ? », tirelire |
| grid | title, caption, pill, note | blocage / durée (60 cases + loupe + cadenas) |
| trap | title, cause [2 lignes], effect [ligne, ligne rouge] | le piège |
| counter | value, dec, unit, caption, note, chart (bool), accent, size | chiffre phare (compteur) |
| flow | words, steps [[s,p]×3], top {old, new, label}, inp [valeur, label], out [valeur, label], pill | fiscalité entrée / sortie |
| compare | words, steps [[s,p]×3], coin, pills [2], left [valeur, label], right [valeur, label], heavier, caption | exemple chiffré (balance) |
| recap | lines [[icône, ligne1, ligne2]×2], cta [scène, phrase] | à retenir + abonne-toi |

Icônes : target, piggy, building, bust, padlock, hourglass, clock, warning, warning_red, pie, stick, coin:<texte>, coinw:<texte>.
Valeurs à l'écran en notation française (« 1 870,20 € »), pas de date.

## Commandes
- Aperçu : `python3 picto.py stills jour x <durée_s ou voice.mp3> 0 5 10 ...` → stills.png
  (avec la voix : `python3 picto.py stills jour timing_jour.json voice.mp3 ...`)
- Montage : `python3 build_picto.py jour voice.mp3 final.mp4` (≈ 4 min, sortie ≈ 45 Mo : un fichier plus lourd ralentit la publication TikTok)
