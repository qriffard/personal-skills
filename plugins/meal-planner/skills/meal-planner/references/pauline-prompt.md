# Canonical user spec — Pauline's prompt

This is the source-of-truth user request that defines what the meal-planner skill is supposed to do for this household. When `Preferences.md`, `Schedule.md`, or `Family.md` are ambiguous, refer back to this prompt — it captures intent in the user's own words.

The vault files (`Preferences.md`, `Schedule.md`, `Family.md`) are the operational, machine-readable distillation of this prompt. Update both in lockstep when intent changes.

---

## Original prompt (French — sent 2026-05-07)

> **Sujet : Gestion et suivi d'un plan de repas familial optimisé**
>
> Bonjour Claude, je souhaite que tu deviennes mon coach cuisine et logistique pour ma famille. Voici le contexte complet de notre organisation actuelle pour que tu puisses m'assister cette semaine et les suivantes :
>
> **1. Profil de la famille :**
> - Famille de 4 : deux parents et deux enfants (1 de 6 ans et un bébé de 19 mois).
> - Objectifs : Cuisine 'Healthy', haute en protéines, gourmande et épicée.
> - Inspirations : Yotam Ottolenghi (saveurs, herbes, sauces) et Joshua McFadden — *Six Seasons* (respect des saisons, légumes grillés/rôtis).
> - Contrainte médicale : je suis allergique à l'ail (je sais adapter les recettes, mais garde-le en tête pour tes suggestions), et je ne mange pas d'agneau/mouton. Et maintenant en wheelchair pour 3 mois suite à un accident de vélo : mon mari gère la cuisine tout seul. Il ne faut donc des repas simples et faciles à préparer.
>
> **2. Logistique et emploi du temps :**
> - **Courses :** faites le vendredi matin pour la semaine suivante, et dimanche matin au farmer's market. J'ai donc besoin d'un meal plan et d'une liste de courses détaillée pour le **jeudi soir**.
> - **Cuisine :** session de 'Batch Prep' le week-end (samedi/dimanche) pour préparer les bases (céréales, découpes, pré-cuissons).
> - **Semaine :** cuisson 'minute' (max 15-20 min) le soir.
> - **Déjeuners (midi) :** on réutilise systématiquement les restes du dîner (lunchboxes).
> - **Lundi soir :** très peu de temps (repas assemblage uniquement).
> - **Dimanche midi :** cours de musique à 12h30 (besoin d'un repas prêt en 5 min).
> - **Vendredi soir :** utilisation de notre Gas Grill extérieur.
>
> **3. Ta mission immédiate :**
> Peux-tu accuser réception de ces informations ? Je te solliciterai pour les recettes détaillées de ces plats, pour ajuster le plan si besoin, ou pour générer la liste de courses de la semaine prochaine en restant sur cette même logique de 'bases communes' et de produits de saison.

---

## English distillation (canonical)

**Family of 4:** Quentin (cook), Pauline (planner / bedside collaborator), Charles (~6.5y, primary school), Léonie (~19 months, daycare).

**Style:** healthy · high-protein · gourmand · spicy.
**Inspirations (anchors):** Ottolenghi (flavors, herbs, sauces) + Joshua McFadden / *Six Seasons* (seasonal vegetables, grilled/roasted).

**Medical context (2026-05-07 → ~2026-08-07):** Pauline in a wheelchair following a bike accident; Quentin handles all cooking solo. Plans must stay simple and easy to execute.

**Hard constraints:**
- ⚠️ Garlic allergy (Pauline) — substitute with shallot / spring onion
- ❌ No lamb / sheep / goat
- Lunchboxes nut-free (school rule)

**Logistics — the schedule the planner must respect:**
- Plan + grocery list ready **Thursday evening** for Friday-morning shopping
- Friday morning: supermarket
- Sunday morning: Clement Street farmer's market
- Weekend: batch prep (grains, pre-cuts, pre-cooks)
- Mon-Fri evenings: max 15-20 min active cooking
- **Monday evening: assembly only (very little time)** — note: relaxed by user 2026-05-07 to "≤15 min cook acceptable" but assembly is preferred
- **Sunday lunch: ready in 5 min** — Charles' music lesson at 12:30
- **Friday dinner: gas grill (outdoor)**
- Midday lunches: always reuse the previous night's dinner

**Mission:** be the family's cooking-and-logistics coach. Generate the weekly plan + detailed grocery list, anchor on common bases + seasonal produce, adjust on request.

---

## How this prompt maps to the vault

| Prompt fact | Vault home |
|---|---|
| Style anchors (Ottolenghi + Six Seasons) | `Preferences.md` → General orientation → Style anchors |
| Wheelchair / solo-cook period | `Preferences.md` → Current operating mode |
| 15-20 min weeknight cap | `Schedule.md` → Hard rules (rule 1) |
| Sunday lunch ≤ 5 min, music lesson | `Schedule.md` → Hard rules (rule 2) |
| Friday gas grill | `Schedule.md` → Hard rules (rule 3) |
| Thursday evening plan delivery | `Schedule.md` → Cadence |
| Friday + Sunday shopping | `Schedule.md` → Cadence + Shopping split |
| Léonie eats like adults | `Preferences.md` → Kids — lunchbox rules |
| Spice level per kid | `Preferences.md` → Spice level — kid handling rule |
