# 🚀 Plumastro API Deployment Guide

This guide shows how to deploy your astrological analysis API for Shopify integration.

## ✅ **Confirmed Input Requirements**

Your program already accepts exactly what you need:
- **Date of birth** (YYYY-MM-DD)
- **Local time of birth** (HH:MM 24h format)
- **Latitude** (decimal degrees)
- **Longitude** (decimal degrees)

## 🌐 **API Endpoints**

Once deployed, your API will have these endpoints:

- `GET /` - Health check
- `GET /health` - Detailed health status
- `POST /analyze` - Main analysis endpoint (includes radar charts)
- `POST /generate-radar-charts` - Generate radar charts only
- `GET /animals` - List all available animals
- `GET /planets` - List all supported planets

## 📋 **API Request Format**

```json
POST /analyze
{
  "date": "1994-05-22",
  "time": "11:55",
  "lat": 47.75,
  "lon": 7.3333,
  "name": "Optional Name"
}
```

## 📤 **API Response Format**

```json
{
  "success": true,
  "message": "Analysis completed successfully",
  "data": {
    "birth_data": {
      "date": "1994-05-22",
      "time": "11:55",
      "utc_time": "09:55",
      "lat": 47.75,
      "lon": 7.3333,
      "name": "Optional Name"
    },
    "birth_chart": {
      "Sun": "GEMINI",
      "Ascendant": "LEO",
      "Moon": "LIBRA",
      // ... all planets
    },
    "top_3_animals": [
      {
        "ANIMAL": "Cat",
        "TOTAL_SCORE": 6319.5
      },
      {
        "ANIMAL": "Fox", 
        "TOTAL_SCORE": 6235.5
      },
      {
        "ANIMAL": "Snake",
        "TOTAL_SCORE": 6197.5
      }
    ],
    "all_animals": [...],
    "analysis_summary": {
      "total_animals_analyzed": 81,
      "top_score": 6319.5
    },
    "radar_charts": {
      "top_animal_chart": "outputs/top_animal_radar.png",
      "comparison_chart": "outputs/top3_comparison_radar.png"
    }
  }
}
```

## 🚀 **Deployment Options**

### **Option 1: Vercel (Recommended for Shopify)**

**Pros**: Easy deployment, great for serverless, works well with Shopify
**Cons**: Cold starts, 10-second timeout limit

**Steps:**
1. Install Vercel CLI: `npm i -g vercel`
2. Create `vercel.json`:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api_server.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api_server.py"
    }
  ]
}
```

3. Deploy: `vercel --prod`

### **Option 2: Render**

**Pros**: Free tier, easy deployment, good performance
**Cons**: Free tier has limitations

**Steps:**
1. Create account on [render.com](https://render.com)
2. Connect your GitHub repository
3. Create new Web Service
4. Set build command: `pip install -r requirements_api.txt`
5. Set start command: `uvicorn api_server:app --host 0.0.0.0 --port $PORT`

### **Option 3: Railway**

**Pros**: Easy deployment, good performance, reasonable pricing
**Cons**: Paid service

**Steps:**
1. Create account on [railway.app](https://railway.app)
2. Connect your GitHub repository
3. Deploy automatically

### **Option 4: Fly.io**

**Pros**: Global deployment, good performance, generous free tier
**Cons**: More complex setup

**Steps:**
1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements_api.txt .
RUN pip install -r requirements_api.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

3. Deploy: `fly launch`

## 🔧 **Production Optimizations**

### **1. Environment Variables**
Create `.env` file:
```env
CORS_ORIGINS=https://your-shopify-store.myshopify.com
API_KEY=your-secret-api-key
```

### **2. Security Headers**
Add to `api_server.py`:
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["your-domain.com"])
```

### **3. Rate Limiting**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/analyze")
@limiter.limit("10/minute")
async def analyze_birth_data(request: Request, birth_data: BirthDataRequest):
    # ... existing code
```

## 📊 **Radar Chart Visualization**

Your API now includes **radar chart generation** that creates beautiful visualizations showing the correlation strength between animals and astrological planets.

### **Chart Types:**

1. **Top Animal Radar Chart** - Shows how strongly the top animal correlates with each planet
2. **Comparison Radar Chart** - Compares the top 3 animals across all planets

### **Chart Features:**
- **12-axis radar chart** (one for each planet/point)
- **Percentage strength** displayed on each axis (0-100%)
- **Value labels** showing exact percentages
- **Professional styling** with clear titles and legends
- **High-resolution output** (300 DPI PNG format)

### **Example Output:**
The radar chart shows that **Beaver** (top animal) has:
- **100% correlation** with Sun, Moon, Mars, Jupiter, Saturn, Uranus, Neptune
- **79.8% correlation** with Venus and MC
- **55.4% correlation** with Ascendant and North Node
- **32.1% correlation** with Mercury and Pluto

### **API Integration:**
Radar charts are automatically generated with the `/analyze` endpoint and can also be generated separately with `/generate-radar-charts`.

## 🔗 **Shopify Integration**

### **1. Shopify App Setup**
In your Shopify app, make API calls like this:

```javascript
// Frontend JavaScript
async function analyzeBirthData(birthData) {
  const response = await fetch('https://your-api-domain.com/analyze', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(birthData)
  });
  
  const result = await response.json();
  
  if (result.success) {
    const topAnimal = result.data.top_3_animals[0];
    console.log(`Your spirit animal is: ${topAnimal.ANIMAL}`);
    return result.data;
  } else {
    console.error('Analysis failed:', result.error);
  }
}

// Example usage
const birthData = {
  date: "1994-05-22",
  time: "11:55", 
  lat: 47.75,
  lon: 7.3333,
  name: "Customer Name"
};

analyzeBirthData(birthData);
```

### **2. Shopify Liquid Template**
```liquid
{% comment %} In your Shopify theme {% endcomment %}
<div id="astrological-analysis">
  <form id="birth-data-form">
    <input type="date" id="birth-date" required>
    <input type="time" id="birth-time" required>
    <input type="number" id="latitude" step="0.0001" placeholder="Latitude" required>
    <input type="number" id="longitude" step="0.0001" placeholder="Longitude" required>
    <button type="submit">Find My Spirit Animal</button>
  </form>
  
  <div id="results" style="display: none;">
    <h3>Your Spirit Animal Results</h3>
    <div id="top-animal"></div>
    <div id="all-results"></div>
  </div>
</div>

<script>
document.getElementById('birth-data-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const formData = {
    date: document.getElementById('birth-date').value,
    time: document.getElementById('birth-time').value,
    lat: parseFloat(document.getElementById('latitude').value),
    lon: parseFloat(document.getElementById('longitude').value)
  };
  
  try {
    const result = await analyzeBirthData(formData);
    displayResults(result);
  } catch (error) {
    console.error('Error:', error);
  }
});

function displayResults(data) {
  const topAnimal = data.top_3_animals[0];
  document.getElementById('top-animal').innerHTML = `
    <h4>🏆 Your Primary Spirit Animal: ${topAnimal.ANIMAL}</h4>
    <p>Score: ${topAnimal.TOTAL_SCORE.toFixed(1)}</p>
  `;
  
  document.getElementById('results').style.display = 'block';
}
</script>
```

## 🧪 **Testing Your Deployment**

1. **Local Testing**: `python test_api.py`
2. **Production Testing**: Use the same test script with your deployed URL
3. **Shopify Testing**: Test the integration in your Shopify development store

## 📊 **Monitoring & Analytics**

Consider adding:
- **Logging**: Track API usage and errors
- **Analytics**: Monitor which animals are most popular
- **Performance**: Track response times
- **Error Tracking**: Services like Sentry for error monitoring

## 🔐 **Security Considerations**

1. **API Keys**: Implement authentication for production
2. **CORS**: Restrict origins to your Shopify domain
3. **Rate Limiting**: Prevent abuse
4. **Input Validation**: Already implemented with Pydantic
5. **HTTPS**: Always use HTTPS in production

## 💰 **Cost Estimates**

- **Vercel**: Free tier (10s timeout), $20/month for Pro
- **Render**: Free tier, $7/month for standard
- **Railway**: $5/month minimum
- **Fly.io**: Free tier (3 apps), $1.94/month per app

## 🎯 **Next Steps**

1. Choose your deployment platform
2. Deploy the API
3. Test the endpoints
4. Integrate with your Shopify store
5. Monitor and optimize

Your API is ready for production! 🚀
