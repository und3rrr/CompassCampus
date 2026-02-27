# CampusCompass Mobile - Setup and Run Guide

## Prerequisites

- Python 3.10+
- pip
- Virtual Environment (recommended)

## Installation

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

## Running the Application

### Desktop (Development)

```bash
python main.py
```

The application will start with a Kivy window simulating Android UI.

### Android (Using Buildozer)

#### Prerequisites
- Java Development Kit (JDK) 11+
- Android SDK
- Buildozer: `pip install buildozer cython`

#### Build APK

```bash
# First time setup (downloads SDK, NDK, etc.)
buildozer android debug

# Output: bin/campuscompass-1.0.0-debug.apk
```

#### Install on Device/Emulator

```bash
buildozer android debug deploy run
```

#### Build Release APK

```bash
buildozer android release
# Sign the APK and upload to Google Play Store
```

## Project Structure

```
mobile_app/
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── buildozer.spec         # Android build configuration
├── .env.example           # Environment configuration template
│
├── screens/               # UI Screens
│   ├── __init__.py
│   ├── home_screen.py     # Building selection screen
│   └── map_screen.py      # Navigation map screen
│
├── widgets/               # Custom Kivy Widgets
│   ├── __init__.py
│   └── map_widget.py      # Map rendering widget
│
├── services/              # Business Logic Services
│   ├── __init__.py
│   ├── api_client.py      # Backend API communication
│   └── cache_service.py   # Local data caching
│
├── tests/                 # Unit Tests
│   ├── __init__.py
│   ├── test_api_client.py
│   ├── test_cache_service.py
│   └── conftest.py        # Pytest fixtures
│
└── assets/                # Application Assets
    └── images/            # Images and icons
```

## Development Workflow

### 1. Start Backend API

```bash
# In another terminal
cd ../
# Start FastAPI backend (see IMPLEMENTATION_GUIDE.md Phase 2)
```

### 2. Configure API URL (if not localhost)

Edit `.env` file or use in-app settings:
- Launch app → Settings (⚙) → Enter API URL

### 3. Run Tests

```bash
pytest tests/ -v
pytest tests/ --cov=services --cov=widgets --cov=screens
```

### 4. Development Tips

- Use `buildozer.spec` to change app settings
- Modify `main.py` for app configuration
- Hot-reload with `kivy.core.window` debugging
- Check logs in `logs/app.log`

## Features

### Current Implementation

- ✅ Building selection screen
- ✅ Interactive map with zoom/pan
- ✅ Node search functionality
- ✅ Route calculation (backend dependent)
- ✅ Multi-floor navigation
- ✅ API communication with caching
- ✅ Settings configuration

### Coming Soon

- [ ] GPS/Location integration
- [ ] Offline mode
- [ ] User favorites/bookmarks
- [ ] Route history
- [ ] Accessibility features
- [ ] Multi-language support
- [ ] Push notifications

## Troubleshooting

### API Connection Issues

```python
# Check API health
from services.api_client import get_api_client
api = get_api_client()
print(api.health_check())  # Should return True
```

### Cache Issues

```python
# Clear cache
from services.cache_service import get_cache_service
cache = get_cache_service()
cache.clear()
```

### Build Issues

```bash
# Clean build
buildozer android clean
buildozer android debug

# View detailed logs
buildozer android debug -- --verbose
```

## Performance Optimization

- Cache building data (default 1 hour)
- Route calculations use optimized Dijkstra
- Map rendering optimized with Kivy Canvas
- API requests use connection pooling

## Security Considerations

- API URL can be configured per environment
- No sensitive data cached locally
- HTTPS support in API client
- Input validation on all user inputs

## API Integration

The app communicates with FastAPI backend at:
- `GET /buildings` - List all buildings
- `GET /buildings/{id}` - Get building details
- `GET /routes/shortest` - Calculate shortest route
- `GET /search` - Search rooms/nodes

See `CODE_EXAMPLES.md` for API integration examples.

## License

CampusCompass Mobile © 2025
