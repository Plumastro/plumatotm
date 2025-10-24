#!/usr/bin/env python3
"""
Cache global pour les traductions astrologiques
Évite la répétition des dictionnaires de traduction dans le code
"""

# Cache global pour les traductions
TRANSLATION_CACHE = {
    'aspects': {
        "Conjunction": "Conjonction",
        "Opposition": "Opposition", 
        "Square": "Carré",
        "Trine": "Trigone",
        "Sextile": "Sextile",
        "Semisextile": "Semi-sextile",
        "Semiquintile": "Semi-quintile",
        "Semisquare": "Semi-carré",
        "Quintile": "Quintile",
        "Sesquiquintile": "Sesqui-quintile",
        "Biquintile": "Bi-quintile",
        "Quincunx": "Quincunx"
    },
    
    'planets': {
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
        "South Node": "Nœud Sud",
        "Ascendant": "Ascendant",
        "MC": "MC"
    },
    
    'signs': {
        "ARIES": "Belier",
        "TAURUS": "Taureau", 
        "GEMINI": "Gemeaux",
        "CANCER": "Cancer",
        "LEO": "Lion",
        "VIRGO": "Vierge",
        "LIBRA": "Balance",
        "SCORPIO": "Scorpion",
        "SAGITTARIUS": "Sagittaire",
        "CAPRICORN": "Capricorne",
        "AQUARIUS": "Verseau",
        "PISCES": "Poissons"
    }
}

def get_aspect_translation(aspect_name):
    """Get French translation for aspect name"""
    return TRANSLATION_CACHE['aspects'].get(aspect_name, aspect_name)

def get_planet_translation(planet_name):
    """Get French translation for planet name"""
    return TRANSLATION_CACHE['planets'].get(planet_name, planet_name)

def get_sign_translation(sign_name):
    """Get French translation for sign name (NO ACCENTS to match CSV format)"""
    return TRANSLATION_CACHE['signs'].get(sign_name, sign_name)

def get_all_aspect_translations():
    """Get all aspect translations dictionary"""
    return TRANSLATION_CACHE['aspects'].copy()

def get_all_planet_translations():
    """Get all planet translations dictionary"""
    return TRANSLATION_CACHE['planets'].copy()

def get_all_sign_translations():
    """Get all sign translations dictionary"""
    return TRANSLATION_CACHE['signs'].copy()

# Fonctions de compatibilité pour l'ancien code
def get_aspect_translations():
    """Get aspect translations (legacy function)"""
    return get_all_aspect_translations()

def get_planet_translations():
    """Get planet translations (legacy function)"""
    return get_all_planet_translations()

def get_sign_translations():
    """Get sign translations (legacy function)"""
    return get_all_sign_translations()
