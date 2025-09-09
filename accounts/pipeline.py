# accounts/pipeline.py
from urllib.parse import urlencode
import requests

def save_profile_picture(backend, user, response, *args, **kwargs):
    """Custom pipeline to save profile picture from social auth"""
    if backend.name == 'google-oauth2':
        if 'picture' in response:
            # Download the profile picture
            url = response['picture']
            response = requests.get(url)
            
            if response.status_code == 200:
                # Save the image to the user's profile
                user.profile_picture.save(
                    f'profile_pics/{user.username}.jpg',
                    ContentFile(response.content),
                    save=True
                )
