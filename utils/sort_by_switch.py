def sort_by_switch(sort_by):
    sort_orders = {
        "alp_asc": "filename",
        "alp_desc": "-filename",
        "date_asc": "upload_date",
        "DEFAULT": "-upload_date"  # Assuming "DEFAULT" corresponds to the default sorting
    }

    return sort_orders.get(sort_by, "upload_date")