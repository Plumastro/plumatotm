#!/usr/bin/env python3
"""Vérifier si le Yod Pluto-Mars-Mercury est valide"""

from aspects_patterns_generator import AspectsPatternsGenerator
from flatlib import const

def check_yod():
    generator = AspectsPatternsGenerator()
    
    date = "1992-06-06"
    time = "03:10"
    lat = 47.6241674
    lon = 4.3373194
    
    chart = generator.generate_chart_from_plumatotm_data(date, time, lat, lon)
    
    # Obtenir les planètes
    pluto = generator._get_chart_object(chart, const.PLUTO)
    mars = generator._get_chart_object(chart, const.MARS)
    mercury = generator._get_chart_object(chart, const.MERCURY)
    
    print("="*80)
    print("VERIFICATION YOD: Pluto-Mars-Mercury")
    print("="*80)
    
    print(f"\nPositions:")
    print(f"  Pluto: {pluto.lon:.2f}deg ({pluto.signlon:.1f}deg {pluto.sign})")
    print(f"  Mars: {mars.lon:.2f}deg ({mars.signlon:.1f}deg {mars.sign})")
    print(f"  Mercury: {mercury.lon:.2f}deg ({mercury.signlon:.1f}deg {mercury.sign})")
    
    # Pour un Yod, il faut:
    # - 1 sextile (60deg)
    # - 2 quinconces (150deg)
    
    print(f"\nAspects requis pour un Yod:")
    
    # Vérifier Mars-Mercury sextile
    asp1 = generator._get_aspect_with_node_override(mars, mercury, [const.SEXTILE])
    if asp1 and asp1.exists():
        print(f"  Mars-Mercury Sextile: OUI (orbe: {asp1.orb:.2f}deg)")
    else:
        print(f"  Mars-Mercury Sextile: NON")
    
    # Vérifier Mars-Pluto quinconce
    asp2 = generator._get_aspect_with_node_override(mars, pluto, [const.QUINCUNX])
    if asp2 and asp2.exists():
        print(f"  Mars-Pluto Quincunx: OUI (orbe: {asp2.orb:.2f}deg)")
    else:
        print(f"  Mars-Pluto Quincunx: NON")
        # Calculer la distance
        diff = abs(mars.lon - pluto.lon)
        if diff > 180:
            diff = 360 - diff
        print(f"    Distance angulaire: {diff:.2f}deg (orbe: {abs(diff-150):.2f}deg)")
    
    # Vérifier Mercury-Pluto quinconce
    asp3 = generator._get_aspect_with_node_override(mercury, pluto, [const.QUINCUNX])
    if asp3 and asp3.exists():
        print(f"  Mercury-Pluto Quincunx: OUI (orbe: {asp3.orb:.2f}deg)")
    else:
        print(f"  Mercury-Pluto Quincunx: NON")
        # Calculer la distance
        diff = abs(mercury.lon - pluto.lon)
        if diff > 180:
            diff = 360 - diff
        print(f"    Distance angulaire: {diff:.2f}deg (orbe: {abs(diff-150):.2f}deg)")
    
    valid = (asp1 and asp1.exists() and asp1.orb <= 8 and
             asp2 and asp2.exists() and asp2.orb <= 8 and
             asp3 and asp3.exists() and asp3.orb <= 8)
    
    print(f"\nYod Pluto-Mars-Mercury valide: {'OUI' if valid else 'NON'}")
    
    if valid:
        orbe_moyen = (asp1.orb + asp2.orb + asp3.orb) / 3
        importance = generator._calculate_planetary_importance_score(["Pluto", "Mars", "Mercury"])
        composite = importance - (orbe_moyen * 0.3)
        print(f"  Orbe moyen: {orbe_moyen:.2f}deg")
        print(f"  Importance: {importance:.2f}")
        print(f"  Score composite: {composite:.2f}")

if __name__ == "__main__":
    check_yod()
