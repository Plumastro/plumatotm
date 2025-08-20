# PLUMATOTM - Astrological Animal Compatibility Engine

PLUMATOTM is a sophisticated astrological analysis engine that computes animal compatibility scores based on birth chart data using planetary positions and zodiac signs.

## 🌟 Features

- **Accurate Astrological Calculations**: Uses `flatlib` for precise planetary positions and zodiac sign calculations
- **Comprehensive Animal Database**: 100+ animals with detailed compatibility scores for each zodiac sign
- **Dynamic Weight System**: Planet weights and multipliers for personalized analysis
- **Multiple Output Formats**: JSON, CSV, and visual radar charts
- **REST API**: Full HTTP API for integration with web applications
- **Timezone Handling**: Automatic local to UTC time conversion based on coordinates

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Required packages (see `requirements.txt`)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/plumatotm.git
cd plumatotm
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the analysis:
```bash
python plumatotm_core.py \
  --scores_json "plumatotm_raw_scores.json" \
  --weights_csv "plumatotm_planets_weights.csv" \
  --multipliers_csv "plumatotm_planets_multiplier.csv" \
  --date 1990-05-15 \
  --time 14:30 \
  --lat 48.8566 \
  --lon 2.3522
```

## 📁 Project Structure

```
plumatotm/
├── plumatotm_core.py          # Main analysis engine
├── plumatotm_api.py           # REST API server
├── plumatotm_radar.py         # Radar chart generator
├── plumatotm_converter.py     # CSV to JSON converter
├── test_plumatotm_api.py      # API testing script
├── test_plumatotm_radar.py    # Radar chart testing
├── requirements.txt           # Python dependencies
├── vercel.json               # Vercel deployment config
├── .gitignore               # Git ignore rules
├── README.md                # This file
├── DEPLOYMENT_GUIDE.md      # Deployment instructions
├── plumatotm_raw_scores.json        # Animal compatibility data
├── plumatotm_planets_weights.csv    # Planet weights
├── plumatotm_planets_multiplier.csv # Planet multipliers
├── plumatotm_raw_scores.csv         # Raw scores (CSV format)
├── plumatotm_radar_reference.png    # Reference radar chart
└── outputs/                  # Generated output files
    ├── birth_chart.json
    ├── planet_weights.json
    ├── raw_scores.json
    ├── weighted_scores.json
    ├── animal_totals.json
    ├── top3_percentage_strength.json
    ├── top3_true_false.json
    ├── top_animal_radar.png
    └── top3_comparison_radar.png
```

## 🔧 Usage

### Command Line Interface

The main analysis can be run from the command line:

```bash
python plumatotm_core.py \
  --scores_json "plumatotm_raw_scores.json" \
  --weights_csv "plumatotm_planets_weights.csv" \
  --multipliers_csv "plumatotm_planets_multiplier.csv" \
  --date YYYY-MM-DD \
  --time HH:MM \
  --lat LATITUDE \
  --lon LONGITUDE
```

### Examples

```bash
# Example 1: Test person
python plumatotm_core.py \
  --scores_json "plumatotm_raw_scores.json" \
  --weights_csv "plumatotm_planets_weights.csv" \
  --multipliers_csv "plumatotm_planets_multiplier.csv" \
  --date 1990-05-15 \
  --time 14:30 \
  --lat 48.8566 \
  --lon 2.3522

# Example 2: Another person
python plumatotm_core.py \
  --scores_json "plumatotm_raw_scores.json" \
  --weights_csv "plumatotm_planets_weights.csv" \
  --multipliers_csv "plumatotm_planets_multiplier.csv" \
  --date 1995-04-13 \
  --time 11:30 \
  --lat 48.8667 \
  --lon 2.2333
```

### Radar Charts

Generate visual radar charts:

```bash
python plumatotm_radar.py
```

## 🌍 Deployment

### Render Deployment

This project is ready for deployment on Render:

1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Set the build command: `pip install -r requirements.txt`
4. Set the start command: `python plumatotm_core.py --help`
5. Deploy!

### For Shopify Integration

Once deployed on Render, Shopify can call your engine by:
- Making HTTP requests to your Render URL
- Passing birth data as parameters
- Receiving JSON responses with animal compatibility results

## 📊 Output Files

The engine generates several output files in the `outputs/` directory:

- **birth_chart.json**: Planetary positions and zodiac signs
- **planet_weights.json**: Dynamic planet weights
- **raw_scores.json**: Raw animal compatibility scores
- **weighted_scores.json**: Weighted scores after planet calculations
- **animal_totals.json**: Total scores for each animal
- **top3_percentage_strength.json**: Top 3 animals with percentage strengths
- **top3_true_false.json**: Top 3 animals with true/false indicators
- **top_animal_radar.png**: Radar chart for the top animal
- **top3_comparison_radar.png**: Comparison radar chart for top 3 animals

## 🔬 Testing

Test the core functionality:

```bash
# Test the main engine
python plumatotm_core.py --help

# Test radar chart generation
python test_plumatotm_radar.py
```

## 📝 Data Format

### Input Data

The engine uses three main data files:

1. **plumatotm_raw_scores.json**: Animal compatibility scores for each zodiac sign
2. **plumatotm_planets_weights.csv**: Base weights for each planet
3. **plumatotm_planets_multiplier.csv**: Multipliers for planet weights based on zodiac signs

### Output Format

The engine generates JSON files with the following structure:

```json
{
  "birth_chart": {...},
  "planet_weights": {...},
  "raw_scores": {...},
  "weighted_scores": {...},
  "animal_totals": {...},
  "top3_percentage_strength": {...},
  "top3_true_false": {...}
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the deployment guide in `DEPLOYMENT_GUIDE.md`
- Review the API documentation at `http://localhost:8000/docs` when running locally

## 🔮 Future Enhancements

- Additional animal species
- More detailed astrological aspects
- Machine learning integration
- Mobile app support
- Multi-language support

---

**PLUMATOTM** - Where Astrology Meets Animal Compatibility 🐾✨
