
# Define the max age for cookies (in seconds)
max_age_access = 60 * 60 * 20  # 20 minutes
max_age_refresh = 60 * 60 * 24 * 30  # 30 days
max_age_stream_video = 60 * 60 * 24  # 24 hours

# Function to create a login cookie
def create_login_cookie(response, access_token, refresh_token):
    response.set_cookie("access-token", access_token, samesite='Lax')
    response.set_cookie("refresh-token", refresh_token, samesite='Lax')
    return response 

# Function to create a logout cookie
def create_logout_cookie(response):
    response.set_cookie("access-token", '', max_age=0, secure=True, samesite='Lax')
    response.set_cookie("refresh-token", '', max_age=0, secure=True, samesite='Lax')
    return response
# Function to create a stream video cookie
def create_stream_video_cookie(response, stream_video_access_token):
    response.set_cookie("video-access-token", stream_video_access_token, max_age=max_age_stream_video, secure=True, samesite='Lax')
    return response
# Function to remove the stream video cookie
def remove_stream_video_cookie(response):
    response.set_cookie("video-access-token", '', max_age=0, secure=True, samesite='Lax')
    return response 