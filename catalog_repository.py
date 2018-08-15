from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, CategoriesTable, CategoryItemsTable, UserTable

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)


def execute_query(clazz, **kwargs):
    session = DBSession()
    try:
        response = session.query(clazz).all() \
            if len(kwargs) == 0 \
            else session.query(clazz).filter_by(**kwargs)
        return response
    finally:
        if session is not None:
            session.close()


def execute_query_single(clazz, **kwargs):
    session = DBSession()
    try:
        response = session.query(clazz).one() \
            if len(kwargs) == 0 \
            else session.query(clazz).filter_by(**kwargs).one()
        return response
    finally:
        if session is not None:
            session.close()


def execute_insert(clazz):
    session = DBSession()
    try:
        session.add(clazz)
        session.commit()
    finally:
        if session is not None:
            session.close()


def execute_delete(clazz):
    session = DBSession()
    try:
        session.delete(clazz)
        session.commit()
    finally:
        if session is not None:
            session.close()


def validate_category_user(category, **kwargs):
    return execute_query(CategoriesTable, category_name=category, **kwargs)\
               .count() != 0


def get_all_categories():
    return execute_query(CategoriesTable)


def get_category_items(category):
    return execute_query(CategoryItemsTable, category=category)


def get_all_category_items():
    return execute_query(CategoryItemsTable)


def update_user(user_id):
    if execute_query(UserTable, user_id=user_id).count() == 0:
        execute_insert(UserTable(user_id=user_id))

    return user_id


def create_category(category, user_id):
    if execute_query(UserTable, user_id=user_id).count() == 0:
        raise Exception("Unauthorized")

    execute_insert(CategoriesTable(category_name=category, user_id=user_id))


def create_item(category, name, description):
    execute_insert(CategoryItemsTable(category=category, item_name=name,
                                      description=description))


def get_category_item(category, item_name):
    return execute_query_single(CategoryItemsTable, category=category,
                                item_name=item_name)


def delete_item(category, item):
    item = execute_query_single(CategoryItemsTable,
                                item_name=item,
                                category=category)
    execute_delete(item)


def update_item(category, item, description):
    item = execute_query_single(CategoryItemsTable,
                                item_name=item,
                                category=category)
    item.description = description
    item.category = category
    execute_insert(item)
