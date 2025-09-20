# Birth Chart Generator

A minimalist astrological birth chart generator that creates black and white circular charts showing planetary positions, houses, and aspects.

## Features

- **Minimalist Design**: Black and white only, clean circular layout
- **Accurate Calculations**: Uses flatlib for precise astrological calculations
- **Custom Icons**: Supports PNG icons for planets, signs, and houses
- **Major Aspects**: Shows conjunction, sextile, square, trine, and opposition aspects
- **Multiple House Systems**: Supports Placidus and Porphyry house systems
- **High Resolution**: Generates 1500x1500 PNG images with transparent backgrounds

## Installation

```bash
pip install flatlib timezonefinderL matplotlib pillow
```

## Quick Usage

### Command Line Interface

```bash
# Basic usage
python generate_birth_chart.py --date 1986-11-09 --time 16:28 --lat 46.2044 --lon 6.1432

# With custom icons and output directory
python generate_birth_chart.py --date 1986-11-09 --time 16:28 --lat 46.2044 --lon 6.1432 \
  --icons ./icons --out outputs/

# Using Porphyry house system
python generate_birth_chart.py --date 1986-11-09 --time 16:28 --lat 46.2044 --lon 6.1432 \
  --house-system porphyry
```

### Python API

```python
from birth_chart import generate_birth_chart

# Generate a birth chart
image_path = generate_birth_chart(
    date="1986-11-09",
    time="16:28",
    lat=46.2044,
    lon=6.1432,
    icons_dir="icons",
    house_system="placidus"
)

print(f"Birth chart saved to: {image_path}")
```

### Integration with PLUMATOTM Engine

```python
from birth_chart_integration import integrate_with_plumatotm_engine

# Generate birth chart from engine results
image_path = integrate_with_plumatotm_engine(
    result_json_path="outputs/result.json",
    icons_dir="icons"
)
```

## Input Requirements

- **Date**: YYYY-MM-DD format (e.g., "1986-11-09")
- **Time**: HH:MM 24-hour format (e.g., "16:28")
- **Latitude**: Decimal degrees (-90 to 90)
- **Longitude**: Decimal degrees (-180 to 180)

## Output

- **Format**: PNG image
- **Size**: 1500x1500 pixels
- **Background**: Transparent
- **Colors**: Black only (minimalist design)
- **Filename**: `birth_chart_YYYYMMDD_HHMM_LATLON.png`

## Chart Elements

### Outer Ring: Zodiac Signs
- 12 zodiac signs placed at 30° intervals
- Uses custom PNG icons from `icons/` directory
- Signs: ARIES.png, TAURUS.png, GEMINI.png, etc.

### Inner Ring: House Cusps
- 12 house cusps positioned according to house system
- Uses custom PNG icons: 1.png, 2.png, 3.png, etc.
- House system: Placidus (default) or Porphyry

### Planets and Points
- 10 planets + North Node + Ascendant + MC
- Positioned by ecliptic longitude
- Uses custom PNG icons: sun.png, moon.png, mercury.png, etc.

### Aspects
- Major aspects only: conjunction, sextile, square, trine, opposition
- Shown as thin black lines connecting planets
- Orbs: ±8° for conjunction/opposition, ±6° for others

## Icon Requirements

Place your PNG icons in the `icons/` directory:

### Planet Icons
- `sun.png`, `moon.png`, `mercury.png`, `venus.png`, `mars.png`
- `jupiter.png`, `saturn.png`, `uranus.png`, `neptune.png`, `pluto.png`
- `north_node.png`, `AC.png`, `MC.png`

### Sign Icons
- `ARIES.png`, `TAURUS.png`, `GEMINI.png`, `CANCER.png`
- `LEO.png`, `VIRGO.png`, `LIBRA.png`, `SCORPIO.png`
- `SAGITTARIUS.png`, `CAPRICORN.png`, `AQUARIUS.png`, `PISCES.png`

### House Icons
- `1.png`, `2.png`, `3.png`, `4.png`, `5.png`, `6.png`
- `7.png`, `8.png`, `9.png`, `10.png`, `11.png`, `12.png`

## Technical Details

- **Astrological System**: Tropical zodiac
- **House System**: Placidus (Porphyry for high latitudes >66°)
- **Node Type**: Mean North Node
- **Timezone**: Auto-detected from coordinates
- **Time Conversion**: Local time → UTC automatically

## Testing

```bash
# Run tests
python -m pytest tests/test_birth_chart.py -v

# Run specific test
python -m pytest tests/test_birth_chart.py::TestBirthChartCalculator::test_convert_local_to_utc -v
```

## Examples

### Example 1: Geneva, Switzerland
```bash
python generate_birth_chart.py --date 1986-11-09 --time 16:28 --lat 46.2044 --lon 6.1432
```

### Example 2: New York, USA
```bash
python generate_birth_chart.py --date 1990-05-15 --time 14:30 --lat 40.7128 --lon -74.0060
```

### Example 3: Tokyo, Japan
```bash
python generate_birth_chart.py --date 1985-12-25 --time 08:45 --lat 35.6762 --lon 139.6503
```

## Integration with PLUMATOTM

The birth chart generator can be integrated with the PLUMATOTM engine:

```python
# After running PLUMATOTM analysis
from birth_chart_integration import integrate_with_plumatotm_engine

birth_chart_path = integrate_with_plumatotm_engine("outputs/result.json")
```

This will automatically extract birth data from the engine results and generate a corresponding birth chart.

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   pip install flatlib timezonefinderL matplotlib pillow
   ```

2. **Icon Not Found**
   - Ensure PNG icons are in the `icons/` directory
   - Check filename case sensitivity
   - Use supported icon names (see Icon Requirements)

3. **Invalid Coordinates**
   - Latitude: -90 to 90
   - Longitude: -180 to 180
   - Use decimal degrees format

4. **Timezone Detection Issues**
   - Ensure timezonefinderL is installed
   - Check coordinate accuracy
   - Verify date/time format

### Debug Mode

```bash
python generate_birth_chart.py --date 1986-11-09 --time 16:28 --lat 46.2044 --lon 6.1432 --verbose
```

## License

This module is part of the PLUMATOTM project and follows the same licensing terms.
