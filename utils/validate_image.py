def image_checker(filename):
    image_ext_list = [
        "jpeg",
        "jpg",
        "png",
        "gif",
        "svg",
        "tiff",
        "bmp"
    ]

    if len(filename) < 1 or '.' not in filename:
        return False

    ext_split = filename.split(".")
    
    if len(ext_split) <= 1:
        return False

    ext = ext_split[-1]
    
    return ext.lower() in image_ext_list
