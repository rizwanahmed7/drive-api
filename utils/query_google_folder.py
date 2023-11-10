def create_query_google_folder(query, parent):
    order_by = ""

    if query.get('sortby') == "date_desc":
        order_by = "modifiedTime desc"
    elif query.get('sortby') == "date_asc":
        order_by = "modifiedTime asc"
    elif query.get('sortby') == "alp_desc":
        order_by = "name desc"
    else:
        order_by = "name asc"

    query_builder = f"mimeType = 'application/vnd.google-apps.folder'"

    if query.get('search') and len(query.get('search')) != 0:
        query_builder += f" and name contains '{query.get('search')}'"
    else:
        query_builder += f" and '{parent}' in parents"

    query_builder += " and trashed=false"

    return {'orderBy': order_by, 'queryBuilder': query_builder}
