from django.core.exceptions import ValidationError

def validate_video_extension(value):
    video_ext_list = [
        "3g2",
        "3gp",
        "aaf",
        "asf",
        "avchd",
        "avi",
        "drc",
        "flv",
        "m2v",
        "m4p",
        "m4v",
        "mkv",
        "mng",
        "mov",
        "mp2",
        "mp4",
        "mpe",
        "mpeg",
        "mpg",
        "mpv",
        "mxf",
        "nsv",
        "ogg",
        "ogv",
        "qt",
        "rm",
        "rmvb",
        "roq",
        "svi",
        "vob",
        "webm",
        "wmv",
        "yuv"
    ]

    if not value.name.endswith(tuple(video_ext_list)):
        return False
