#!/usr/bin/env python3
"""
Script réutilisable pour générer des livres astrologiques (version sans emojis)
Usage: python generate_book_simple.py
"""

import os
import json
import shutil
import random
import sys
import io
from datetime import datetime
from aspects_patterns_generator import AspectsPatternsGenerator


def run_plumatotm_analysis(input_data):
    """Lance l'analyse PLUMATOTM en utilisant la même logique que l'API"""
    
    try:
        # Importer et utiliser PLUMATOTM
        from plumatotm_core import BirthChartAnalyzer
        
        # Initialiser l'analyseur
        analyzer = BirthChartAnalyzer(
            scores_csv_path="plumatotm_raw_scores_trad.csv",
            weights_csv_path="plumatotm_planets_weights.csv", 
            multipliers_csv_path="plumatotm_planets_multiplier.csv",
            translations_csv_path="plumatotm_raw_scores_trad.csv"
        )
        
        # Utiliser la méthode qui génère tous les fichiers (même que l'API)
        result = analyzer.run_analysis(
            input_data['date_naissance'],
            input_data['heure_naissance'],
            input_data['lat'],
            input_data['lon'],
            user_name=input_data.get('prenom', '')
        )
        
        # Générer PLANETARY POSITIONS SUMMARY comme dans main.py
        from main import generate_planetary_positions_summary
        planetary_summary = generate_planetary_positions_summary()
        print(f"DEBUG: Generated {len(planetary_summary)} planetary positions")
        
        # Sauvegarder dans result.json pour cohérence avec l'API
        if planetary_summary:
            with open("outputs/result.json", 'r', encoding='utf-8') as f:
                result_data = json.load(f)
            result_data['PLANETARY POSITIONS SUMMARY'] = planetary_summary
            with open("outputs/result.json", 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
            print("DEBUG: PLANETARY POSITIONS SUMMARY saved to result.json")
        else:
            print("DEBUG: No planetary summary generated")
        
        print("Analyse PLUMATOTM terminee avec succes")
        return True
        
    except Exception as e:
        print(f"Erreur lors de l'analyse PLUMATOTM: {e}")
        return False

def get_animal_totem_data():
    """Récupère les données des animaux totems (top 3) avec leurs noms français et scores"""
    try:
        # Charger les données des animaux totems
        with open("outputs/top3_percentage_strength.json", 'r', encoding='utf-8') as f:
            animal_scores = json.load(f)
        
        # Charger les traductions des animaux
        with open("plumatotm_raw_scores_trad.csv", 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Parser le CSV pour créer un dictionnaire de traductions
        animal_translations = {}
        for line in lines[1:]:  # Skip header
            parts = line.strip().split(',')
            if len(parts) >= 4:
                animal_en = parts[0]
                animal_fr = parts[1]
                determinant = parts[2]
                animal_translations[animal_en] = {
                    'french_name': animal_fr,
                    'determinant': determinant
                }
        
        # Récupérer les top 3 animaux
        top_animals = []
        for animal_en in animal_scores.keys():
            if animal_en in animal_translations:
                animal_data = animal_scores[animal_en]
                top_animals.append({
                    'english_name': animal_en,
                    'french_name': animal_translations[animal_en]['french_name'],
                    'determinant': animal_translations[animal_en]['determinant'],
                    'overall_strength_adjust': animal_data.get('OVERALL_STRENGTH_ADJUST', 0),
                    'scores': animal_data
                })
        
        # Trier par score décroissant
        top_animals.sort(key=lambda x: x['overall_strength_adjust'], reverse=True)
        
        return top_animals[:3]  # Top 3 seulement
        
    except Exception as e:
        print(f"Erreur lors de la récupération des données des animaux totems: {e}")
        return []

def get_top_planets_for_animal(animal_name, top3_data):
    """Récupère les top 8 planètes pour un animal donné"""
    try:
        # Trouver l'animal dans les données
        animal_data = None
        for animal in top3_data:
            if animal['english_name'] == animal_name:
                animal_data = animal
                break
        
        if not animal_data:
            return []
        
        # Extraire les scores des planètes (exclure les métadonnées)
        planet_scores = {}
        for key, value in animal_data['scores'].items():
            if key not in ['OVERALL_STRENGTH', 'OVERALL_STRENGTH_ADJUST']:
                planet_scores[key] = value
        
        # Définir l'ordre de priorité des planètes pour le tie-breaking
        planet_priority = {
            "Sun": 1, "Moon": 2, "Ascendant": 3, "Mercury": 4, "Venus": 5,
            "Mars": 6, "Jupiter": 7, "Saturn": 8, "Uranus": 9, "Neptune": 10,
            "Pluto": 11, "North Node": 12, "MC": 13
        }
        
        # Trier par score décroissant, puis par priorité croissante pour les égalités
        sorted_planets = sorted(
            planet_scores.items(), 
            key=lambda x: (-x[1], planet_priority.get(x[0], 999))  # Score décroissant, priorité croissante
        )[:8]
        
        # Charger les positions planétaires pour ajouter signe et maison
        with open("outputs/result.json", 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        birth_chart = result_data.get('birth_chart', {})
        planet_signs = birth_chart.get('planet_signs', {})
        planet_houses = birth_chart.get('planet_houses', {})
        
        # Traductions des planètes
        planet_translations = {
            "Sun": "Soleil", "Moon": "Lune", "Mercury": "Mercure", "Venus": "Vénus",
            "Mars": "Mars", "Jupiter": "Jupiter", "Saturn": "Saturne", "Uranus": "Uranus",
            "Neptune": "Neptune", "Pluto": "Pluton", "North Node": "Nœud Nord",
            "Ascendant": "Ascendant", "MC": "MC"
        }
        
        # Traductions des signes
        sign_translations = {
            "ARIES": "Bélier", "TAURUS": "Taureau", "GEMINI": "Gémeaux", "CANCER": "Cancer",
            "LEO": "Lion", "VIRGO": "Vierge", "LIBRA": "Balance", "SCORPIO": "Scorpion",
            "SAGITTARIUS": "Sagittaire", "CAPRICORN": "Capricorne", "AQUARIUS": "Verseau", "PISCES": "Poissons"
        }
        
        # Formater les résultats
        formatted_planets = []
        for planet_en, score in sorted_planets:
            planet_fr = planet_translations.get(planet_en, planet_en)
            sign_en = planet_signs.get(planet_en, '')
            sign_fr = sign_translations.get(sign_en, sign_en)
            house = planet_houses.get(planet_en, '')
            
            formatted_planets.append({
                'planet': planet_fr,
                'sign': sign_fr,
                'house': house,
                'score': score
            })
        
        return formatted_planets
        
    except Exception as e:
        print(f"Erreur lors de la récupération des planètes pour {animal_name}: {e}")
        return []

def generate_planetary_positions_paragraphs():
    """Génère les paragraphes de positions planétaires à partir des données de l'API"""
    try:
        # Charger les données de l'API (même structure que l'API)
        with open("outputs/result.json", 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        planetary_summary = result_data.get('PLANETARY POSITIONS SUMMARY', [])
        if not planetary_summary:
            return ""
        
        # Grouper les planètes selon les 3 paragraphes demandés
        paragraph1_planets = ["Soleil", "Ascendant", "Lune"]
        paragraph2_planets = ["Mercure", "Vénus", "Mars", "Jupiter", "Saturne", "Uranus", "Neptune", "Pluton"]
        paragraph3_planets = ["MC", "Nœud Nord"]
        
        paragraphs = []
        
        # Paragraphe 1
        para1_lines = []
        for planet_data in planetary_summary:
            planet_name = planet_data.get('PLANETE', '')
            if planet_name in paragraph1_planets:
                angle = planet_data.get('ANGLE', '')
                sign = planet_data.get('SIGNE', '')
                maison_explanation = planet_data.get('MAISON EXPLICATION', '')
                maison_num = planet_data.get('MAISON', '')
                para1_lines.append(f"{planet_name} en {angle} {sign} dans la {maison_num}")
        
        if para1_lines:
            paragraphs.append('\n'.join(para1_lines))
        
        # Paragraphe 2
        para2_lines = []
        for planet_data in planetary_summary:
            planet_name = planet_data.get('PLANETE', '')
            if planet_name in paragraph2_planets:
                angle = planet_data.get('ANGLE', '')
                sign = planet_data.get('SIGNE', '')
                maison_explanation = planet_data.get('MAISON EXPLICATION', '')
                maison_num = planet_data.get('MAISON', '')
                para2_lines.append(f"{planet_name} en {angle} {sign} dans la {maison_num}")
        
        if para2_lines:
            paragraphs.append('\n'.join(para2_lines))
        
        # Paragraphe 3
        para3_lines = []
        # Process planets in the correct order: MC first, then Nœud Nord
        for planet_name in paragraph3_planets:
            for planet_data in planetary_summary:
                if planet_data.get('PLANETE', '') == planet_name:
                    angle = planet_data.get('ANGLE', '')
                    sign = planet_data.get('SIGNE', '')
                    maison_explanation = planet_data.get('MAISON EXPLICATION', '')
                    maison_num = planet_data.get('MAISON', '')
                    para3_lines.append(f"{planet_name} en {angle} {sign} dans la {maison_num}")
                    break
        
        if para3_lines:
            paragraphs.append('\n'.join(para3_lines))
        
        return '\n\n\n\n\n'.join(paragraphs)
        
    except Exception as e:
        print(f"Erreur lors de la génération des paragraphes planétaires: {e}")
        return ""

def generate_planetary_positions_content():
    """Génère le contenu des positions planétaires pour intégration dans le prompt"""
    try:
        # Charger les données de l'API
        with open("outputs/result.json", 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        planetary_summary = result_data.get('PLANETARY POSITIONS SUMMARY', [])
        if not planetary_summary:
            print("Aucune donnée planétaire trouvée")
            return ""
        
        # Dictionnaire de traduction des signes vers l'anglais
        sign_translations = {
            "Bélier": "Aries",
            "Taureau": "Taurus", 
            "Gémeaux": "Gemini",
            "Cancer": "Cancer",
            "Lion": "Leo",
            "Vierge": "Virgo",
            "Balance": "Libra",
            "Scorpion": "Scorpio",
            "Sagittaire": "Sagittarius",
            "Capricorne": "Capricorn",
            "Verseau": "Aquarius",
            "Poissons": "Pisces"
        }
        
        # Ordre des planètes selon le format demandé
        planet_order = [
            "Soleil", "Lune", "Mercure", "Vénus", "Mars", "Jupiter", 
            "Saturne", "Uranus", "Neptune", "Pluton", "Nœud Nord", 
            "Ascendant", "MC"
        ]
        
        # Créer le contenu
        content_lines = [
            "PLANETARY POSITIONS:",
            "You can think of the planets as symbolizing core parts of the human personality, and the signs as different colors of consciousness through which they filter.",
            "",
            ""
        ]
        
        # Ajouter chaque planète
        for planet_name in planet_order:
            # Trouver la planète dans les données
            planet_data = None
            for data in planetary_summary:
                if data.get('PLANETE') == planet_name:
                    planet_data = data
                    break
            
            if planet_data:
                # Traduire le nom de la planète en anglais
                planet_english = {
                    "Soleil": "Sun",
                    "Lune": "Moon",
                    "Mercure": "Mercury",
                    "Vénus": "Venus",
                    "Mars": "Mars",
                    "Jupiter": "Jupiter",
                    "Saturne": "Saturn",
                    "Uranus": "Uranus",
                    "Neptune": "Neptune",
                    "Pluton": "Pluto",
                    "Nœud Nord": "North Node",
                    "Ascendant": "Ascendant",
                    "MC": "MC"
                }.get(planet_name, planet_name)
                
                # Obtenir les données
                angle = planet_data.get('ANGLE', '0°00\'')
                sign_fr = planet_data.get('SIGNE', '')
                sign_en = sign_translations.get(sign_fr, sign_fr)
                
                # Ajouter au contenu
                content_lines.extend([
                    planet_english,
                    "in",
                    angle.replace('°', '° ').replace("'", "'"),
                    sign_en,
                    ""
                ])
        
        return '\n'.join(content_lines)
        
    except Exception as e:
        print(f"Erreur lors de la génération du contenu des positions planétaires: {e}")
        return ""

def generate_chatgpt_prompt(input_data, aspects_patterns_data):
    """Génère le prompt ChatGPT personnalisé"""
    
    # Configuration des longueurs de texte (1 mot = 6 caractères)
    TEXT_LENGTHS = {
        "MEGA_SHORT": "60-80 mots",
        "V_SHORT": "100-140 mots",
        "SHORT": "155-190 mots",
        "MID": "180-220 mots",
        "LONG": "240-270 mots",
        "V_LONG": "300-330 mots"
    }
    
    # Dictionnaires de traduction
    planet_translations = {
        "Sun": "Soleil",
        "Moon": "Lune", 
        "Mercury": "Mercure",
        "Venus": "Vénus",
        "Mars": "Mars",
        "Jupiter": "Jupiter",
        "Saturn": "Saturne",
        "Uranus": "Uranus",
        "Neptune": "Neptune",
        "Pluto": "Pluton",
        "North Node": "Nœud Nord",
        "Ascendant": "Ascendant",
        "MC": "MC"
    }
    
    sign_translations = {
        "Aries": "Bélier",
        "Taurus": "Taureau", 
        "Gemini": "Gémeaux",
        "Cancer": "Cancer",
        "Leo": "Lion",
        "Virgo": "Vierge",
        "Libra": "Balance",
        "Scorpio": "Scorpion",
        "Sagittarius": "Sagittaire",
        "Capricorn": "Capricorne",
        "Aquarius": "Verseau",
        "Pisces": "Poissons"
    }
    
    aspect_translations = {
        "Conjunction": "Conjonction",
        "Opposition": "Opposition",
        "Square": "Carré",
        "Trine": "Trigone",
        "Sextile": "Sextile",
        "Quincunx": "Quinconce",
        "Semisextile": "Semi-sextile",
        "Semisquare": "Semi-carré",
        "Quintile": "Quintile",
        "Sesquiquintile": "Sesqui-quintile",
        "Biquintile": "Bi-quintile",
        "Semiquintile": "Semi-quintile"
    }
    
    pattern_translations = {
        "T-Square": "T-Carré",
        "Grand Trine": "Grand Trigone",
        "Grand Square": "Grand Carré", 
        "Stellium": "Stellium",
        "Multiple Aspect": "Aspect Multiple",
        "Multiple Planet Square": "Carré Multiple",
        "Yod": "Yod"
    }
    
    # Charger les résultats d'analyse
    with open("outputs/result.json", 'r', encoding='utf-8') as f:
        result_data = json.load(f)
    with open("outputs/birth_chart.json", 'r', encoding='utf-8') as f:
        birth_chart_data = json.load(f)
    
    # L'animal totem sera récupéré plus tard avec les autres données
    french_birth_chart = birth_chart_data.get('french_birth_chart', {})
    
    # Générer un nom d'astrologue aléatoire
    astrologue_names = ["Jade", "Alba"]
    astrologue_name = random.choice(astrologue_names)
    
    # Formater le thème de naissance français complet
    french_chart_text = "{\n"
    for planet, position in french_birth_chart.items():
        french_chart_text += f'    "{planet}": "{position}",\n'
    french_chart_text = french_chart_text.rstrip(",\n") + "\n}"
    
    # Formater les aspects en français
    aspects_text = ""
    if aspects_patterns_data['aspects']:
        aspects_text = "\nAspects:\n"
        for aspect in aspects_patterns_data['aspects']:
            planet1_fr = planet_translations.get(aspect['planet1'], aspect['planet1'])
            planet2_fr = planet_translations.get(aspect['planet2'], aspect['planet2'])
            aspect_fr = aspect_translations.get(aspect['aspect'], aspect['aspect'])
            aspects_text += f"{planet1_fr} {aspect_fr} {planet2_fr} (orb: {aspect['orb']}°)\n"
    
    # Formater les patterns en français
    patterns_text = ""
    if aspects_patterns_data['patterns']:
        patterns_text = "\nConfigurations:\n"
        for pattern in aspects_patterns_data['patterns']:
            pattern_type_fr = pattern_translations.get(pattern['type'], pattern['type'])
            patterns_text += f"{pattern_type_fr}\n"
            
            if pattern['type'] == 'Stellium':
                sign_fr = sign_translations.get(pattern['sign'], pattern['sign'])
                patterns_text += f"  {sign_fr}\n"
                for planet in pattern['planets']:
                    if isinstance(planet, dict) and 'name' in planet:
                        planet_name_fr = planet_translations.get(planet['name'], planet['name'])
                        patterns_text += f"  {planet_name_fr} en {planet['position']}\n"
                        
            elif pattern['type'] == 'Multiple Aspect':
                target_planet_fr = planet_translations.get(pattern['target_planet'], pattern['target_planet'])
                patterns_text += f"  {target_planet_fr} en {pattern['target_position']}\n"
                for aspecting_planet in pattern['aspecting_planets']:
                    planet_fr = planet_translations.get(aspecting_planet['planet'], aspecting_planet['planet'])
                    aspect_fr = aspect_translations.get(aspecting_planet['aspect'], aspecting_planet['aspect'])
                    patterns_text += f"    {planet_fr} {aspect_fr} (orb: {aspecting_planet['orb']}°)\n"
                    
            elif pattern['type'] == 'Multiple Planet Square':
                if 'target_planet' in pattern:
                    # Ancien format
                    target_planet_fr = planet_translations.get(pattern['target_planet'], pattern['target_planet'])
                    # Traduire le signe dans la position
                    target_position_fr = pattern['target_position']
                    for eng, fr in sign_translations.items():
                        target_position_fr = target_position_fr.replace(eng, fr)
                    patterns_text += f"  {target_planet_fr} en {target_position_fr}\n"
                    for squaring_planet in pattern['squaring_planets']:
                        planet_fr = planet_translations.get(squaring_planet['planet'], squaring_planet['planet'])
                        # Traduire le signe dans la position
                        position_fr = squaring_planet['position']
                        for eng, fr in sign_translations.items():
                            position_fr = position_fr.replace(eng, fr)
                        patterns_text += f"  {planet_fr} en {position_fr}\n"
                else:
                    # Nouveau format
                    for planet in pattern.get('planets', []):
                        planet_name_fr = planet_translations.get(planet['name'], planet['name'])
                        # Traduire le signe dans la position
                        position_fr = planet['position']
                        for eng, fr in sign_translations.items():
                            position_fr = position_fr.replace(eng, fr)
                        patterns_text += f"  {planet_name_fr} en {position_fr}\n"
                    
            elif pattern['type'] == 'Berceau':
                # Format Cradle/Berceau
                for planet in pattern.get('planets', []):
                    planet_name_fr = planet_translations.get(planet['name'], planet['name'])
                    # Traduire le signe dans la position
                    position_fr = planet['position']
                    for eng, fr in sign_translations.items():
                        position_fr = position_fr.replace(eng, fr)
                    patterns_text += f"  {planet_name_fr} en {position_fr}\n"
                    
            elif pattern['type'] == 'Yod':
                for planet in pattern['planets']:
                    planet_name_fr = planet_translations.get(planet['name'], planet['name'])
                    # Traduire le signe dans la position
                    position_fr = planet['position']
                    for eng, fr in sign_translations.items():
                        position_fr = position_fr.replace(eng, fr)
                    patterns_text += f"  {planet_name_fr} en {position_fr}\n"
                    
            elif 'aspects' in pattern:
                for aspect in pattern['aspects']:
                    # Traduire les aspects dans la liste
                    aspect_fr = aspect
                    for eng, fr in aspect_translations.items():
                        aspect_fr = aspect_fr.replace(eng, fr)
                    for eng, fr in planet_translations.items():
                        aspect_fr = aspect_fr.replace(eng, fr)
                    for eng, fr in sign_translations.items():
                        aspect_fr = aspect_fr.replace(eng, fr)
                    patterns_text += f"  {aspect_fr}\n"
                    
            elif 'planets' in pattern:
                for planet in pattern['planets']:
                    planet_name_fr = planet_translations.get(planet['name'], planet['name'])
                    # Traduire le signe dans la position
                    position_fr = planet['position']
                    for eng, fr in sign_translations.items():
                        position_fr = position_fr.replace(eng, fr)
                    patterns_text += f"  {planet_name_fr} en {position_fr}\n"
    
    # Générer les paragraphes de positions planétaires dynamiquement
    planetary_paragraphs = generate_planetary_positions_paragraphs()
    
    # Récupérer les données des animaux totems
    animal_totem_data = get_animal_totem_data()
    
    # Récupérer l'animal totem depuis les données top3 (cohérence avec le reste)
    animal_totem = "Animal inconnu"
    if animal_totem_data:
        animal_totem = animal_totem_data[0]['determinant']
    
    # Générer les informations sur les animaux totems (partie 1 : animaux et scores)
    animal_totem_info_part1 = ""
    if animal_totem_data:
        # Top 1 animal
        top1 = animal_totem_data[0]
        animal_totem_info_part1 += f"1. {top1['determinant']}\n"
        animal_totem_info_part1 += f"{str(top1['overall_strength_adjust']).replace('.', ',')}\n\n"
        
        # Top 2 animal
        if len(animal_totem_data) > 1:
            top2 = animal_totem_data[1]
            animal_totem_info_part1 += f"2. {top2['determinant']}\n"
            animal_totem_info_part1 += f"{str(top2['overall_strength_adjust']).replace('.', ',')}\n\n"
        
        # Top 3 animal
        if len(animal_totem_data) > 2:
            top3 = animal_totem_data[2]
            animal_totem_info_part1 += f"3. {top3['determinant']}\n"
            animal_totem_info_part1 += f"{str(top3['overall_strength_adjust']).replace('.', ',')}\n\n"
    
    # Générer les informations sur les planètes (partie 2 : top 8 planètes)
    animal_totem_info_part2 = ""
    if animal_totem_data:
        top1 = animal_totem_data[0]
        top_planets = get_top_planets_for_animal(top1['english_name'], animal_totem_data)
        if top_planets:
            animal_totem_info_part2 += "Top 8 planètes avec les scores les plus élevés pour l'animal totem:\n"
            for planet in top_planets:
                animal_totem_info_part2 += f"- {planet['planet']} en {planet['sign']} en Maison {planet['house']}\n"
            animal_totem_info_part2
    
    # Définir les instructions pour les pages selon si la planète est dans le top 8 ou non
    TOP_8_PAGES_GUIDANCE = f"""- Page 1 ({TEXT_LENGTHS['MID']}): in 2 paragraphs, describe the planet's position in sign and house. Explain what the sign and house mean and how they influence the planet.
- Page 2 [{TEXT_LENGTHS['MID']}]: in 2 paragraphs, provide a deeper personal interpretation. Explain clearly the influence of this planet on the subject's identity and life. Focus on personality analysis based on planetary position, considering also aspects. Give clear plumastro analysis of the personality. DO NOT mention the animal totem.
- Page 3 [{TEXT_LENGTHS['MEGA_SHORT']}]: analyze the connection between this planet and the animal totem. Explain how this planetary energy resonates with the totem's characteristics. Write once the name of the animal in the text, but do not write "animal totem"."""

    NOT_TOP_8_PAGES_GUIDANCE = f"""- Page 1 ({TEXT_LENGTHS['MID']}): in 2 paragraphs, describe the planet's position in sign and house. Explain what the sign and house mean and how they influence the planet.
- Page 2 [{TEXT_LENGTHS['V_LONG']}]: in 2 or 3 paragraphs, provide a deeper personal interpretation. Explain clearly the influence of this planet on the subject's identity and life. Focus on personality analysis based on planetary position, here you have to consider aspects, more than just the planet and its location. Give clear plumastro analysis of the personality. DO NOT mention the animal totem."""
    
    # Traductions des planètes pour correspondance
    planet_translations = {
        "Soleil": "Sun", "Lune": "Moon", "Mercure": "Mercury", "Vénus": "Venus",
        "Mars": "Mars", "Jupiter": "Jupiter", "Saturne": "Saturn", "Uranus": "Uranus",
        "Neptune": "Neptune", "Pluton": "Pluto", "Nœud Nord": "North Node",
        "Ascendant": "Ascendant", "Milieu de Ciel": "MC"
    }
    
    # Traductions inverses
    planet_translations_inv = {v: k for k, v in planet_translations.items()}
    
    # Traductions des aspects
    aspect_translations = {
        "Conjunction": "Conjonction", "Opposition": "Opposition", "Square": "Carré",
        "Trine": "Trigone", "Sextile": "Sextile", "Quincunx": "Quinconce",
        "Semisextile": "Semi-sextile", "Semisquare": "Semi-carré", "Quintile": "Quintile",
        "Sesquiquintile": "Sesqui-quintile", "Biquintile": "Bi-quintile", "Semiquintile": "Semi-quintile"
    }
    
    # Traductions des signes
    sign_translations = {
        "Aries": "Bélier", "Taurus": "Taureau", "Gemini": "Gémeaux",
        "Cancer": "Cancer", "Leo": "Lion", "Virgo": "Vierge",
        "Libra": "Balance", "Scorpio": "Scorpion", "Sagittarius": "Sagittaire",
        "Capricorn": "Capricorne", "Aquarius": "Verseau", "Pisces": "Poissons"
    }
    
    # Créer une instance du générateur pour la distribution optimale
    from aspects_patterns_generator import AspectsPatternsGenerator
    generator_instance = AspectsPatternsGenerator()
    
    # Distribuer les mentions de manière optimale
    assignments = generator_instance.distribute_mentions_optimally(
        aspects_patterns_data['aspects'], 
        aspects_patterns_data['patterns']
    )
    
    # Fonction pour extraire les aspects et patterns assignés à une planète
    def get_planet_specific_aspects_and_patterns(planet_name, aspects_patterns_data, assignments):
        """Extrait les aspects et patterns ASSIGNÉS à une planète donnée"""
        planet_en = planet_translations.get(planet_name, planet_name)
        
        # Obtenir les mentions assignées à cette planète
        mentions = generator_instance.get_planet_mentions(
            planet_en, 
            aspects_patterns_data['aspects'], 
            aspects_patterns_data['patterns'], 
            assignments
        )
        
        planet_aspects = []
        planet_patterns = []
        
        # Formater les aspects assignés
        for aspect in mentions['aspects']:
            planet1_fr = planet_translations_inv.get(aspect['planet1'], aspect['planet1'])
            planet2_fr = planet_translations_inv.get(aspect['planet2'], aspect['planet2'])
            aspect_fr = aspect_translations.get(aspect['aspect'], aspect['aspect'])
            planet_aspects.append(f"{planet1_fr} {aspect_fr} {planet2_fr} (orb: {aspect['orb']}°)")
        
        # Formater les configurations assignées
        for pattern in mentions['patterns']:
            # Traduire le type de pattern
            pattern_type_fr = pattern_translations.get(pattern['type'], pattern['type'])
            
            if 'planets' in pattern:
                # Extraire les noms des planètes
                planet_names = []
                for planet_info in pattern['planets']:
                    if isinstance(planet_info, dict) and 'name' in planet_info:
                        p_name = planet_info['name']
                        p_position = planet_info['position']
                        
                        # Traduire les signes en français
                        for sign_en, sign_fr in sign_translations.items():
                            p_position = p_position.replace(sign_en, sign_fr)
                        
                        planet_names.append(f"{planet_translations_inv.get(p_name, p_name)} en {p_position}")
                
                if planet_names:
                    planet_patterns.append(f"{pattern_type_fr}: {', '.join(planet_names)}")
            elif 'target_planet' in pattern:
                target_fr = planet_translations_inv.get(pattern['target_planet'], pattern['target_planet'])
                target_position = pattern.get('target_position', '')
                
                # Traduire les signes en français
                for sign_en, sign_fr in sign_translations.items():
                    target_position = target_position.replace(sign_en, sign_fr)
                
                planet_patterns.append(f"{pattern_type_fr}: {target_fr} en {target_position}")
        
        return planet_aspects, planet_patterns
    
    # Générer la liste des planètes avec leurs instructions de pages
    planets_sequence = ["Soleil", "Ascendant", "Lune", "Mercure", "Vénus", "Mars", "Jupiter", "Saturne", "Uranus", "Neptune", "Pluton", "Milieu de Ciel", "Nœud Nord"]
    planets_paragraphs = []  # Liste pour stocker les 13 paragraphes séparés
    
    if animal_totem_data:
        top1 = animal_totem_data[0]
        top_planets = get_top_planets_for_animal(top1['english_name'], animal_totem_data)
        top_planets_names = [planet['planet'] for planet in top_planets] if top_planets else []
        
        for planet in planets_sequence:
            # Obtenir les aspects et patterns ASSIGNÉS à cette planète (distribution optimale)
            planet_aspects, planet_patterns = get_planet_specific_aspects_and_patterns(planet, aspects_patterns_data, assignments)
            
            # Construire la section des aspects et patterns
            aspects_section = ""
            if planet_aspects:
                aspects_section += f"\nTu peux si la symbolique est intéressante et pertinente pour l'analyse, mentionner ces aspects à {planet}:\n"
                for aspect in planet_aspects:
                    aspects_section += f"- {aspect}\n"
            
            if planet_patterns:
                aspects_section += f"\nTu peux si la symbolique est intéressante et pertinente pour l'analyse, mentionner ces Configurations impliquant {planet}:\n"
                for pattern in planet_patterns:
                    aspects_section += f"- {pattern}\n"
            
            # Créer un paragraphe complet pour cette planète
            planet_paragraph = f"""LET'S CONTINUE (REFER BACK TO THE FIRST PROMPT SENT IN THIS CHAT TO ENSURE YOU'RE FAMILIAR WITH ALL INPUT DATA)
Next Section :
PLANETARY ANALYSIS

"""
            
            if planet in top_planets_names:
                planet_paragraph += f"{planet} :\n{TOP_8_PAGES_GUIDANCE}{aspects_section}\n"
            else:
                planet_paragraph += f"{planet} :\n{NOT_TOP_8_PAGES_GUIDANCE}{aspects_section}\n"
            
            planet_paragraph += """
Important rules:
Vary the structure from one planet to the next, avoid repetitions
Sometimes begin with the sign, sometimes with the house, sometimes with an aspect.
Alternate descriptive style (evocative imagery) and analytical style (reasoning).
the planet amalysis must always be placed in the context of the full chart, never isolated.
Les numeros des maisons sont ecrits en chiffres arabes.
Souviens toi : pas de tiets "-" / "—"
Respecte les contraintes de longueur de texte pour chaque page.
"""
            
            planets_paragraphs.append(planet_paragraph)
    
    # Joindre tous les paragraphes avec des sauts de ligne
    planets_pages_guidance = "\n\n\n\n\n\n\n\n\n\n\n".join(planets_paragraphs)
    
    # Générer la liste des top 10 aspects les plus puissants
    top_10_aspects = ""
    if aspects_patterns_data['aspects']:
        # Trier les aspects par orbe croissant (plus l'orbe est petit, plus l'aspect est puissant)
        sorted_aspects = sorted(aspects_patterns_data['aspects'], key=lambda x: x['orb'])[:10]
        
        # Traductions des aspects
        aspect_translations = {
            "Conjunction": "Conjonction",
            "Opposition": "Opposition", 
            "Square": "Carré",
            "Trine": "Trigone",
            "Sextile": "Sextile",
            "Quincunx": "Quinconce",
            "Semisextile": "Semi-sextile",
            "Semisquare": "Semi-carré",
            "Quintile": "Quintile",
            "Sesquiquintile": "Sesqui-quintile",
            "Biquintile": "Bi-quintile",
            "Semiquintile": "Semi-quintile"
        }
        
        # Traductions des planètes
        planet_translations = {
            "Sun": "Soleil", "Moon": "Lune", "Mercury": "Mercure", "Venus": "Vénus",
            "Mars": "Mars", "Jupiter": "Jupiter", "Saturn": "Saturne", "Uranus": "Uranus",
            "Neptune": "Neptune", "Pluto": "Pluton", "North Node": "Nœud Nord",
            "Ascendant": "Ascendant", "MC": "MC"
        }
        
        for i, aspect in enumerate(sorted_aspects, 1):
            planet1_fr = planet_translations.get(aspect['planet1'], aspect['planet1'])
            planet2_fr = planet_translations.get(aspect['planet2'], aspect['planet2'])
            aspect_fr = aspect_translations.get(aspect['aspect'], aspect['aspect'])
            top_10_aspects += f"{planet1_fr} {aspect_fr} {planet2_fr} (orb: {aspect['orb']}°)\n\n"
    
    
    # Générer le contenu des positions planétaires
    planetary_positions_content = generate_planetary_positions_content()
    
    # Générer le prompt complet
    prompt = f"""{planetary_positions_content}
Aspects and configurations : {aspects_text}{patterns_text}








You are an expert astrologer from the Plumastro team.
Your mission is to write a highly personalised astrology book in French, using tutoiement, based on the client's complete natal chart. The text must sound alive, precise, and warm, as if it were written directly for them by the Plumastro team.
Your name is {astrologue_name} from Plumastro

1. Client Information

Prenom : {'-'.join([word[:1].upper() + word[1:].lower() for word in input_data.get('prenom', '').split('-')]) if input_data.get('prenom', '') else ''}

Lieu de naissance : {input_data.get('lieu_naissance', '').split(' — ')[0]}

Date de naissance : {input_data['date_naissance']}

Heure de naissance : {input_data['heure_naissance']}

Animal Totem : {animal_totem}

Genre : {input_data['genre']}

Birth Chart Data : {french_chart_text}

Aspects and configurations : {aspects_text}{patterns_text}

2. Structure of the Book

The book is divided into chapters/sections, each with a specific word length constraint.
You must write section by section. After each section, you will wait for me to say "OK" before continuing with the next one.

INTRODUCTION
TON ANIMAL TOTEM
PLANETARY ANALYSIS
COMPATIBILITÉS AVEC LES SIGNES
LES TRANSITS DE VIE
SYNTHÈSE DE LA PERSONNALITÉ


3. Writing Constraints
Language: French only.
As an astrologer, your analysis must be sincere and honest, without any sugarcoating or flattery.
Style: Expert astrologer, direct tutoiement.
Tone: Alive, deep, personal, never vague or flat. Don't use "Enfin, Ainsi, Cependant, etc..."
Formatting:
No emojis.
N'utilise pas le mot "féconde" ou "fécond"
No dashes or long "–" "—" → always use commas or slash instead.
Evite les formulations trop litteraires comme "en somme" ou "enfin", sois naturel dans ton style d'expression. Tu es astrologue de l'equipe Plumastro
Each page = maximum 2 paragraphs.
Name usage: The subject's first name appears only twice in the whole book: once in the Introduction, once in the Synthèse.
CRITICAL WORD COUNT REQUIREMENT:
- Stay within the specified word range
- Count words after writing each section and before sending the response to me, if outside range, rewrite to fit and then send the response to me.

4. Process
I'll give you the guidance for each section, and then you'll write the section
After each section, stop and wait for me to say "OK" before continuing.
✅ REMEMBER ALL THESE INSTRUCTIONS AND INPUT DATA FOR THIS ENTIRE CHAT, YOU MUST REFER BACK TO THIS INPUT EVERYTIME YOU GENERATE A RESPONSE













{'-'.join([word[:1].upper() + word[1:].lower() for word in input_data.get('prenom', '').split('-')]) if input_data.get('prenom', '') else ''},





LET'S CONTINUE (REFER BACK TO THE FIRST PROMPT SENT IN THIS CHAT TO ENSURE YOU'RE FAMILIAR WITH ALL INPUT DATA)
Next Section :
INTRODUCTION ({TEXT_LENGTHS['MID']} 1 page)
Start with the subject's first name "Prenom, tu es..."
Present their birth data (date, place, time)
Give a short synthesis of the subject's personality to tease the deeper analysis that will come next in the book (don't mention positions of planets or anything about birth chart)
Mention the spiritual animal clearly
Present yourself within the Plumastro team "Je vais analyser tout ton theme et t'accompagner..."
Explain briefly what the book will analyse next.
Souviens toi : pas de tiets "-" / "—", remplace par des virgules ou parentheses
Your name is {astrologue_name} from Plumastro








///////////RAJOUTE CARTE CIEL/////////////////










{planetary_paragraphs}











{top_10_aspects}









///////////RAJOUTE RADAR/////////////////




{animal_totem_info_part1}











LET'S CONTINUE (REFER BACK TO THE FIRST PROMPT SENT IN THIS CHAT TO ENSURE YOU'RE FAMILIAR WITH ALL INPUT DATA)
Next Section :
TON ANIMAL TOTEM (2 pages total)
PAGE 1 : Lien spirituel avec l'animal totem (Page 1) ({TEXT_LENGTHS['V_LONG']}) : Decris la CORRESPONDANCE AVEC L'ANIMAL TOTEM  {animal_totem_data[0]['determinant'] if len(animal_totem_data) > 1 else 'animal totem'}
Using the birth chart, understand the personality of the subject and then create link with the animal totem.Focus only on the link between the personality and the animal totem. Focus on creating connections between the personality of the subject and the symbol of the animal.
PAGE 2 : Spiritual link with the 2 other animals and transition to planetary analysis (Page 2) ({TEXT_LENGTHS['LONG']}) : 
Mention also some correlations and spiritual link with 2 other animals that have a connection (even if it's not as strong as the animal totem)  {animal_totem_data[1]['determinant'] if len(animal_totem_data) > 1 else 'le deuxième animal'} and {animal_totem_data[2]['determinant'] if len(animal_totem_data) > 2 else 'le troisième animal'} without mentioning any planets but purely focusing on the overall symbol of the animal and the connection with the subject's personality.
describe the link with the 2 animals and then connect it back to the animal totem reinforcing the link between the subject and animal totem. And finish with a transition to the upcoming planetary analysis that will clearly link the personality of the subject with the animal totem.
Tone: deep, inviting, excited, plumastro-style
Souviens toi : pas de tiets "-" / "—", remplace par des virgules ou parentheses
Souviens toi : tu t'addresses directement au sujet

















{planets_pages_guidance}






























LET'S CONTINUE (REFER BACK TO THE FIRST PROMPT SENT IN THIS CHAT TO ENSURE YOU'RE FAMILIAR WITH ALL INPUT DATA)
Next Section :
COMPATIBILITÉS AVEC LES SIGNES (2 pages total)
Page 1 ({TEXT_LENGTHS['V_LONG']}): introduce compatibility concept in astrology, but then explain that we can still get an overview of the compatibility by analysing the sun sign of other people with the subject's birth chart. then cover Feu & Terre, consider the entire birth chart in the analysis.
Page 2 ({TEXT_LENGTHS['V_LONG']}): cover Air & Eau, consider the entire birth chart in the analysis. End this page providing an idea of what type of personality and sign a subject's lover could have. Be specific to 2 or 3 signs maximum that vibrate the most with the subject.
For each element, go through each sign and put each sign in perspective with the entire personality of the subject, for signs where there is a key interaction you can give an example of how they could match in real life.
Souviens toi : pas de tiets "-" / "—", remplace par des virgules ou parentheses
Souviens toi : tu t'addresses directement au sujet















LET'S CONTINUE (REFER BACK TO THE FIRST PROMPT SENT IN THIS CHAT TO ENSURE YOU'RE FAMILIAR WITH ALL INPUT DATA)
Next Section :
LES TRANSITS DE VIE (3 pages total, {TEXT_LENGTHS['V_LONG']} each)
Explain what planetary transits are.
Describe key life periods and ages of transformation. On page1 focus on early stage of life, page2 is mid-life and page3 end-life. Make it a continuous flow for all 3 pages
Consider the age of the subject now to speak in the past and future depending on the age you're analysing. Go deep in the analysis here as an astrology expert, correlate transits with the birth chart to describe clearly the key life moments of the subject based on the birth chart.
Always tie predictions to the subject's natal chart.
Sois clair et precis sur l'interpretation des moments de vie et de ce que le sujet a vecu ou va vivre.
Write ages of the subject in numbers, don't write years (e.g. 2028)
Ton of voice : Plumastro style, direct, warm, personal, professional but Gen-Z friendly.
Souviens toi : pas de tiets "-" / "—", remplace par des virgules ou parentheses
Quand tu ecris des ages, ecris l'age suivi du mot "ans"
Fais des phrases completes et claires, pas juste des phrases partielles. Sois clair et precis.
Si tu mentionnes une maison, indique le mot "maison" et son numero en chiffre arabe.













LET'S CONTINUE (REFER BACK TO THE FIRST PROMPT SENT IN THIS CHAT TO ENSURE YOU'RE FAMILIAR WITH ALL INPUT DATA)
Next Section :
SYNTHÈSE DE LA PERSONNALITÉ
Page 1 {TEXT_LENGTHS['V_LONG']}
Page 2 {TEXT_LENGTHS['MID']}
Start with the subject's first name (once only here).
Summarise the entire personality by weaving together: planetary influences, aspects. (Don't talk about transits)
Make the animal totem central: show many symbolic links between the chart and the animal.
Give personalised advice and inspiration, like a letter signed by {astrologue_name} from Plumastro, I want the last paragraph to start with a variation of "De la part de {astrologue_name} et de l'équipe Plumastro je t'adresse ce livre comme une lettre personnelle,..." puis un conseil, une guidance sur elle et utiliser au mieux ses atouts personnels maintenant que nous avons analyse toute sa personnalite. Sois poetique, inspirant mais clairement comprehensible pour le sujet qui est francais.
Tone: warm, insightful, empowering.
Souviens toi : pas de tiets "-" / "—", remplace par des virgules ou parentheses



{astrologue_name} et l'équipe Plumastro





"""
    
    return prompt

def generate_book_from_text(input_text):
    """Génère un livre directement à partir du format de texte spécifique"""
    data = parse_input_format(input_text)
    if data:
        return generate_book(data)
    else:
        print("Erreur: Impossible de parser les données d'input")
        return False

def parse_input_format(input_text):
    """Parse le format d'input spécifique"""
    lines = input_text.strip().split('\n')
    data = {}
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Ignorer les lignes vides
        if not line:
            i += 1
            continue
            
        # Chercher les clés avec ":" (vérifier que c'est une vraie clé)
        if ':' in line:
            key = line.split(':')[0].strip()
            value = line.split(':', 1)[1].strip()
            # Vérifier que c'est une vraie clé (pas une heure)
            known_keys = ["Genre", "Nom", "Prenom", "Prénom", "Lieu de naissance", "_Ville - Pays", "_Ville - Région", "_Ville - Latitude", "_Ville - Longitude", "Date de naissance", "Heure de naissance"]
            if key not in known_keys:
                i += 1
                continue
                
            
            # Si la valeur est vide, prendre la ligne suivante (ignorer les lignes vides)
            if not value and i + 1 < len(lines):
                i += 1
                while i < len(lines) and not lines[i].strip():
                    i += 1
                if i < len(lines):
                    next_line = lines[i].strip()
                    # Vérifier que la ligne suivante n'est pas une nouvelle clé
                    if ':' not in next_line or next_line.split(':')[0].strip() not in known_keys:
                        value = next_line
                    else:
                        # Si c'est une nouvelle clé, on doit décrémenter i pour la traiter
                        i -= 1
            
            # Mapper les clés vers les champs attendus
            if key == "Genre":
                data['genre'] = value
            elif key == "Nom":
                data['nom'] = value
            elif key in ["Prenom", "Prénom"]:
                data['prenom'] = value
            elif key == "Lieu de naissance":
                data['lieu_naissance'] = value
            elif key == "_Ville - Pays":
                data['pays'] = value
            elif key == "_Ville - Région":
                data['region'] = value if value else ""
            elif key == "_Ville - Latitude":
                if value:  # Vérifier que la valeur n'est pas vide
                    data['lat'] = float(value)
            elif key == "_Ville - Longitude":
                if value:  # Vérifier que la valeur n'est pas vide
                    data['lon'] = float(value)
            elif key == "Date de naissance":
                data['date_naissance'] = value
            elif key == "Heure de naissance":
                data['heure_naissance'] = value
        
        i += 1
    
    return data

def get_user_input():
    """Récupère les données de l'utilisateur depuis le fichier 'INPUT TO GENERATE BOOK.txt'"""
    input_file = "INPUT TO GENERATE BOOK.txt"
    
    if not os.path.exists(input_file):
        print("Put your input in INPUT TO GENERATE BOOK.txt")
        return None
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            input_text = f.read()
        
        # Vérifier si le fichier est vide
        if not input_text.strip():
            print("Put your input in INPUT TO GENERATE BOOK.txt")
            return None
        
        print(f"Lecture des données depuis '{input_file}'...")
        data = parse_input_format(input_text)
        
        # Vérifier si les données essentielles sont présentes
        if not data or not data.get('prenom') or not data.get('date_naissance'):
            print("Put your input in INPUT TO GENERATE BOOK.txt")
            return None
        
        return data
        
    except Exception as e:
        print("Put your input in INPUT TO GENERATE BOOK.txt")
        return None

def generate_book(input_data=None):
    """Fonction principale pour générer un livre"""
    
    if input_data is None:
        input_data = get_user_input()
    
    if input_data is None:
        print("Erreur: Impossible de lire les données d'entrée.")
        return False
    
    print(f"\nGénération du livre pour {input_data.get('prenom', '')} {input_data.get('nom', '')}")
    print("=" * 60)
    
    # Créer le dossier livre
    os.makedirs("livre", exist_ok=True)
    
    try:
        # Lancer l'analyse PLUMATOTM
        print("Lancement de l'analyse PLUMATOTM...")
        if not run_plumatotm_analysis(input_data):
            # Vérifier si les fichiers essentiels ont été générés
            essential_files = ["outputs/result.json", "outputs/birth_chart.json", "outputs/animal_proportion.json"]
            if all(os.path.exists(f) for f in essential_files):
                print("WARNING: PLUMATOTM analysis had minor issues but essential files were generated. Continuing...")
            else:
                raise RuntimeError("L'analyse PLUMATOTM a échoué. Impossible de générer le livre.")
        
        # Générer les aspects et patterns
        print("Génération des aspects et patterns...")
        generator = AspectsPatternsGenerator()
        aspects_patterns_data = generator.generate_aspects_patterns(
            input_data['date_naissance'],
            input_data['heure_naissance'],
            input_data['lat'],
            input_data['lon']
        )
        
        print(f"Aspects trouvés: {len(aspects_patterns_data['aspects'])}")
        print(f"Configurations trouvées: {len(aspects_patterns_data['patterns'])}")
        
        # Afficher les aspects principaux
        print("\nAspects principaux:")
        for i, aspect in enumerate(aspects_patterns_data['aspects'][:10], 1):
            print(f"{i:2d}. {aspect['planet1']} {aspect['aspect']} {aspect['planet2']} (orb: {aspect['orb']}°)")
        
        # Afficher les patterns
        if aspects_patterns_data['patterns']:
            print(f"\nConfigurations ({len(aspects_patterns_data['patterns'])}):")
            for i, pattern in enumerate(aspects_patterns_data['patterns'], 1):
                print(f"\n{i}. {pattern['type']}")
                if pattern['type'] == 'T-Square':
                    for planet in pattern['planets']:
                        print(f"  {planet['name']} in {planet['position']}")
                elif pattern['type'] == 'Yod':
                    print("  YOD DETECTE!")
                    for planet in pattern['planets']:
                        print(f"  {planet['name']} in {planet['position']}")
                elif pattern['type'] == 'Stellium':
                    print(f"  {pattern['sign']}")
                    for planet in pattern['planets']:
                        print(f"  {planet['name']} in {planet['position']}")
                elif pattern['type'] == 'Multiple Planet Square':
                    if 'target_planet' in pattern:
                        # Ancien format
                        print(f"  {pattern['target_planet']} in {pattern['target_position']}")
                        for squaring_planet in pattern['squaring_planets']:
                            print(f"  {squaring_planet['planet']} in {squaring_planet['position']}")
                    else:
                        # Nouveau format
                        for planet in pattern.get('planets', []):
                            print(f"  {planet['name']} in {planet['position']}")
                elif pattern['type'] == 'Berceau':
                    # Format Cradle/Berceau
                    for planet in pattern.get('planets', []):
                        print(f"  {planet['name']} in {planet['position']}")
        else:
            print("\nAucun pattern majeur détecté")
        
        # Copier les fichiers PNG
        print("\nCopie des fichiers PNG...")
        png_files = [
            ("outputs/top1_animal_radar.png", "livre/top1_animal_radar.png"),
            ("outputs/top2_animal_radar.png", "livre/top2_animal_radar.png"),
            ("outputs/top3_animal_radar.png", "livre/top3_animal_radar.png"),
            ("outputs/birth_chart.png", "livre/birth_chart.png")
        ]
        
        for src, dst in png_files:
            if not os.path.exists(src):
                print(f"WARNING: Fichier PNG manquant: {src}")
                continue
            
            if os.path.getsize(src) == 0:
                print(f"WARNING: Fichier PNG vide: {src}")
                continue
            
            shutil.copy2(src, dst)
            print(f"Copié: {src} -> {dst}")
        
        # Générer le prompt ChatGPT
        print("\nGénération du prompt ChatGPT...")
        prompt = generate_chatgpt_prompt(input_data, aspects_patterns_data)
        
        # Sauvegarder le prompt
        prompt_file = "livre/prompt_chatgpt.txt"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        print(f"Prompt sauvegardé: {prompt_file}")
        
        # Les positions planétaires sont maintenant intégrées dans le prompt ChatGPT
        print("\nPositions planétaires intégrées dans le prompt ChatGPT")
        
        print("\nGénération terminée avec succès!")
        print("Fichiers générés dans le dossier 'livre':")
        print("   - top1_animal_radar.png")
        print("   - top2_animal_radar.png") 
        print("   - top3_animal_radar.png")
        print("   - birth_chart.png")
        print("   - prompt_chatgpt.txt (contient maintenant les positions planétaires)")
        
        return True
        
    except Exception as e:
        print(f"\nErreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    generate_book()
