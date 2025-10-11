#!/usr/bin/env python3
"""
Analyse des différences entre configurations attendues et détectées
"""

from aspects_patterns_generator import AspectsPatternsGenerator
from flatlib import const

def analyze_yod_differences():
    """Analyse les différences entre les Yods"""
    generator = AspectsPatternsGenerator()
    
    date = "1992-06-06"
    time = "03:10"
    lat = 47.6241674
    lon = 4.3373194
    
    chart = generator.generate_chart_from_plumatotm_data(date, time, lat, lon)
    
    # Obtenir les planètes
    sun = generator._get_chart_object(chart, const.SUN)
    moon = generator._get_chart_object(chart, const.MOON)
    mercury = generator._get_chart_object(chart, const.MERCURY)
    neptune = generator._get_chart_object(chart, const.NEPTUNE)
    
    print("="*80)
    print("ANALYSE YOD: Neptune-Moon-Sun (attendu) vs Moon-Mercury-Neptune (detecte)")
    print("="*80)
    
    # Yod attendu: Neptune-Moon-Sun
    print("\n1. Yod ATTENDU: Neptune-Moon-Sun")
    asp_sun_moon_1 = generator._get_aspect_with_node_override(sun, moon, [const.SEXTILE])
    asp_sun_neptune_1 = generator._get_aspect_with_node_override(sun, neptune, [const.QUINCUNX])
    asp_moon_neptune_1 = generator._get_aspect_with_node_override(moon, neptune, [const.QUINCUNX])
    
    print(f"  Sun-Moon Sextile: orbe {asp_sun_moon_1.orb:.2f}deg")
    print(f"  Sun-Neptune Quincunx: orbe {asp_sun_neptune_1.orb:.2f}deg")
    print(f"  Moon-Neptune Quincunx: orbe {asp_moon_neptune_1.orb:.2f}deg")
    
    orbe_moyen_1 = (asp_sun_moon_1.orb + asp_sun_neptune_1.orb + asp_moon_neptune_1.orb) / 3
    print(f"  ORBE MOYEN: {orbe_moyen_1:.2f}deg")
    print(f"  Planetes: Sun (personnelle), Moon (personnelle), Neptune (transpersonnelle)")
    
    # Yod détecté: Moon-Mercury-Neptune
    print("\n2. Yod DETECTE: Moon-Mercury-Neptune")
    asp_moon_mercury = generator._get_aspect_with_node_override(moon, mercury, [const.SEXTILE])
    asp_moon_neptune_2 = generator._get_aspect_with_node_override(moon, neptune, [const.QUINCUNX])
    asp_mercury_neptune = generator._get_aspect_with_node_override(mercury, neptune, [const.QUINCUNX])
    
    print(f"  Moon-Mercury Sextile: orbe {asp_moon_mercury.orb:.2f}deg")
    print(f"  Moon-Neptune Quincunx: orbe {asp_moon_neptune_2.orb:.2f}deg")
    print(f"  Mercury-Neptune Quincunx: orbe {asp_mercury_neptune.orb:.2f}deg")
    
    orbe_moyen_2 = (asp_moon_mercury.orb + asp_moon_neptune_2.orb + asp_mercury_neptune.orb) / 3
    print(f"  ORBE MOYEN: {orbe_moyen_2:.2f}deg")
    print(f"  Planetes: Moon (personnelle), Mercury (personnelle), Neptune (transpersonnelle)")
    
    print(f"\n3. COMPARAISON:")
    print(f"  Difference d'orbe moyen: {abs(orbe_moyen_1 - orbe_moyen_2):.2f}deg")
    print(f"  Yod avec orbe le plus serre: {'Neptune-Moon-Sun' if orbe_moyen_1 < orbe_moyen_2 else 'Moon-Mercury-Neptune'}")
    
    # En astrologie, Sun est généralement considéré plus important que Mercury
    print(f"\n4. IMPORTANCE ASTROLOGIQUE:")
    print(f"  Neptune-Moon-Sun: Implique le SOLEIL (identite, essence)")
    print(f"  Moon-Mercury-Neptune: Implique MERCURE (mental, communication)")
    print(f"  => Le Soleil est traditionnellement plus important que Mercure en astrologie")

def analyze_cradle_differences():
    """Analyse les différences entre les Cradles"""
    generator = AspectsPatternsGenerator()
    
    date = "1992-06-06"
    time = "03:10"
    lat = 47.6241674
    lon = 4.3373194
    
    chart = generator.generate_chart_from_plumatotm_data(date, time, lat, lon)
    
    # Obtenir les planètes
    sun = generator._get_chart_object(chart, const.SUN)
    moon = generator._get_chart_object(chart, const.MOON)
    mars = generator._get_chart_object(chart, const.MARS)
    saturn = generator._get_chart_object(chart, const.SATURN)
    asc = generator._get_chart_object(chart, const.ASC)
    
    print("\n\n" + "="*80)
    print("ANALYSE CRADLE: Moon-Saturn-Ascendant-Sun (attendu) vs Moon-Saturn-Sun-Mars (detecte)")
    print("="*80)
    
    # Cradle attendu: Moon-Saturn-Ascendant-Sun
    print("\n1. Cradle ATTENDU: Moon-Saturn-Ascendant-Sun")
    opp = generator._get_aspect_with_node_override(moon, saturn, [const.OPPOSITION])
    asp1 = generator._get_aspect_with_node_override(asc, moon, [const.TRINE])
    asp2 = generator._get_aspect_with_node_override(asc, saturn, [const.SEXTILE])
    asp3 = generator._get_aspect_with_node_override(sun, moon, [const.SEXTILE])
    asp4 = generator._get_aspect_with_node_override(sun, saturn, [const.TRINE])
    
    print(f"  Moon-Saturn Opposition: orbe {opp.orb:.2f}deg")
    print(f"  Ascendant-Moon Trine: orbe {asp1.orb:.2f}deg")
    print(f"  Ascendant-Saturn Sextile: orbe {asp2.orb:.2f}deg")
    print(f"  Sun-Moon Sextile: orbe {asp3.orb:.2f}deg")
    print(f"  Sun-Saturn Trine: orbe {asp4.orb:.2f}deg")
    
    orbe_moyen_1 = (opp.orb + asp1.orb + asp2.orb + asp3.orb + asp4.orb) / 5
    print(f"  ORBE MOYEN: {orbe_moyen_1:.2f}deg")
    print(f"  Planetes: Moon (personnelle), Saturn (sociale), Ascendant (ANGLE), Sun (personnelle)")
    
    # Cradle détecté: Moon-Saturn-Sun-Mars
    print("\n2. Cradle DETECTE: Moon-Saturn-Sun-Mars")
    opp2 = generator._get_aspect_with_node_override(moon, saturn, [const.OPPOSITION])
    asp5 = generator._get_aspect_with_node_override(sun, moon, [const.SEXTILE])
    asp6 = generator._get_aspect_with_node_override(sun, saturn, [const.TRINE])
    asp7 = generator._get_aspect_with_node_override(mars, moon, [const.TRINE])
    asp8 = generator._get_aspect_with_node_override(mars, saturn, [const.SEXTILE])
    
    print(f"  Moon-Saturn Opposition: orbe {opp2.orb:.2f}deg")
    print(f"  Sun-Moon Sextile: orbe {asp5.orb:.2f}deg")
    print(f"  Sun-Saturn Trine: orbe {asp6.orb:.2f}deg")
    print(f"  Mars-Moon Trine: orbe {asp7.orb:.2f}deg")
    print(f"  Mars-Saturn Sextile: orbe {asp8.orb:.2f}deg")
    
    orbe_moyen_2 = (opp2.orb + asp5.orb + asp6.orb + asp7.orb + asp8.orb) / 5
    print(f"  ORBE MOYEN: {orbe_moyen_2:.2f}deg")
    print(f"  Planetes: Moon (personnelle), Saturn (sociale), Sun (personnelle), Mars (personnelle)")
    
    print(f"\n3. COMPARAISON:")
    print(f"  Difference d'orbe moyen: {abs(orbe_moyen_1 - orbe_moyen_2):.2f}deg")
    print(f"  Cradle avec orbe le plus serre: {'Moon-Saturn-Ascendant-Sun' if orbe_moyen_1 < orbe_moyen_2 else 'Moon-Saturn-Sun-Mars'}")
    
    print(f"\n4. IMPORTANCE ASTROLOGIQUE:")
    print(f"  Moon-Saturn-Ascendant-Sun: Implique l'ASCENDANT (angle majeur, personnalite)")
    print(f"  Moon-Saturn-Sun-Mars: Implique MARS (action, energie)")
    print(f"  => L'Ascendant est traditionnellement plus important que Mars en astrologie")
    print(f"     car c'est un ANGLE MAJEUR du theme")

def main():
    analyze_yod_differences()
    analyze_cradle_differences()
    
    print("\n\n" + "="*80)
    print("CONCLUSION")
    print("="*80)
    print("""
Les différences s'expliquent par le critère de sélection basé sur l'orbe moyen:
- L'algorithme actuel privilégie les configurations avec les orbes les plus serrés
- MAIS en astrologie traditionnelle, certaines planètes/points sont plus importants:
  1. ANGLES (Ascendant, MC) sont les plus importants
  2. LUMINAIRES (Sun, Moon) sont très importants
  3. PLANETES PERSONNELLES (Mercury, Venus, Mars) sont importantes
  4. PLANETES SOCIALES/TRANSPERSONNELLES sont secondaires

SOLUTION PROPOSEE:
Modifier l'algorithme pour privilégier les configurations qui impliquent:
1. Les Angles (Ascendant, MC) en priorité
2. Les Luminaires (Sun, Moon) ensuite
3. Puis les autres planètes personnelles

Cela correspondrait mieux à la pratique astrologique traditionnelle.
    """)

if __name__ == "__main__":
    main()
