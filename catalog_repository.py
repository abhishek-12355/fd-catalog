from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, CategoriesTable, CategoryItemsTable

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


def get_all_categories():
    return execute_query(CategoriesTable)


def get_category_items(category):
    return execute_query(CategoryItemsTable,
                         category=category)


def get_all_category_items():
    return execute_query(CategoryItemsTable)


def get_category_item(category, item_name):
    return execute_query_single(CategoryItemsTable,
                                category=category,
                                name=item_name)


def add_item(name, description, category):
    execute_insert(CategoryItemsTable(category=category,
                                      name=name,
                                      description=description))


def update_item(name, description, category):
    item = execute_query_single(CategoryItemsTable,
                                name=name,
                                category=category)
    item.description = description
    item.category = category
    execute_insert(item)


def delete_item(name, category):
    item = execute_query_single(CategoryItemsTable,
                                name=name,
                                category=category)
    execute_delete(item)
