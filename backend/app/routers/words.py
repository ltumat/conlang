from fastapi import APIRouter

router = APIRouter(prefix="/words", tags=["words"])

@router.get("/")
async def list_words(language: str = 'French'):

    return {
        'words': [
            {
                'word': 'Bonjour',
                'translation': 'Hello',
            },
            {
                'word': 'Merci',
                'translation': 'Thank you',
            },
            {
                'word': 'Au revoir',
                'translation': 'Goodbye',
            },
        ]
    }

@router.post("/add_word")
async def add_word(word: str, translation: str, language: str = 'French'):

    return {
        'message': f'Word "{word}" with translation "{translation}" added to {language} language.'
    }