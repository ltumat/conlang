# conlang
A vocabulary learning app focused on providing context.

## Project Structure

```
conlang/
├── backend/          # Python (FastAPI) backend
│   ├── app/
│   │   ├── main.py        # FastAPI application entry point
│   │   ├── config.py      # App settings via pydantic-settings
│   │   ├── database.py    # SQLAlchemy engine & session
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── routers/       # API route handlers
│   │   └── schemas/       # Pydantic request/response schemas
│   ├── tests/
│   ├── pyproject.toml
│   └── .env.example
├── frontend/         # Flutter mobile app
│   ├── lib/
│   │   ├── main.dart
│   │   ├── app.dart       # MaterialApp configuration
│   │   ├── screens/       # Full-page screen widgets
│   │   ├── widgets/       # Reusable UI components
│   │   ├── models/        # Data classes
│   │   └── services/      # API client & business logic
│   └── pubspec.yaml
└── README.md
```

## Getting Started

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Copy env and adjust as needed
cp .env.example .env

# Run the dev server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Frontend

Requires [Flutter SDK](https://docs.flutter.dev/get-started/install) (>= 3.6).

```bash
cd frontend
flutter pub get
flutter run
```

### Running Tests

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && flutter test
```
