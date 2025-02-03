from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import logging

logger = logging.getLogger(__name__)

def upload_to_youtube(
    video_file: str,
    title: str,
    description: str,
    credentials_path: str
) -> str:
    """
    Upload video to YouTube using the YouTube Data API
    """
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    
    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    credentials = flow.run_local_server(port=0)

    youtube = build('youtube', 'v3', credentials=credentials)

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': ['Music Mix', 'Playlist', 'Music'],
            'categoryId': '10'  # Music category
        },
        'status': {
            'privacyStatus': 'private',  # or 'public', 'unlisted'
            'selfDeclaredMadeForKids': False
        }
    }

    try:
        insert_request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=MediaFileUpload(
                video_file,
                chunksize=-1,
                resumable=True
            )
        )

        response = insert_request.execute()
        video_id = response['id']
        logger.info(f"Video uploaded successfully! Video ID: {video_id}")
        return f"https://youtube.com/watch?v={video_id}"
    except Exception as e:
        logger.error(f"Error uploading to YouTube: {str(e)}")
        raise 