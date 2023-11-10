def sort_by_switch_folder(sort_by):
    sort_orders = {
        "alp_asc": "name",
        "alp_desc": "-name",
        "date_asc": "created_at",
        "DEFAULT": "-created_at" }

    return sort_orders.get(sort_by, "-created_at")
