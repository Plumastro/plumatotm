#!/usr/bin/env python3
"""
Test script for ChatGPT interpretation functionality
"""

import json
import os
from plumatotm_core import BirthChartAnalyzer

def test_chatgpt_interpretation():
    """Test the ChatGPT interpretation functionality"""
    
    # Load test data from outputs directory
    try:
        with open('outputs/birth_chart.json', 'r', encoding='utf-8') as f:
            birth_chart_data = json.load(f)
        
        with open('outputs/top3_true_false.json', 'r', encoding='utf-8') as f:
            true_false_data = json.load(f)
        
        with open('outputs/animal_totals.json', 'r', encoding='utf-8') as f:
            animal_totals_data = json.load(f)
        
    except FileNotFoundError as e:
        print(f"❌ Test data not found: {e}")
        print("Please run plumatotm_core.py first to generate the required output files")
        return False
    
    # Initialize analyzer (we only need it for the supported_planets list)
    analyzer = BirthChartAnalyzer(
        "plumatotm_raw_scores.json",
        "plumatotm_planets_weights.csv", 
        "plumatotm_planets_multiplier.csv"
    )
    
    # Convert JSON data to DataFrame format
    import pandas as pd
    true_false_df = pd.DataFrame.from_dict(true_false_data, orient='index')
    animal_totals_df = pd.DataFrame(animal_totals_data)
    
    # Extract planet signs and houses from birth chart data
    if isinstance(birth_chart_data, dict) and "planet_signs" in birth_chart_data:
        # New format with separate planet_signs and planet_houses
        planet_signs = birth_chart_data["planet_signs"]
        planet_houses = birth_chart_data["planet_houses"]
    else:
        # Old format - assume it's just planet signs
        planet_signs = birth_chart_data
        planet_houses = {}
        print("⚠️  Using old birth chart format - house information not available")
    
    # Test the ChatGPT interpretation
    print("🤖 Testing ChatGPT interpretation...")
    interpretation = analyzer.generate_chatgpt_interpretation(
        planet_signs, planet_houses, true_false_df, animal_totals_df
    )
    
    if interpretation:
        print("✅ ChatGPT interpretation generated successfully!")
        print(f"Top1 Animal: {interpretation['top1_animal']}")
        print(f"True Planets: {', '.join(interpretation['true_planets'])}")
        print(f"Character Count: {interpretation['character_count']}")
        print("\n📝 Interpretation:")
        print(interpretation['interpretation'])
        
        # Save to file
        with open('outputs/test_chatgpt_interpretation.json', 'w', encoding='utf-8') as f:
            json.dump(interpretation, f, indent=2, ensure_ascii=False)
        print("\n💾 Test interpretation saved to: outputs/test_chatgpt_interpretation.json")
        
        return True
    else:
        print("❌ ChatGPT interpretation failed")
        print("This is expected if OPENAI_API_KEY is not set")
        return False

def test_prompt_generation():
    """Test the prompt generation without calling the API"""
    
    # Load test data from outputs directory
    try:
        with open('outputs/birth_chart.json', 'r', encoding='utf-8') as f:
            birth_chart_data = json.load(f)
        
        with open('outputs/top3_true_false.json', 'r', encoding='utf-8') as f:
            true_false_data = json.load(f)
        
        with open('outputs/animal_totals.json', 'r', encoding='utf-8') as f:
            animal_totals_data = json.load(f)
        
    except FileNotFoundError as e:
        print(f"❌ Test data not found: {e}")
        return False
    
    # Initialize analyzer
    analyzer = BirthChartAnalyzer(
        "plumatotm_raw_scores.json",
        "plumatotm_planets_weights.csv", 
        "plumatotm_planets_multiplier.csv"
    )
    
    # Convert JSON data to DataFrame format
    import pandas as pd
    true_false_df = pd.DataFrame.from_dict(true_false_data, orient='index')
    animal_totals_df = pd.DataFrame(animal_totals_data)
    
    # Extract planet signs and houses from birth chart data
    if isinstance(birth_chart_data, dict) and "planet_signs" in birth_chart_data:
        # New format with separate planet_signs and planet_houses
        planet_signs = birth_chart_data["planet_signs"]
        planet_houses = birth_chart_data["planet_houses"]
    else:
        # Old format - assume it's just planet signs
        planet_signs = birth_chart_data
        planet_houses = {}
        print("⚠️  Using old birth chart format - house information not available")
    
    # Get the top1 animal
    top1_animal = animal_totals_df.iloc[0]['ANIMAL']
    
    # Get the planets marked TRUE for the top1 animal
    top1_true_planets = []
    for planet in analyzer.supported_planets:
        if true_false_df.loc[top1_animal, planet]:
            top1_true_planets.append(planet)
    
    print("🔍 Testing prompt generation...")
    print(f"Top1 Animal: {top1_animal}")
    print(f"True Planets: {', '.join(top1_true_planets)}")
    print(f"Birth Chart Signs: {json.dumps(planet_signs, indent=2, ensure_ascii=False)}")
    print(f"Birth Chart Houses: {json.dumps(planet_houses, indent=2, ensure_ascii=False)}")
    
    # Build the prompt (same logic as in the method)
    prompt = f"""Tu es un astrologue expert spécialisé dans l'interprétation des thèmes de naissance et la compatibilité avec les animaux totems.

Basé sur le thème de naissance suivant et les planètes qui ont une forte corrélation avec l'animal totem, explique pourquoi l'animal "{top1_animal}" correspond à la personnalité de cette personne.

THÈME DE NAISSANCE:
{json.dumps(planet_signs, indent=2, ensure_ascii=False)}

PLANÈTES AVEC FORTE CORRÉLATION POUR L'ANIMAL "{top1_animal}":
{', '.join(top1_true_planets)}

Pour chaque planète marquée TRUE, voici son signe et sa maison dans le thème de naissance:
"""
    
    # Add planet-sign-house combinations for TRUE planets
    for planet in top1_true_planets:
        sign = planet_signs.get(planet, "Non défini")
        house = planet_houses.get(planet, 0)
        prompt += f"- {planet}: {sign} (Maison {house})\n"
    
    prompt += f"""

Écris une interprétation courte (environ 800 caractères au total) en 3 points bullet points expliquant pourquoi l'animal "{top1_animal}" correspond à la personnalité de cette personne. Chaque point doit établir une corrélation directe entre des éléments spécifiques du thème natal (planètes dans signes et maisons) et l'archétype de l'animal.

Format de réponse souhaité (3 points obligatoires):
• [Trait de personnalité] : [planète(s) en signe(s) et maison(s)] donne/transmet [qualité]. Comme [l'animal], tu [comportement/qualité], grâce à [aspect astrologique spécifique].
• [Autre trait de personnalité] : [planète(s) en signe(s) et maison(s)] traduit [qualité]. [L'animal] incarne [trait], [comportement spécifique], [qualité].
• [Troisième trait de personnalité] : [planète(s) en signe(s) et maison(s)] apporte [qualité]. Comme [l'animal] qui [comportement animal], ta personnalité associe [qualités], [comportements].

IMPORTANT: 
- Chaque point doit mentionner des planètes spécifiques avec leurs signes et maisons
- Établir des corrélations directes entre les aspects astrologiques et les traits de l'animal
- Utiliser le tutoiement et un style fluide
- Inclure des références concrètes aux comportements de l'animal
- Maximum 800 caractères au total"""
    
    print("\n📝 Generated Prompt:")
    print("=" * 50)
    print(prompt)
    print("=" * 50)
    
    # Save prompt to file for reference
    with open('outputs/test_prompt.txt', 'w', encoding='utf-8') as f:
        f.write(prompt)
    print("\n💾 Prompt saved to: outputs/test_prompt.txt")
    
    return True

if __name__ == "__main__":
    print("🧪 Testing ChatGPT Interpretation Feature")
    print("=" * 50)
    
    # Test prompt generation (works without API key)
    print("\n1. Testing prompt generation...")
    test_prompt_generation()
    
    # Test full functionality (requires API key)
    print("\n2. Testing full ChatGPT interpretation...")
    test_chatgpt_interpretation()
    
    print("\n✅ Testing completed!")
