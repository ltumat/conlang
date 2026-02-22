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