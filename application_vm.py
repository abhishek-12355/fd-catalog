import catalog_repository


def categories():
    return catalog_repository.get_all_categories()


def category_list(category):
    return catalog_repository.get_all_category_items() \
        if category == 'Latest Items' \
        else catalog_repository.get_category_items(category)


def category_add(category_name, session):
    catalog_repository.create_category(category=category_name,
                                       user_id=session['user_id'])


def category_add_item(category, name, description):
    catalog_repository.create_item(category=category, name=name,
                                   description=description)


def category_item(category, item_name):
    return catalog_repository.get_category_item(category, item_name)


def category_delete_item(category, item):
    catalog_repository.delete_item(category, item)


def category_edit_item(category, item, description):
    catalog_repository.update_item(category, item, description)
