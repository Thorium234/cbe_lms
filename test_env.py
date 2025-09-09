# test_env.py
import os

print("DJANGO_SECRET_KEY:", os.environ.get('DJANGO_SECRET_KEY', 'Not set'))
print("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY:", os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', 'Not set'))
print("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET:", os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', 'Not set'))
print("SOCIAL_AUTH_REDIRECT_IS_HTTPS:", os.environ.get('SOCIAL_AUTH_REDIRECT_IS_HTTPS', 'Not set'))
print("DOMAIN_NAME:", os.environ.get('DOMAIN_NAME', 'Not set'))
