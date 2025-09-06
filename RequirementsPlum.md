📄 Functional Requirements Specification – Plumastro Animal × Planet Scoring
1. Project Overview
We want to build a Python program that takes a client’s birth data (date, time, place, name, surname) and produces:
The birth chart data: list of planets and their zodiac signs.


A scoring table of animals vs planets (raw and weighted).


Additional analytics on the top-scoring animals.


The system must:
Compute each planet’s zodiac sign from the birth chart (using Flatlib).


Use a predefined Animal × Sign scoring table to retrieve the animal’s score for the sign of each planet.


Apply personality impact weights per planet.


Output results as structured CSV and JSON files.



2. Inputs
2.1. Client Data
Date of birth (YYYY-MM-DD)


Time of birth (HH:MM 24h)


Place of birth (city, country) OR direct latitude, longitude, timezone


First name and last name (optional, for metadata)


2.2. Animal × Sign Score Table
Format: JSON file with structure:

 {
  "animals": [
    {
      "ANIMAL": "Lynx",
      "ARIES": 92, "TAURUS": 40, "GEMINI": 75, ...
    },
    {
      "ANIMAL": "Panda",
      "ARIES": 30, "TAURUS": 85, "GEMINI": 50, ...
    }
  ]
}


Each animal has one score (0–100) per zodiac sign.


2.3. Planet Weights
Hardcoded dictionary:

 PLANET_WEIGHTS = {
    "Sun": 23, "Ascendant": 18, "Moon": 15,
    "Mercury": 10, "Venus": 10, "Mars": 10,
    "Jupiter": 8, "Saturn": 8, "Uranus": 6,
    "Neptune": 6, "Pluto": 6, "North Node": 6,
    "MC": 5
}



3. Processing Logic
Compute Planet → Sign mapping


Use flatlib with birth data (date, time, place/lat-lon-tz).


Supported planets/points:
 Sun, Ascendant, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, North Node, MC.


Build Animal × Planet Raw Table


For each planet P in sign S, retrieve score(animal, S) from JSON table.


Fill table: rows = animals, columns = planets.


Apply Planet Weights


For each planet column, multiply score by PLANET_WEIGHTS[P].


Produce weighted_scores table.


Compute Animal Totals


For each animal, compute the sum of weighted scores across all planets.


Sort animals from top score to lowest score.


Compute Top 3 Animal % Strength per Planet


Take the top 3 animals by total score.


For each of the 12 planets:


Find the maximum weighted score among all animals for that planet.


Divide each top-3 animal’s weighted score by that maximum → percentage (0–100%).


Output as a table: rows = 3 animals, columns = planets.


Compute Top 3 TRUE/FALSE Table


For each top-3 animal:


Rank that animal’s weighted scores across the 12 planets.


Mark TRUE for the top 6 planets (highest values for that animal).


Mark FALSE for the other 6 planets.


Output as a table: rows = 3 animals, columns = planets.



4. Outputs
The program must generate:
Birth Chart Data (JSON)


List of planets with their zodiac sign.


Example:

 {
  "Sun": "Virgo",
  "Ascendant": "Leo",
  "Moon": "Gemini",
  "Mercury": "Leo",
  "Venus": "Leo",
  "Mars": "Libra",
  "Jupiter": "Leo",
  "Saturn": "Aquarius",
  "Uranus": "Capricorn",
  "Neptune": "Capricorn",
  "Pluto": "Scorpio",
  "North Node": "Capricorn",
  "MC": "Taurus"
}


Raw Scores Table (CSV & JSON)


Shape: n_animals × n_planets


Weighted Scores Table (CSV & JSON)


Same shape, values = raw × weight.


Animal Totals Table (CSV & JSON)


List of animals with their total weighted score, sorted descending.


Top 3 % Strength Table (CSV & JSON)


Rows = top 3 animals, columns = planets.


Each cell = (weighted score of animal for planet) ÷ (max weighted score for planet among all animals) × 100%.


Top 3 TRUE/FALSE Table (CSV & JSON)


Rows = top 3 animals, columns = planets.


TRUE if the planet is in the top 6 % weighted scores for that animal, FALSE otherwise. (higher % are true, lower % are false)


Combined Results JSON (_result.json)
 Must include:


Planet → Sign mapping


Raw scores table


Weighted scores table


Animal totals


Top 3 % strength table


Top 3 TRUE/FALSE table



5. Command Line Interface (CLI)
python compute_scores.py \
  --scores_json scores_animaux.json \
  --date 1991-09-01 --time 22:45 \
  --place "Saint-Claude, Guadeloupe" \
  --out_prefix suzanna


6. Non-Functional Requirements
Language: Python 3.9+


Libraries: pandas, flatlib, json, argparse (+ geopy, timezonefinder if place used)


Cross-platform: must run on Windows, macOS, Linux


Error handling: must validate JSON structure, planet names, sign names


Extensibility: allow adding new planets/points in the future



👉 Avec cette spec, tu obtiendras non seulement les scores bruts et pondérés, mais aussi un classement clair des animaux, et deux vues puissantes sur le profil des 3 meilleurs animaux.
Veux-tu que je t’écrive maintenant un exemple concret de sortie (CSV + JSON) pour que Cursor sache exactement à quoi ressembleront les résultats ?

