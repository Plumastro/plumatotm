#!/usr/bin/env python3
"""
Générateur d'aspects et patterns astrologiques pour PLUMATOTM
Ce module calcule les aspects et patterns en réutilisant les calculs de thème existants
"""

import os
import json
import itertools
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
from flatlib.aspects import getAspect

class AspectsPatternsGenerator:
    def __init__(self):
        self.planet_names = {
            const.SUN: "Sun",
            const.MOON: "Moon",
            const.MERCURY: "Mercury",
            const.VENUS: "Venus",
            const.MARS: "Mars",
            const.JUPITER: "Jupiter",
            const.SATURN: "Saturn",
            const.URANUS: "Uranus",
            const.NEPTUNE: "Neptune",
            const.PLUTO: "Pluto",
            const.NORTH_NODE: "North Node",
            const.SOUTH_NODE: "South Node",
            const.ASC: "Ascendant",
            const.MC: "MC"
        }
        self.aspect_names = {
            const.CONJUNCTION: "Conjunction",
            const.SEXTILE: "Sextile",
            const.SQUARE: "Square",
            const.TRINE: "Trine",
            const.OPPOSITION: "Opposition",
            const.SEMISEXTILE: "Semisextile",
            const.SEMIQUINTILE: "Semiquintile",
            const.SEMISQUARE: "Semisquare",
            const.QUINTILE: "Quintile",
            const.SESQUIQUINTILE: "Sesquiquintile",
            const.BIQUINTILE: "Biquintile",
            const.QUINCUNX: "Quincunx"
        }
        
        # Définir les orbes selon les standards professionnels
        # Aspects majeurs: 8°, Aspects mineurs: 4°
        self.aspect_orbs = {
            # Aspects majeurs - 8° d'orbe
            const.CONJUNCTION: 8,
            const.SEXTILE: 8,
            const.SQUARE: 8,
            const.TRINE: 8,
            const.OPPOSITION: 8,
            
            # Aspects mineurs - 4° d'orbe
            const.SEMISEXTILE: 4,
            const.SEMIQUINTILE: 4,
            const.SEMISQUARE: 4,
            const.QUINTILE: 4,
            const.SESQUIQUINTILE: 4,
            const.BIQUINTILE: 4,
            const.QUINCUNX: 4
        }
    
    def get_aspect_orb(self, aspect_type):
        """Retourne l'orbe approprié pour un type d'aspect donné"""
        return self.aspect_orbs.get(aspect_type, 4)  # 4° par défaut pour les aspects non définis

    def generate_chart_from_plumatotm_data(self, date, time, lat, lon):
        """Génère un thème astrologique en réutilisant la même logique que PLUMATOTM"""
        try:
            # Conversion UTC simplifiée (copiée de plumatotm_core)
            from datetime import datetime
            from zoneinfo import ZoneInfo
            from timezonefinder import TimezoneFinder
            
            # Utiliser TimezoneFinder pour obtenir le timezone
            tf = TimezoneFinder()
            timezone_name = tf.timezone_at(lat=lat, lng=lon)
            
            if not timezone_name:
                raise ValueError(f"Could not determine timezone for coordinates ({lat}, {lon})")
            
            # Calculer la date UTC
            y, m, d = map(int, date.split("-"))
            hh, mm = map(int, time.split(":"))
            local_naive = datetime(y, m, d, hh, mm)
            local_dt = local_naive.replace(tzinfo=ZoneInfo(timezone_name))
            utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
            utc_date = utc_dt.strftime("%Y/%m/%d")
            utc_time = utc_dt.strftime("%H:%M")
            
            # Créer la date/heure UTC pour flatlib
            dt = Datetime(utc_date, utc_time, 0)
            
            # Créer la position géographique
            pos = GeoPos(lat, lon)
            
            # Vérifier la latitude pour le système de maisons
            if abs(lat) > 66.0:
                house_system = const.HOUSES_PORPHYRIUS
            else:
                house_system = const.HOUSES_PLACIDUS
            
            # Créer le thème avec les mêmes objets que PLUMATOTM
            custom_objects = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'North Node']
            chart = Chart(dt, pos, hsys=house_system, IDs=custom_objects)
            
            return chart
            
        except Exception as e:
            raise ValueError(f"Error generating chart: {e}")

    def _get_chart_object(self, chart, obj_id):
        """Récupère un objet du thème en gérant les cas spéciaux pour ASC et MC"""
        try:
            if obj_id == const.ASC:
                return chart.getAngle(const.ASC)
            elif obj_id == const.MC:
                return chart.getAngle(const.MC)
            else:
                return chart.getObject(obj_id)
        except Exception:
            return None

    def _get_aspect_with_node_override(self, obj1, obj2, aspect_list):
        """Obtient un aspect en contournant les bugs flatlib pour les Nœuds et Quinconces"""
        # D'abord essayer la méthode normale
        aspect = getAspect(obj1, obj2, aspect_list)
        
        # Si pas d'aspect, calculer manuellement (bug flatlib avec Nodes et Quinconces)
        if not aspect or not aspect.exists():
            # Calculer manuellement la différence d'angle
            diff = abs(obj1.lon - obj2.lon)
            if diff > 180:
                diff = 360 - diff
            
            # Définir les angles cibles pour chaque aspect
            aspect_angles = {
                const.CONJUNCTION: 0,
                const.SEXTILE: 60,
                const.SQUARE: 90,
                const.TRINE: 120,
                const.QUINCUNX: 150,
                const.OPPOSITION: 180,
                const.SEMISEXTILE: 30,
                const.SEMISQUARE: 45,
                const.QUINTILE: 72,
                const.SESQUIQUINTILE: 108,
                const.BIQUINTILE: 144
            }
            
            # Vérifier chaque aspect demandé
            for aspect_type in aspect_list:
                if aspect_type in aspect_angles:
                    target_angle = aspect_angles[aspect_type]
                    orb = abs(diff - target_angle)
                    max_orb = self.get_aspect_orb(aspect_type)  # Utilise les orbes différenciés
                    
                    if orb <= max_orb:
                        # Créer un objet aspect factice
                        class FakeAspect:
                            def __init__(self, aspect_type, orb_val):
                                self.type = aspect_type
                                self.orb = orb_val
                            def exists(self):
                                return True
                        
                        return FakeAspect(aspect_type, orb)
        
        return aspect

    def calculate_aspects(self, chart, max_orb=8):
        """Calcule tous les aspects du thème"""
        aspects = []
        
        # Liste des objets à analyser (même que PLUMATOTM)
        objects = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO,
            const.NORTH_NODE, const.ASC, const.MC
        ]
        
        # Calculer les aspects entre tous les objets
        for i, obj1_id in enumerate(objects):
            obj1 = self._get_chart_object(chart, obj1_id)
            if not obj1:
                continue
            
            for j, obj2_id in enumerate(objects):
                if i >= j:  # Éviter les doublons et les aspects avec soi-même
                    continue
                
                obj2 = self._get_chart_object(chart, obj2_id)
                if not obj2:
                    continue
                
                # Obtenir l'aspect avec fallback manuel pour North Node et Ascendant
                aspect = getAspect(obj1, obj2, const.MAJOR_ASPECTS)
                
                # Si flatlib ne détecte pas l'aspect, essayer manuellement (pour North Node, ASC, MC)
                if not aspect or not aspect.exists():
                    # Essayer avec notre override qui calcule manuellement
                    aspect = self._get_aspect_with_node_override(obj1, obj2, [
                        const.CONJUNCTION, const.SEXTILE, const.SQUARE, 
                        const.TRINE, const.OPPOSITION
                    ])
                
                if aspect and aspect.exists():
                    # Utiliser l'orbe approprié pour ce type d'aspect
                    aspect_orb = self.get_aspect_orb(aspect.type)
                    
                    # Si max_orb est spécifié, l'utiliser comme limite supérieure
                    if max_orb is not None:
                        aspect_orb = min(aspect_orb, max_orb)
                    
                    if aspect.orb <= aspect_orb:
                        # Gérer le mouvement (peut ne pas exister pour les aspects manuels)
                        try:
                            movement = aspect.movement()
                        except:
                            movement = "N/A"
                        
                        aspect_info = {
                            "planet1": self.planet_names.get(obj1_id, obj1_id),
                            "planet2": self.planet_names.get(obj2_id, obj2_id),
                            "aspect": self.aspect_names.get(aspect.type, "Unknown"),
                            "orb": round(aspect.orb, 1),
                            "movement": movement,
                            "planet1_position": f"{obj1.signlon:.1f}° {obj1.sign}",
                            "planet2_position": f"{obj2.signlon:.1f}° {obj2.sign}"
                        }
                        aspects.append(aspect_info)
        
        # Trier par orb croissant
        aspects.sort(key=lambda x: x["orb"])
        
        return aspects

    def _detect_t_square(self, chart, max_orb=8):
        """Détecte les T-Squares (2 oppositions + 2 carrés) - AVEC OVERRIDE pour bugs flatlib"""
        t_squares = []
        
        objects = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO,
            const.NORTH_NODE, const.ASC, const.MC
        ]
        
        for p1_id, p2_id, p3_id in itertools.permutations(objects, 3):
            obj1 = self._get_chart_object(chart, p1_id)
            obj2 = self._get_chart_object(chart, p2_id)
            obj3 = self._get_chart_object(chart, p3_id)

            if not (obj1 and obj2 and obj3):
                continue

            # Vérifier les aspects AVEC OVERRIDE pour contourner bugs flatlib (angles)
            asp12 = self._get_aspect_with_node_override(obj1, obj2, [const.OPPOSITION])
            asp13 = self._get_aspect_with_node_override(obj1, obj3, [const.SQUARE])
            asp23 = self._get_aspect_with_node_override(obj2, obj3, [const.SQUARE])

            if (asp12 and asp12.exists() and asp12.orb <= max_orb and
                asp13 and asp13.exists() and asp13.orb <= max_orb and
                asp23 and asp23.exists() and asp23.orb <= max_orb):
                
                t_squares.append({
                    "type": "T-Square",
                    "planets": [
                        {"name": self.planet_names.get(p1_id, p1_id), "position": f"{obj1.signlon:.1f}° {obj1.sign}"},
                        {"name": self.planet_names.get(p2_id, p2_id), "position": f"{obj2.signlon:.1f}° {obj2.sign}"},
                        {"name": self.planet_names.get(p3_id, p3_id), "position": f"{obj3.signlon:.1f}° {obj3.sign}"}
                    ],
                    "aspects": [
                        f"{self.planet_names.get(p1_id, p1_id)} {self.aspect_names.get(asp12.type, 'Unknown')} {self.planet_names.get(p2_id, p2_id)} (orb: {asp12.orb:.1f}°)",
                        f"{self.planet_names.get(p1_id, p1_id)} {self.aspect_names.get(asp13.type, 'Unknown')} {self.planet_names.get(p3_id, p3_id)} (orb: {asp13.orb:.1f}°)",
                        f"{self.planet_names.get(p2_id, p2_id)} {self.aspect_names.get(asp23.type, 'Unknown')} {self.planet_names.get(p3_id, p3_id)} (orb: {asp23.orb:.1f}°)"
                    ]
                })
        return t_squares

    def _get_element(self, sign):
        """Détermine l'élément d'un signe zodiacal"""
        fire = ['Aries', 'Leo', 'Sagittarius']
        earth = ['Taurus', 'Virgo', 'Capricorn']
        air = ['Gemini', 'Libra', 'Aquarius']
        water = ['Cancer', 'Scorpio', 'Pisces']
        
        if sign in fire:
            return "Fire"
        elif sign in earth:
            return "Earth"
        elif sign in air:
            return "Air"
        elif sign in water:
            return "Water"
        else:
            return "Unknown"

    def _detect_grand_trine(self, chart, max_orb=8):
        """Détecte les Grand Trines (3 planètes en trine mutuel dans le même élément)"""
        grand_trines = []
        
        objects = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO,
            const.NORTH_NODE, const.ASC, const.MC
        ]
        
        for p1_id, p2_id, p3_id in itertools.combinations(objects, 3):
            obj1 = self._get_chart_object(chart, p1_id)
            obj2 = self._get_chart_object(chart, p2_id)
            obj3 = self._get_chart_object(chart, p3_id)

            if not (obj1 and obj2 and obj3):
                continue

            # Vérifier les aspects (override flatlib restriction for North Node)
            asp12 = self._get_aspect_with_node_override(obj1, obj2, [const.TRINE])
            asp13 = self._get_aspect_with_node_override(obj1, obj3, [const.TRINE])
            asp23 = self._get_aspect_with_node_override(obj2, obj3, [const.TRINE])

            if (asp12 and asp12.exists() and asp12.orb <= max_orb and
                asp13 and asp13.exists() and asp13.orb <= max_orb and
                asp23 and asp23.exists() and asp23.orb <= max_orb):
                
                # Vérifier que les 3 planètes sont dans le même élément
                element1 = self._get_element(obj1.sign)
                element2 = self._get_element(obj2.sign)
                element3 = self._get_element(obj3.sign)
                
                # Un vrai Grand Trigone doit avoir les 3 planètes dans le même élément
                if element1 == element2 == element3 and element1 != "Unknown":
                    grand_trines.append({
                        "type": "Grand Trine",
                        "planets": [
                            {"name": self.planet_names.get(p1_id, p1_id), "position": f"{obj1.signlon:.1f}° {obj1.sign}"},
                            {"name": self.planet_names.get(p2_id, p2_id), "position": f"{obj2.signlon:.1f}° {obj2.sign}"},
                            {"name": self.planet_names.get(p3_id, p3_id), "position": f"{obj3.signlon:.1f}° {obj3.sign}"}
                        ],
                        "aspects": [
                            f"{self.planet_names.get(p1_id, p1_id)} {self.aspect_names.get(asp12.type, 'Unknown')} {self.planet_names.get(p2_id, p2_id)} (orb: {asp12.orb:.1f}°)",
                            f"{self.planet_names.get(p1_id, p1_id)} {self.aspect_names.get(asp13.type, 'Unknown')} {self.planet_names.get(p3_id, p3_id)} (orb: {asp13.orb:.1f}°)",
                            f"{self.planet_names.get(p2_id, p2_id)} {self.aspect_names.get(asp23.type, 'Unknown')} {self.planet_names.get(p3_id, p3_id)} (orb: {asp23.orb:.1f}°)"
                        ]
                    })
        return grand_trines

    def _detect_kite(self, chart, max_orb=8):
        """Détecte les configurations Kite (Grand Trigone + Opposition + 2 Sextiles)"""
        kites = []
        
        objects = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO,
            const.NORTH_NODE, const.ASC, const.MC
        ]
        
        # D'abord, trouver tous les Grand Trigones valides
        grand_trines = self._detect_grand_trine(chart, max_orb)
        
        for gt in grand_trines:
            # Extraire les 3 planètes du Grand Trigone
            gt_planets = [p["name"] for p in gt["planets"]]
            
            # Convertir les noms en IDs flatlib
            gt_ids = []
            for planet_name in gt_planets:
                # Trouver l'ID flatlib correspondant
                for flatlib_id, name in self.planet_names.items():
                    if name == planet_name:
                        gt_ids.append(flatlib_id)
                        break
            
            if len(gt_ids) != 3:
                continue
                
            # Obtenir les objets du Grand Trigone
            gt_obj1 = self._get_chart_object(chart, gt_ids[0])
            gt_obj2 = self._get_chart_object(chart, gt_ids[1])
            gt_obj3 = self._get_chart_object(chart, gt_ids[2])
            
            if not (gt_obj1 and gt_obj2 and gt_obj3):
                continue
            
            # Chercher une 4ème planète qui forme un Kite
            for p4_id in objects:
                if p4_id in gt_ids:
                    continue  # Éviter de reprendre une planète du Grand Trigone
                    
                p4_obj = self._get_chart_object(chart, p4_id)
                if not p4_obj:
                    continue
                
                # Vérifier si cette planète forme une opposition avec l'une des planètes du GT
                opposition_found = False
                opposition_planet = None
                
                for gt_obj in [gt_obj1, gt_obj2, gt_obj3]:
                    opp_aspect = self._get_aspect_with_node_override(p4_obj, gt_obj, [const.OPPOSITION])
                    if opp_aspect and opp_aspect.exists() and opp_aspect.orb <= max_orb:
                        opposition_found = True
                        opposition_planet = gt_obj
                        break
                
                if not opposition_found:
                    continue
                
                # Vérifier que la 4ème planète forme des sextiles avec les 2 autres planètes du GT
                sextile_count = 0
                sextile_planets = []
                
                for gt_obj in [gt_obj1, gt_obj2, gt_obj3]:
                    if gt_obj == opposition_planet:
                        continue  # Skip la planète en opposition
                        
                    sext_aspect = self._get_aspect_with_node_override(p4_obj, gt_obj, [const.SEXTILE])
                    if sext_aspect and sext_aspect.exists() and sext_aspect.orb <= max_orb:
                        sextile_count += 1
                        sextile_planets.append(gt_obj)
                
                # Si on a exactement 2 sextiles, on a un Kite !
                if sextile_count == 2:
                    p4_name = self.planet_names.get(p4_id, str(p4_id))
                    
                    kites.append({
                        "type": "Cerf-volant",
                        "planets": [
                            {"name": self.planet_names.get(gt_ids[0], str(gt_ids[0])), "position": f"{gt_obj1.signlon:.1f}° {gt_obj1.sign}"},
                            {"name": self.planet_names.get(gt_ids[1], str(gt_ids[1])), "position": f"{gt_obj2.signlon:.1f}° {gt_obj2.sign}"},
                            {"name": self.planet_names.get(gt_ids[2], str(gt_ids[2])), "position": f"{gt_obj3.signlon:.1f}° {gt_obj3.sign}"},
                            {"name": p4_name, "position": f"{p4_obj.signlon:.1f}° {p4_obj.sign}"}
                        ],
                        "aspects": [
                            f"Grand Trigone: {gt_planets[0]}, {gt_planets[1]}, {gt_planets[2]}",
                            f"Opposition: {p4_name} Opposition {self.planet_names.get(opposition_planet.id, str(opposition_planet.id))}",
                            f"Sextiles: {p4_name} Sextile {self.planet_names.get(sextile_planets[0].id, str(sextile_planets[0].id))}, {self.planet_names.get(sextile_planets[1].id, str(sextile_planets[1].id))}"
                        ]
                    })
        
        return kites

    def _detect_cradle(self, chart, max_orb=8):
        """Détecte les configurations Cradle/Berceau (opposition + 2 paires harmonieuses trine/sextile)"""
        cradles = []
        
        objects = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO,
            const.NORTH_NODE, const.ASC, const.MC
        ]
        
        # Chercher toutes les combinaisons de 4 planètes
        for combo in itertools.combinations(objects, 4):
            objs = []
            for planet_id in combo:
                obj = self._get_chart_object(chart, planet_id)
                if not obj:
                    break
                objs.append((planet_id, obj))
            
            if len(objs) != 4:
                continue
            
            # Essayer toutes les configurations possibles pour trouver un cradle
            # Un cradle a 1 opposition + 4 aspects harmonieux (2 trines + 2 sextiles)
            for i in range(4):
                for j in range(i+1, 4):
                    # Tester si objs[i] et objs[j] sont en opposition
                    p1_id, obj1 = objs[i]
                    p2_id, obj2 = objs[j]
                    
                    opp_asp = self._get_aspect_with_node_override(obj1, obj2, [const.OPPOSITION])
                    if not opp_asp or not opp_asp.exists() or opp_asp.orb > max_orb:
                        continue
                    
                    # Obtenir les 2 autres planètes
                    others = [objs[k] for k in range(4) if k != i and k != j]
                    if len(others) != 2:
                        continue
                    
                    p3_id, obj3 = others[0]
                    p4_id, obj4 = others[1]
                    
                    # Vérifier les 2 configurations possibles de cradle
                    # Config 1: obj3 trine obj1, sextile obj2; obj4 sextile obj1, trine obj2
                    asp31 = self._get_aspect_with_node_override(obj3, obj1, [const.TRINE])
                    asp32 = self._get_aspect_with_node_override(obj3, obj2, [const.SEXTILE])
                    asp41 = self._get_aspect_with_node_override(obj4, obj1, [const.SEXTILE])
                    asp42 = self._get_aspect_with_node_override(obj4, obj2, [const.TRINE])
                    
                    if (asp31 and asp31.exists() and asp31.orb <= max_orb and
                        asp32 and asp32.exists() and asp32.orb <= max_orb and
                        asp41 and asp41.exists() and asp41.orb <= max_orb and
                        asp42 and asp42.exists() and asp42.orb <= max_orb):
                        
                        cradles.append({
                            "type": "Berceau",
                            "planets": [
                                {"name": self.planet_names.get(p1_id, str(p1_id)), "position": f"{obj1.signlon:.1f}° {obj1.sign}"},
                                {"name": self.planet_names.get(p2_id, str(p2_id)), "position": f"{obj2.signlon:.1f}° {obj2.sign}"},
                                {"name": self.planet_names.get(p3_id, str(p3_id)), "position": f"{obj3.signlon:.1f}° {obj3.sign}"},
                                {"name": self.planet_names.get(p4_id, str(p4_id)), "position": f"{obj4.signlon:.1f}° {obj4.sign}"}
                            ],
                            "aspects": [
                                f"Opposition: {self.planet_names.get(p1_id, str(p1_id))} - {self.planet_names.get(p2_id, str(p2_id))} (orb: {opp_asp.orb:.1f}°)",
                                f"Trine: {self.planet_names.get(p3_id, str(p3_id))} - {self.planet_names.get(p1_id, str(p1_id))} (orb: {asp31.orb:.1f}°)",
                                f"Sextile: {self.planet_names.get(p3_id, str(p3_id))} - {self.planet_names.get(p2_id, str(p2_id))} (orb: {asp32.orb:.1f}°)",
                                f"Sextile: {self.planet_names.get(p4_id, str(p4_id))} - {self.planet_names.get(p1_id, str(p1_id))} (orb: {asp41.orb:.1f}°)",
                                f"Trine: {self.planet_names.get(p4_id, str(p4_id))} - {self.planet_names.get(p2_id, str(p2_id))} (orb: {asp42.orb:.1f}°)"
                            ]
                        })
                        continue
                    
                    # Config 2: obj3 sextile obj1, trine obj2; obj4 trine obj1, sextile obj2
                    asp31_b = self._get_aspect_with_node_override(obj3, obj1, [const.SEXTILE])
                    asp32_b = self._get_aspect_with_node_override(obj3, obj2, [const.TRINE])
                    asp41_b = self._get_aspect_with_node_override(obj4, obj1, [const.TRINE])
                    asp42_b = self._get_aspect_with_node_override(obj4, obj2, [const.SEXTILE])
                    
                    if (asp31_b and asp31_b.exists() and asp31_b.orb <= max_orb and
                        asp32_b and asp32_b.exists() and asp32_b.orb <= max_orb and
                        asp41_b and asp41_b.exists() and asp41_b.orb <= max_orb and
                        asp42_b and asp42_b.exists() and asp42_b.orb <= max_orb):
                        
                        cradles.append({
                            "type": "Berceau",
                            "planets": [
                                {"name": self.planet_names.get(p1_id, str(p1_id)), "position": f"{obj1.signlon:.1f}° {obj1.sign}"},
                                {"name": self.planet_names.get(p2_id, str(p2_id)), "position": f"{obj2.signlon:.1f}° {obj2.sign}"},
                                {"name": self.planet_names.get(p3_id, str(p3_id)), "position": f"{obj3.signlon:.1f}° {obj3.sign}"},
                                {"name": self.planet_names.get(p4_id, str(p4_id)), "position": f"{obj4.signlon:.1f}° {obj4.sign}"}
                            ],
                            "aspects": [
                                f"Opposition: {self.planet_names.get(p1_id, str(p1_id))} - {self.planet_names.get(p2_id, str(p2_id))} (orb: {opp_asp.orb:.1f}°)",
                                f"Sextile: {self.planet_names.get(p3_id, str(p3_id))} - {self.planet_names.get(p1_id, str(p1_id))} (orb: {asp31_b.orb:.1f}°)",
                                f"Trine: {self.planet_names.get(p3_id, str(p3_id))} - {self.planet_names.get(p2_id, str(p2_id))} (orb: {asp32_b.orb:.1f}°)",
                                f"Trine: {self.planet_names.get(p4_id, str(p4_id))} - {self.planet_names.get(p1_id, str(p1_id))} (orb: {asp41_b.orb:.1f}°)",
                                f"Sextile: {self.planet_names.get(p4_id, str(p4_id))} - {self.planet_names.get(p2_id, str(p2_id))} (orb: {asp42_b.orb:.1f}°)"
                            ]
                        })
        
        return cradles

    def _find_planet_id(self, flatlib_id):
        """Trouve l'ID dans notre mapping à partir de l'ID flatlib"""
        for our_id, flatlib_const in self.planet_names.items():
            if flatlib_const == flatlib_id:
                return our_id
        return flatlib_id

    def _detect_grand_square(self, chart, max_orb=8):
        """Détecte les Grand Squares (4 planètes formant un carré)"""
        grand_squares = []
        
        objects = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO,
            const.NORTH_NODE, const.ASC, const.MC
        ]
        
        for p1_id, p2_id, p3_id, p4_id in itertools.combinations(objects, 4):
            obj1 = self._get_chart_object(chart, p1_id)
            obj2 = self._get_chart_object(chart, p2_id)
            obj3 = self._get_chart_object(chart, p3_id)
            obj4 = self._get_chart_object(chart, p4_id)

            if not (obj1 and obj2 and obj3 and obj4):
                continue

            # Un Grand Square nécessite 4 planètes formant un carré géométrique
            # avec 2 oppositions et 2 carrés, disposées à 90° les unes des autres
            
            # Obtenir les positions des planètes
            pos1 = obj1.lon
            pos2 = obj2.lon
            pos3 = obj3.lon
            pos4 = obj4.lon
            
            # Vérifier que les planètes forment un carré géométrique
            # Pour cela, on doit avoir exactement 2 oppositions et 2 carrés
            aspects = []
            
            # Calculer tous les aspects entre les 4 planètes
            asp12 = getAspect(obj1, obj2, [const.OPPOSITION, const.SQUARE])
            asp13 = getAspect(obj1, obj3, [const.OPPOSITION, const.SQUARE])
            asp14 = getAspect(obj1, obj4, [const.OPPOSITION, const.SQUARE])
            asp23 = getAspect(obj2, obj3, [const.OPPOSITION, const.SQUARE])
            asp24 = getAspect(obj2, obj4, [const.OPPOSITION, const.SQUARE])
            asp34 = getAspect(obj3, obj4, [const.OPPOSITION, const.SQUARE])
            
            # Compter les oppositions et carrés valides
            oppositions = 0
            squares = 0
            
            if asp12 and asp12.exists() and asp12.orb <= max_orb:
                if asp12.type == const.OPPOSITION:
                    oppositions += 1
                elif asp12.type == const.SQUARE:
                    squares += 1
                aspects.append((obj1, obj2, asp12))
                    
            if asp13 and asp13.exists() and asp13.orb <= max_orb:
                if asp13.type == const.OPPOSITION:
                    oppositions += 1
                elif asp13.type == const.SQUARE:
                    squares += 1
                aspects.append((obj1, obj3, asp13))
                    
            if asp14 and asp14.exists() and asp14.orb <= max_orb:
                if asp14.type == const.OPPOSITION:
                    oppositions += 1
                elif asp14.type == const.SQUARE:
                    squares += 1
                aspects.append((obj1, obj4, asp14))
                    
            if asp23 and asp23.exists() and asp23.orb <= max_orb:
                if asp23.type == const.OPPOSITION:
                    oppositions += 1
                elif asp23.type == const.SQUARE:
                    squares += 1
                aspects.append((obj2, obj3, asp23))
                    
            if asp24 and asp24.exists() and asp24.orb <= max_orb:
                if asp24.type == const.OPPOSITION:
                    oppositions += 1
                elif asp24.type == const.SQUARE:
                    squares += 1
                aspects.append((obj2, obj4, asp24))
                    
            if asp34 and asp34.exists() and asp34.orb <= max_orb:
                if asp34.type == const.OPPOSITION:
                    oppositions += 1
                elif asp34.type == const.SQUARE:
                    squares += 1
                aspects.append((obj3, obj4, asp34))

            # Un Grand Square nécessite exactement 2 oppositions et 2 carrés
            # ET une disposition géométrique spécifique (4 planètes à 90° les unes des autres)
            # Pour vérifier cela, on s'assure que les oppositions ne partagent pas les mêmes planètes
            # et que les carrés connectent les bonnes paires
            if oppositions == 2 and squares == 2:
                # Vérifier la géométrie : dans un vrai Grand Square, 
                # les 2 oppositions doivent être perpendiculaires (non connectées)
                # et les 2 carrés doivent relier les bonnes paires
                
                # Extraire les paires en opposition et en carré
                opposition_pairs = []
                square_pairs = []
                
                for obj1, obj2, asp in aspects:
                    if asp.type == const.OPPOSITION:
                        opposition_pairs.append((obj1.id, obj2.id))
                    elif asp.type == const.SQUARE:
                        square_pairs.append((obj1.id, obj2.id))
                
                # Dans un vrai Grand Square, les oppositions ne doivent pas partager de planètes
                # et les carrés doivent connecter les bonnes paires
                if len(opposition_pairs) == 2 and len(square_pairs) == 2:
                    # Vérifier que les oppositions sont perpendiculaires (pas de planète commune)
                    opp1_planets = set(opposition_pairs[0])
                    opp2_planets = set(opposition_pairs[1])
                    
                    if len(opp1_planets.intersection(opp2_planets)) == 0:
                        # Les oppositions sont perpendiculaires, c'est un vrai Grand Square
                        grand_squares.append({
                            "type": "Grand Square",
                            "planets": [
                                {"name": self.planet_names.get(p1_id, p1_id), "position": f"{obj1.signlon:.1f}° {obj1.sign}"},
                                {"name": self.planet_names.get(p2_id, p2_id), "position": f"{obj2.signlon:.1f}° {obj2.sign}"},
                                {"name": self.planet_names.get(p3_id, p3_id), "position": f"{obj3.signlon:.1f}° {obj3.sign}"},
                                {"name": self.planet_names.get(p4_id, p4_id), "position": f"{obj4.signlon:.1f}° {obj4.sign}"}
                            ],
                            "aspects": [f"{self.planet_names.get(obj1.id, obj1.id)} {self.aspect_names.get(asp.type, 'Unknown')} {self.planet_names.get(obj2.id, obj2.id)} (orb: {asp.orb:.1f}°)" for obj1, obj2, asp in aspects]
                        })
        
        return grand_squares

    def _detect_stelliums(self, chart, conjunction_orb=8):
        """Détecte les stelliums en groupant les planètes connectées par conjonctions.
        
        Un stellium est un groupe de 3+ planètes où chaque planète est en conjonction 
        avec au moins une autre planète du groupe (connexité par conjonctions).
        Tous les groupes de planètes connectées sont regroupés en UN SEUL stellium.
        """
        stelliums = []
        
        # Définir les planètes personnelles (essentielles pour un stellium)
        personal_planets = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS]
        # Définir les planètes sociales (optionnelles)
        social_planets = [const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO]
        
        # Toutes les planètes à considérer
        all_planet_ids = personal_planets + social_planets
        
        # Obtenir toutes les planètes avec leurs positions
        planets_data = []
        for obj_id in all_planet_ids:
            obj = self._get_chart_object(chart, obj_id)
            if obj:
                planets_data.append({
                    "id": obj_id,
                    "obj": obj,
                    "name": self.planet_names.get(obj_id, obj_id),
                    "position": f"{obj.signlon:.1f}°",
                    "sign": obj.sign,
                    "lon": obj.lon,
                    "is_personal": obj_id in personal_planets
                })
        
        # Étape 1: Construire un graphe de connexions par conjonctions
        def angular_distance(lon1, lon2):
            """Calcule la distance angulaire entre deux longitudes (0-180°)"""
            diff = abs(lon1 - lon2)
            if diff > 180:
                diff = 360 - diff
            return diff
        
        # Créer un dictionnaire des connexions (qui est en conjonction avec qui)
        connections = {}
        for i, planet1 in enumerate(planets_data):
            connections[planet1["name"]] = []
            for j, planet2 in enumerate(planets_data):
                if i != j:
                    distance = angular_distance(planet1["lon"], planet2["lon"])
                    if distance <= conjunction_orb:
                        connections[planet1["name"]].append(planet2["name"])
        
        # Étape 2: Trouver les composantes connexes (groupes de planètes connectées)
        def find_connected_component(start_planet, visited, connections):
            """Trouve toutes les planètes connectées à start_planet via des conjonctions"""
            component = []
            stack = [start_planet]
            
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                    
                visited.add(current)
                component.append(current)
                
                # Ajouter toutes les planètes en conjonction avec la planète courante
                for neighbor in connections.get(current, []):
                    if neighbor not in visited:
                        stack.append(neighbor)
            
            return component
        
        # Trouver tous les groupes connexes
        visited = set()
        connected_components = []
        
        for planet_data in planets_data:
            planet_name = planet_data["name"]
            if planet_name not in visited:
                component = find_connected_component(planet_name, visited, connections)
                if len(component) >= 3:  # Un stellium nécessite au moins 3 planètes
                    connected_components.append(component)
        
        # Étape 3: Valider et formater les stelliums
        for component in connected_components:
            # Vérifier qu'au moins une planète personnelle est dans le stellium
            has_personal = False
            component_planets_data = []
            
            for planet_name in component:
                # Trouver les données de cette planète
                for planet_data in planets_data:
                    if planet_data["name"] == planet_name:
                        component_planets_data.append(planet_data)
                        if planet_data["is_personal"]:
                            has_personal = True
                        break
            
            # Un stellium valide doit contenir au moins une planète personnelle
            if has_personal and len(component_planets_data) >= 3:
                # Trier les planètes par longitude pour un ordre cohérent
                component_planets_data.sort(key=lambda p: p["lon"])
                
                stellium = {
                    "type": "Stellium",
                    "sign": component_planets_data[0]["sign"],  # Signe de la première planète
                    "planets": [{"name": p["name"], "position": p["position"]} for p in component_planets_data],
                    "count": len(component_planets_data),
                    "personal_count": sum(1 for p in component_planets_data if p["is_personal"])
                }
                stelliums.append(stellium)
        
        return stelliums

    def _detect_multiple_aspects(self, chart, max_orb=8):
        """Détecte les patterns d'aspects multiples (plusieurs planètes en aspect avec une même planète)"""
        multiple_aspects = []
        
        objects = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO,
            const.NORTH_NODE, const.ASC, const.MC
        ]
        
        for target_id in objects:
            target_obj = self._get_chart_object(chart, target_id)
            if not target_obj:
                continue
            
            aspecting_planets = []
            for other_id in objects:
                if target_id == other_id:
                    continue
                
                other_obj = self._get_chart_object(chart, other_id)
                if not other_obj:
                    continue
                
                aspect = getAspect(target_obj, other_obj, const.MAJOR_ASPECTS)
                if aspect and aspect.exists() and aspect.orb <= max_orb:
                    aspecting_planets.append({
                        "planet": self.planet_names.get(other_id, other_id),
                        "aspect": self.aspect_names.get(aspect.type, "Unknown"),
                        "orb": round(aspect.orb, 1),
                        "position": f"{other_obj.signlon:.1f}° {other_obj.sign}"
                    })
            
            if len(aspecting_planets) >= 2:  # Au moins deux planètes aspectent la cible
                multiple_aspects.append({
                    "type": "Multiple Aspect",
                    "target_planet": self.planet_names.get(target_id, target_id),
                    "target_position": f"{target_obj.signlon:.1f}° {target_obj.sign}",
                    "aspecting_planets": aspecting_planets
                })
        return multiple_aspects

    def _detect_multiple_planet_square(self, chart, max_orb=8, cluster_orb=15):
        """Détecte les Multiple Planet Square: deux groupes de planètes proches formant un carré entre eux
        
        Un Multiple Planet Square valide nécessite:
        - Groupe A: 2+ planètes proches (dans un cluster de cluster_orb degrés)
        - Groupe B: 2+ planètes proches (dans un cluster de cluster_orb degrés)  
        - Les deux groupes sont en carré (90° apart)
        """
        multiple_planet_squares = []
        
        objects = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO,
            const.NORTH_NODE, const.ASC, const.MC
        ]
        
        def angular_distance(lon1, lon2):
            """Calcule la distance angulaire entre deux longitudes (0-180°)"""
            diff = abs(lon1 - lon2)
            if diff > 180:
                diff = 360 - diff
            return diff
        
        # Étape 1: Identifier tous les groupes de planètes proches (2+ planètes)
        cluster_groups = []
        
        for size in range(6, 1, -1):  # De 6 à 2 planètes
            for combo in itertools.combinations(objects, size):
                objs = []
                for planet_id in combo:
                    obj = self._get_chart_object(chart, planet_id)
                    if obj:
                        objs.append((planet_id, obj))
                
                if len(objs) < 2:
                    continue
                
                # Vérifier si toutes les planètes sont proches les unes des autres (cluster)
                all_in_cluster = True
                for i in range(len(objs)):
                    for j in range(i+1, len(objs)):
                        p1_id, obj1 = objs[i]
                        p2_id, obj2 = objs[j]
                        
                        # Vérifier la distance angulaire
                        distance = angular_distance(obj1.lon, obj2.lon)
                        if distance > cluster_orb:
                            all_in_cluster = False
                            break
                    
                    if not all_in_cluster:
                        break
                
                if all_in_cluster:
                    # Vérifier que ce groupe n'est pas déjà inclus dans un groupe plus grand
                    is_subset = False
                    for existing_group in cluster_groups:
                        existing_ids = set([p[0] for p in existing_group])
                        current_ids = set([p[0] for p in objs])
                        if current_ids.issubset(existing_ids):
                            is_subset = True
                            break
                    
                    if not is_subset:
                        # Retirer les groupes qui sont des sous-ensembles de celui-ci
                        cluster_groups = [g for g in cluster_groups 
                                         if not set([p[0] for p in g]).issubset(set([p[0] for p in objs]))]
                        cluster_groups.append(objs)
        
        # Étape 2: Trouver les paires de groupes qui sont en carré
        for i in range(len(cluster_groups)):
            for j in range(i+1, len(cluster_groups)):
                group_a = cluster_groups[i]
                group_b = cluster_groups[j]
                
                # Compter le nombre de carrés entre les deux groupes
                square_count = 0
                square_aspects = []
                
                for p1_id, obj1 in group_a:
                    for p2_id, obj2 in group_b:
                        asp = self._get_aspect_with_node_override(obj1, obj2, [const.SQUARE])
                        if asp and asp.exists() and asp.orb <= max_orb:
                            square_count += 1
                            square_aspects.append({
                                "p1": self.planet_names.get(p1_id, str(p1_id)),
                                "p2": self.planet_names.get(p2_id, str(p2_id)),
                                "orb": asp.orb
                            })
                
                # Si au moins 2 carrés entre les groupes (configuration significative)
                if square_count >= 2:
                    all_planets = group_a + group_b
                    planet_list = []
                    for p_id, obj in all_planets:
                        planet_list.append({
                            "name": self.planet_names.get(p_id, str(p_id)),
                            "position": f"{obj.signlon:.1f}° {obj.sign}"
                        })
                    
                    aspects_list = []
                    for sa in square_aspects:
                        aspects_list.append(f"{sa['p1']} Square {sa['p2']} (orb: {sa['orb']:.1f}°)")
                    
                    multiple_planet_squares.append({
                        "type": "Multiple Planet Square",
                        "planets": planet_list,
                        "square_count": square_count,
                        "aspects": aspects_list,
                        "group_a_size": len(group_a),
                        "group_b_size": len(group_b)
                    })
        
        # Trier par nombre de carrés et taille des groupes (les plus complexes d'abord)
        multiple_planet_squares.sort(key=lambda x: (x.get("square_count", 0), 
                                                     x.get("group_a_size", 0) + x.get("group_b_size", 0)), 
                                     reverse=True)
        
        # Filtrer les doublons
        unique_squares = []
        seen = set()
        for mps in multiple_planet_squares:
            planets = tuple(sorted([p["name"] for p in mps["planets"]]))
            if planets not in seen:
                seen.add(planets)
                unique_squares.append(mps)
        
        return unique_squares[:1]  # Garder uniquement le plus complexe

    def _detect_yod(self, chart, max_orb=8):
        """Détecte les Yods (2 sextiles + 2 quinconces) - AVEC OVERRIDE pour bugs flatlib
        
        Note: Les Yods utilisent uniquement les PLANÈTES, pas les angles (Ascendant/MC)
        """
        yods = []
        
        # Yods: planètes uniquement (pas d'angles)
        objects = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO,
            const.NORTH_NODE
        ]
        
        for p1_id, p2_id, p3_id in itertools.permutations(objects, 3):
            obj1 = self._get_chart_object(chart, p1_id)
            obj2 = self._get_chart_object(chart, p2_id)
            obj3 = self._get_chart_object(chart, p3_id)
            
            if not (obj1 and obj2 and obj3):
                continue
            
            # Vérifier les aspects AVEC OVERRIDE pour contourner bugs flatlib
            asp12 = self._get_aspect_with_node_override(obj1, obj2, [const.SEXTILE])
            asp13 = self._get_aspect_with_node_override(obj1, obj3, [const.QUINCUNX])
            asp23 = self._get_aspect_with_node_override(obj2, obj3, [const.QUINCUNX])
            
            if (asp12 and asp12.exists() and asp12.orb <= max_orb and
                asp13 and asp13.exists() and asp13.orb <= max_orb and
                asp23 and asp23.exists() and asp23.orb <= max_orb):
                
                yods.append({
                    "type": "Yod",
                    "planets": [
                        {"name": self.planet_names.get(p1_id, p1_id), "position": f"{obj1.signlon:.1f}° {obj1.sign}"},
                        {"name": self.planet_names.get(p2_id, p2_id), "position": f"{obj2.signlon:.1f}° {obj2.sign}"},
                        {"name": self.planet_names.get(p3_id, p3_id), "position": f"{obj3.signlon:.1f}° {obj3.sign}"}
                    ],
                    "aspects": [
                        f"{self.planet_names.get(p1_id, p1_id)} {self.aspect_names.get(asp12.type, 'Unknown')} {self.planet_names.get(p2_id, p2_id)} (orb: {asp12.orb:.1f}°)",
                        f"{self.planet_names.get(p1_id, p1_id)} {self.aspect_names.get(asp13.type, 'Unknown')} {self.planet_names.get(p3_id, p3_id)} (orb: {asp13.orb:.1f}°)",
                        f"{self.planet_names.get(p2_id, p2_id)} {self.aspect_names.get(asp23.type, 'Unknown')} {self.planet_names.get(p3_id, p3_id)} (orb: {asp23.orb:.1f}°)"
                    ]
                })
        
        return yods

    def _calculate_planetary_importance_score(self, planet_names):
        """Calcule un score d'importance basé sur la hiérarchie astrologique"""
        importance_values = {
            # Angles (priorité maximale)
            "Ascendant": 10,
            "MC": 10,
            # Luminaires (très haute priorité)
            "Sun": 8,
            "Moon": 8,
            # Planètes personnelles (priorité moyenne)
            "Mercury": 5,
            "Venus": 5,
            "Mars": 5,
            # Planètes sociales (priorité basse)
            "Jupiter": 3,
            "Saturn": 3,
            # Planètes transpersonnelles (Neptune prioritaire pour Yods)
            "Neptune": 2.2,  # Légèrement prioritaire (spiritualité)
            "Pluto": 2.1,    # Transformation
            "Uranus": 2.0,   # Changement soudain
            # Nœuds
            "North Node": 1,
            "South Node": 1
        }
        
        total_importance = sum(importance_values.get(name, 0) for name in planet_names)
        avg_importance = total_importance / len(planet_names) if planet_names else 0
        return avg_importance
    
    def _filter_yods(self, yods):
        """Filtre les Yods pour maximiser le nombre de Yods sans chevauchement
        
        NOUVELLE RÈGLE: Un même planète ne peut apparaître que dans UN SEUL Yod.
        L'objectif est de maximiser le nombre de Yods trouvés.
        """
        if not yods:
            return []
        
        # Calculer les scores pour tous les Yods
        for yod in yods:
            planets = [p["name"] for p in yod["planets"]]
            
            # Calculer l'orbe moyen
            orb_sum = 0
            orb_count = 0
            for aspect_str in yod.get("aspects", []):
                if "orb:" in aspect_str:
                    orb_val = float(aspect_str.split("orb:")[1].strip().replace("°)", ""))
                    orb_sum += orb_val
                    orb_count += 1
            yod["avg_orb"] = orb_sum / orb_count if orb_count > 0 else 999
            
            # Calculer l'importance astrologique
            yod["importance"] = self._calculate_planetary_importance_score(planets)
            
            # Score composite : importance élevée - pénalité d'orbe réduite
            yod["composite_score"] = yod["importance"] - (yod["avg_orb"] * 0.15)
        
        # Étape 1: Éliminer les doublons exacts (mêmes 3 planètes, ordre différent)
        seen_planet_sets = {}
        unique_yods = []
        
        for yod in yods:
            planets = frozenset([p["name"] for p in yod["planets"]])
            if planets not in seen_planet_sets:
                seen_planet_sets[planets] = yod
                unique_yods.append(yod)
        
        # Filtrer pour garder seulement les Yods avec orbes serrés
        significant_yods = [y for y in unique_yods if y.get("avg_orb", 999) < 6]
        
        if not significant_yods:
            return []
        
        # Étape 2: Trouver la combinaison optimale de Yods sans chevauchement
        # Algorithme: recherche exhaustive pour maximiser le nombre de Yods
        
        def get_planet_set(yod):
            """Retourne l'ensemble des planètes d'un Yod"""
            return set([p["name"] for p in yod["planets"]])
        
        def yods_overlap(yod1, yod2):
            """Vérifie si deux Yods partagent au moins une planète"""
            return len(get_planet_set(yod1) & get_planet_set(yod2)) > 0
        
        def find_best_combination(yods_list):
            """Trouve la meilleure combinaison de Yods non-chevauchants
            Priorité: 1) Maximiser le nombre de Yods, 2) Maximiser le score total"""
            from itertools import combinations
            
            best_combo = []
            best_score = -999999
            
            # Tester toutes les combinaisons possibles de taille décroissante
            for size in range(len(yods_list), 0, -1):
                found_valid = False
                
                for combo in combinations(yods_list, size):
                    # Vérifier que les Yods ne se chevauchent pas
                    valid = True
                    for i in range(len(combo)):
                        for j in range(i+1, len(combo)):
                            if yods_overlap(combo[i], combo[j]):
                                valid = False
                                break
                        if not valid:
                            break
                    
                    if valid:
                        found_valid = True
                        # Calculer le score total de cette combinaison
                        total_score = sum(y["composite_score"] for y in combo)
                        
                        if total_score > best_score:
                            best_score = total_score
                            best_combo = list(combo)
                
                # Si on a trouvé des combinaisons valides de cette taille, on s'arrête
                # (on veut maximiser le NOMBRE de Yods)
                if found_valid:
                    break
            
            return best_combo
        
        # Trouver la meilleure combinaison
        selected_yods = find_best_combination(significant_yods)
        
        # Trier par score composite
        selected_yods.sort(key=lambda x: x.get("composite_score", -999), reverse=True)
        
        return selected_yods

    def _filter_t_squares(self, t_squares):
        """Filtre les T-Squares pour éviter les doublons"""
        if not t_squares:
            return []
        
        # Créer des ensembles de planètes triés pour détecter les doublons
        unique_patterns = []
        seen_patterns = set()
        
        for t_square in t_squares:
            planets = [p["name"] for p in t_square["planets"]]
            # Créer une clé unique basée sur les planètes triées
            pattern_key = tuple(sorted(planets))
            
            if pattern_key not in seen_patterns:
                seen_patterns.add(pattern_key)
                unique_patterns.append(t_square)
        
        return unique_patterns

    def _filter_stelliums(self, stelliums):
        """Filtre les stelliums pour ne garder que les plus significatifs"""
        if not stelliums:
            return []
        
        # Ne garder que le stellium avec le plus de planètes
        max_planets = max(len(s["planets"]) for s in stelliums)
        return [s for s in stelliums if len(s["planets"]) == max_planets]
    
    def _filter_cradles(self, cradles):
        """Filtre les cradles en privilégiant l'importance astrologique ET les orbes serrés
        
        Si plusieurs Cradles partagent 3 planètes identiques, garde seulement celui avec 
        la 4ème planète la plus importante et les orbes les plus serrés.
        """
        if not cradles:
            return []
        
        # Calculer les scores pour tous les Cradles
        for cradle in cradles:
            planets = [p["name"] for p in cradle["planets"]]
            
            # Calculer l'orbe moyen
            orb_sum = 0
            orb_count = 0
            for aspect_str in cradle.get("aspects", []):
                if "orb:" in aspect_str:
                    orb_val = float(aspect_str.split("orb:")[1].strip().replace("°)", ""))
                    orb_sum += orb_val
                    orb_count += 1
            cradle["avg_orb"] = orb_sum / orb_count if orb_count > 0 else 999
            
            # Calculer l'importance astrologique
            cradle["importance"] = self._calculate_planetary_importance_score(planets)
            
            # Score composite : importance élevée - pénalité d'orbe réduite
            cradle["composite_score"] = cradle["importance"] - (cradle["avg_orb"] * 0.15)
        
        # Étape 1: Éliminer les doublons exacts (mêmes 4 planètes, ordre différent)
        seen_planet_sets = {}
        unique_cradles = []
        
        for cradle in cradles:
            planets = frozenset([p["name"] for p in cradle["planets"]])
            if planets not in seen_planet_sets:
                seen_planet_sets[planets] = cradle
                unique_cradles.append(cradle)
        
        # Étape 2: Comparer les paires de Cradles pour détecter les conflits
        # Deux cradles sont en conflit s'ils partagent EXACTEMENT 3 planètes
        excluded_cradles = set()
        
        for i, cradle1 in enumerate(unique_cradles):
            if id(cradle1) in excluded_cradles:
                continue
                
            planets1 = set([p["name"] for p in cradle1["planets"]])
            
            for j, cradle2 in enumerate(unique_cradles):
                if i >= j or id(cradle2) in excluded_cradles:
                    continue
                
                planets2 = set([p["name"] for p in cradle2["planets"]])
                
                # Compter les planètes partagées
                shared_planets = planets1 & planets2
                
                # Si exactement 3 planètes sont partagées, il y a conflit
                if len(shared_planets) == 3:
                    # Garder celui avec le meilleur composite score
                    if cradle1["composite_score"] >= cradle2["composite_score"]:
                        excluded_cradles.add(id(cradle2))
                    else:
                        excluded_cradles.add(id(cradle1))
                        break  # cradle1 est exclu, pas besoin de continuer
        
        # Sélectionner tous les Cradles non exclus
        selected_cradles = [cradle for cradle in unique_cradles if id(cradle) not in excluded_cradles]
        
        # Trier par score composite
        selected_cradles.sort(key=lambda x: x.get("composite_score", -999), reverse=True)
        
        # Ne garder que les 2 Cradles les plus significatifs avec orbes serrés
        significant = [c for c in selected_cradles if c.get("avg_orb", 999) < 7]
        return significant[:2]

    def detect_patterns(self, chart, max_orb=8):
        """Détecte les patterns astrologiques principaux - ordre de priorité optimisé"""
        patterns = []
        
        # Détecter les patterns avec filtrage
        t_squares = self._detect_t_square(chart, max_orb)
        grand_trines = self._detect_grand_trine(chart, max_orb)
        grand_squares = self._detect_grand_square(chart, max_orb)
        kites = self._detect_kite(chart, max_orb)
        cradles = self._detect_cradle(chart, max_orb)
        stelliums = self._detect_stelliums(chart)
        multiple_planet_squares = self._detect_multiple_planet_square(chart, max_orb)
        yods = self._detect_yod(chart, max_orb)
        
        # Appliquer les filtres dans l'ordre de priorité (configurations majeures)
        patterns.extend(self._filter_t_squares(t_squares))  # T-Squares (tension/conflit)
        patterns.extend(multiple_planet_squares)  # Multiple Planet Squares (complexité)
        patterns.extend(self._filter_yods(yods))  # Yods (mission spéciale)
        patterns.extend(self._filter_cradles(cradles))  # Cradles (soutien harmonieux)
        patterns.extend(grand_trines)  # Grand Trines (facilité/talent)
        patterns.extend(kites)  # Cerf-volants (potentiel dirigé)
        patterns.extend(grand_squares)  # Grand Squares (tension maximale)
        patterns.extend(self._filter_stelliums(stelliums))  # Stelliums (concentration)
        
        # Ne pas limiter - retourner tous les patterns significatifs détectés
        return patterns

    def distribute_mentions_optimally(self, aspects, patterns):
        """Distribue les mentions d'aspects et de configurations de manière équilibrée
        
        Règles:
        - Chaque aspect (2 planètes) → mentionné pour 1 SEULE planète
        - Chaque configuration (3+ planètes) → mentionnée pour EXACTEMENT 2 planètes
        
        Objectif: Minimiser Max (nombre max de mentions) et maximiser Min (nombre min de mentions)
        pour équilibrer la charge entre toutes les planètes
        """
        
        # Liste de toutes les planètes impliquées
        all_planets = set()
        
        # Extraire toutes les planètes des aspects
        for aspect in aspects:
            all_planets.add(aspect['planet1'])
            all_planets.add(aspect['planet2'])
        
        # Extraire toutes les planètes des configurations
        for pattern in patterns:
            if 'planets' in pattern:
                for planet in pattern['planets']:
                    if isinstance(planet, dict) and 'name' in planet:
                        all_planets.add(planet['name'])
            elif 'target_planet' in pattern:
                all_planets.add(pattern['target_planet'])
                if 'aspecting_planets' in pattern:
                    for ap in pattern['aspecting_planets']:
                        all_planets.add(ap['planet'])
                if 'squaring_planets' in pattern:
                    for sp in pattern['squaring_planets']:
                        all_planets.add(sp['planet'])
        
        # Initialiser le compteur de mentions pour chaque planète
        mention_counts = {planet: 0 for planet in all_planets}
        
        # Dictionnaires pour stocker les attributions
        aspect_assignments = {}  # aspect_id -> planet_name
        pattern_assignments = {}  # pattern_id -> [planet_name1, planet_name2]
        
        # Créer une liste de tous les éléments à attribuer avec leurs options
        items_to_assign = []
        
        # Ajouter les aspects (2 options chacun)
        for i, aspect in enumerate(aspects):
            items_to_assign.append({
                'type': 'aspect',
                'id': i,
                'options': [aspect['planet1'], aspect['planet2']],
                'needed': 1,
                'data': aspect
            })
        
        # Ajouter les configurations (choisir 2 parmi 3+)
        for i, pattern in enumerate(patterns):
            planet_options = []
            if 'planets' in pattern:
                planet_options = [p['name'] if isinstance(p, dict) else p 
                                 for p in pattern['planets']]
            elif 'target_planet' in pattern:
                planet_options.append(pattern['target_planet'])
                if 'aspecting_planets' in pattern:
                    planet_options.extend([ap['planet'] for ap in pattern['aspecting_planets']])
                if 'squaring_planets' in pattern:
                    planet_options.extend([sp['planet'] for sp in pattern['squaring_planets']])
            
            if len(planet_options) >= 2:
                items_to_assign.append({
                    'type': 'pattern',
                    'id': i,
                    'options': planet_options,
                    'needed': 2,
                    'data': pattern
                })
        
        # Algorithme greedy: attribuer en fonction de la charge actuelle
        # Trier par nombre d'options (moins d'options = priorité plus haute)
        items_to_assign.sort(key=lambda x: len(x['options']))
        
        for item in items_to_assign:
            # Trier les options par nombre de mentions (ordre croissant)
            sorted_options = sorted(item['options'], 
                                   key=lambda p: mention_counts.get(p, 0))
            
            # Sélectionner les N planètes avec le moins de mentions
            selected = sorted_options[:item['needed']]
            
            # Incrémenter les compteurs
            for planet in selected:
                mention_counts[planet] = mention_counts.get(planet, 0) + 1
            
            # Enregistrer l'attribution
            if item['type'] == 'aspect':
                aspect_assignments[item['id']] = selected[0]
            else:  # pattern
                pattern_assignments[item['id']] = selected
        
        return {
            'aspect_assignments': aspect_assignments,
            'pattern_assignments': pattern_assignments,
            'mention_counts': mention_counts
        }
    
    def get_planet_mentions(self, planet_name, aspects, patterns, assignments):
        """Retourne les aspects et configurations à mentionner pour une planète donnée"""
        
        planet_aspects = []
        planet_patterns = []
        
        # Aspects assignés à cette planète
        for aspect_id, assigned_planet in assignments['aspect_assignments'].items():
            if assigned_planet == planet_name:
                planet_aspects.append(aspects[aspect_id])
        
        # Configurations assignées à cette planète
        for pattern_id, assigned_planets in assignments['pattern_assignments'].items():
            if planet_name in assigned_planets:
                planet_patterns.append(patterns[pattern_id])
        
        return {
            'aspects': planet_aspects,
            'patterns': planet_patterns
        }

    def generate_aspects_patterns(self, date, time, lat, lon, max_orb=8):
        """Génère les aspects et patterns pour un thème donné"""
        chart = self.generate_chart_from_plumatotm_data(date, time, lat, lon)
        aspects = self.calculate_aspects(chart, max_orb)
        patterns = self.detect_patterns(chart, max_orb)
        
        return {
            "aspects": aspects,
            "patterns": patterns
        }

    def save_aspects_patterns(self, data, output_dir="outputs", filename="aspects_patterns.json"):
        """Sauvegarde les aspects et patterns dans un fichier JSON"""
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Aspects et patterns sauvegardes: {filepath}")

def main():
    """Fonction principale pour tester le générateur"""
    generator = AspectsPatternsGenerator()
    
    # Données de Charlene QUINTARD
    date = "1991-07-02"
    time = "08:20"
    lat = 47.3900474
    lon = 0.6889268
    
    print("Generation des aspects et patterns pour Charlene QUINTARD")
    print("=" * 60)
    
    data = generator.generate_aspects_patterns(date, time, lat, lon)
    
    # Afficher les aspects
    print(f"\nASPECTS ({len(data['aspects'])} trouves):")
    print("-" * 40)
    for aspect in data['aspects']:
        print(f"{aspect['planet1']} {aspect['aspect']} {aspect['planet2']} (orb: {aspect['orb']}°)")
    
    # Afficher les patterns
    print(f"\nPATTERNS ({len(data['patterns'])} trouves):")
    print("-" * 40)
    for pattern in data['patterns']:
        print(f"\n{pattern['type']}:")
        if 'planets' in pattern:
            for planet in pattern['planets']:
                if isinstance(planet, dict) and 'name' in planet:
                    print(f"  - {planet['name']} en {planet['position']}")
                else:
                    print(f"  - {planet}")
        if 'aspects' in pattern:
            for aspect in pattern['aspects']:
                print(f"  - {aspect}")
    
    # Sauvegarder
    generator.save_aspects_patterns(data)
    
    print("\nGeneration terminee!")

if __name__ == "__main__":
    main()
