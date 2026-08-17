from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/words", tags=["words"])

# Temporary API data. This will later be replaced by the TEI/Postgres source.
_WORDS = [
    {
        "word": "accoupler",
        "pronunciation": "akuple",
        "part_of_speech": "verb",
        "gender": None,
        "senses": [
            {"number": 1, "translations": ["join", "unite"]},
            {"number": 2, "translations": ["couple"]},
        ],
        "conjugations": {
            "present": {
                "je": "accouple",
                "tu": "accouples",
                "il/elle": "accouple",
                "nous": "accouplons",
                "vous": "accouplez",
                "ils/elles": "accouplent",
            },
            "past_participle": "accouplé",
        },
    },
    {
        "word": "accueillir",
        "pronunciation": "akœjiʀ",
        "part_of_speech": "verb",
        "gender": None,
        "senses": [{"number": 1, "translations": ["welcome", "receive"]}],
    },
    {
        "word": "accroissement",
        "pronunciation": "akʀwasəmɑ̃",
        "part_of_speech": "noun",
        "gender": "masculine",
        "senses": [
            {"number": 1, "translations": ["accretion", "growth"]},
            {"number": 2, "translations": ["increase"]},
        ],
    },
    {
        "word": "accoutumé",
        "pronunciation": "akutyme",
        "part_of_speech": "adjective",
        "gender": None,
        "senses": [
            {
                "number": 1,
                "translations": ["accustomed", "customary", "used to"],
            }
        ],
    },
]


@router.get("/")
async def list_words(language: str = "French"):
    return {"words": _WORDS}


@router.post("/add_word")
async def add_word(word: str, translation: str, language: str = "French"):
    message = (
        f'Word "{word}" with translation "{translation}" '
        f'added to {language} language.'
    )
    return {"message": message}


@router.get("/{word}")
async def get_word(word: str, language: str = "French"):
    result = next((item for item in _WORDS if item["word"] == word), None)
    if result is None:
        raise HTTPException(status_code=404, detail="Word not found")
    return {"word": result}
