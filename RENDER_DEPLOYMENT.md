# Render Deployment Guide

## 🚨 IMPORTANT: Python Version

**This project REQUIRES Python 3.11** - it will NOT work with Python 3.13 due to pyswisseph compatibility issues.

## 📋 Render Configuration

### Build Command
```bash
pip install -r requirements.txt
```

### Start Command
```bash
python start.py
```

**Note:** The `Procfile` is also configured to use Gunicorn for production:
```bash
web: gunicorn main:app -c gunicorn.conf.py
```

### Environment Variables
```
OPENAI_API_KEY=sk-proj-...
SUPABASE_URL=https://...
SUPABASE_ANON_KEY=eyJ...
```

## 🔧 Python Version Control

The following files ensure Python 3.11 is used:
- `runtime.txt` - Contains `python-3.11.9`
- `.python-version` - Contains `3.11.9`
- `requirements.txt` - Comments specify Python 3.11 requirement

## 🐛 Troubleshooting

### Error: `undefined symbol: PyUnicode_AS_DATA`
- **Cause**: Python 3.13 incompatibility with pyswisseph
- **Solution**: Ensure `runtime.txt` is present and contains `python-3.11.9`

### Error: `flatlib is required`
- **Cause**: Import failure during startup
- **Solution**: Check Python version in Render logs, should be 3.11.x

## 📊 Expected Logs

Successful deployment should show:
```
🔍 Testing critical imports...
✅ flatlib: 0.2.3
✅ flask: 3.1.2
✅ pandas: 2.3.1
✅ numpy: 2.3.2
✅ matplotlib: 3.10.5
✅ plumatotm_core imported successfully
✅ main imported successfully
🎉 All imports successful! Starting Flask app...
✅ PLUMATOTM Analyzer initialized successfully
✅ API ready to serve requests
```

## 🌐 API Endpoints

Once deployed, your API will be available at:
- `https://your-app.onrender.com/` - API info
- `https://your-app.onrender.com/health` - Health check
- `https://your-app.onrender.com/analyze` - Main analysis endpoint
