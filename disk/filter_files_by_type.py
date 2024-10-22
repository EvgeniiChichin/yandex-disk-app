def filter_files_by_type(files_data, media_type):
    """Фильтрует файлы по типу медиа."""
    filtered_files = []
    for file in files_data:
        mime_type = file.get('mime_type', '')
        if media_type == 'all':
            filtered_files.append(file)
        elif media_type == 'document' and mime_type.startswith('application/'):
            filtered_files.append(file)
        elif media_type == 'image' and mime_type.startswith('image/'):
            filtered_files.append(file)
        elif media_type == 'video' and mime_type.startswith('video/'):
            filtered_files.append(file)
        elif media_type == 'audio' and mime_type.startswith('audio/'):
            filtered_files.append(file)
        elif media_type == 'archive' and (mime_type.startswith('application/zip') or
                                          mime_type.startswith('application/x-rar-compressed')):
            filtered_files.append(file)
    return filtered_files
