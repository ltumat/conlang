from fastapi import APIRouter

router = APIRouter(prefix="/languages", tags=["languages"])

@router.get("/")
async def list_languages():

    return {
        'languages': [{
            'name': 'English',
            'word_count': 1000,
            'video_count': 100,
            }, 
            {'name': 'Spanish', 
             'word_count': 800, 
             'video_count': 80}, 
            {'name': 'French', 
             'word_count': 900, 
             'video_count': 90}]
    }
