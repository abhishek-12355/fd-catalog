from datetime import datetime
from sqlalchemy import Column, DateTime, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class CategoriesTable(Base):
    __tablename__ = 'categories_table'
    name = Column(String(80), nullable=False, primary_key=True)


class CategoryItemsTable(Base):
    __tablename__ = 'category_items_table'
    category = Column(String(80), ForeignKey('categories_table.name'),
                      nullable=False,
                      primary_key=True)
    name = Column(String(80), nullable=False,   primary_key=True)
    entry_date = Column(DateTime, default=datetime.now())
    description = Column(String(4000))


if __name__ == '__main__':
    engine = create_engine('sqlite:///catalog.db')
    Base.metadata.create_all(engine)

    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    initialCategoryList = [
        CategoriesTable(name='Soccer'),
        CategoriesTable(name='Basketball'),
        CategoriesTable(name='Baseball'),
        CategoriesTable(name='Frisbee'),
        CategoriesTable(name='Snowboarding'),
        CategoriesTable(name='Rock Climbing'),
        CategoriesTable(name='Foosball'),
        CategoriesTable(name='Skating'),
        CategoriesTable(name='Hockey')
    ]

    initialCategoryItems = [
        CategoryItemsTable(name='Stick',
                           category='Hockey',
                           description='Stick description'),
        CategoryItemsTable(name='Goggles',
                           category='Snowboarding',
                           description='Goggles description'),
        CategoryItemsTable(name='Snowboard',
                           category='Snowboarding',
                           description='Snowboard description'),
        CategoryItemsTable(name='Two shinguards',
                           category='Soccer',
                           description='Two shinguards description'),
        CategoryItemsTable(name='Shinguards',
                           category='Soccer',
                           description='Shinguards description'),
        CategoryItemsTable(name='Frisbee',
                           category='Frisbee',
                           description='Frisbee description'),
        CategoryItemsTable(name='Bat',
                           category='Baseball',
                           description='Bat description'),
        CategoryItemsTable(name='Jersey',
                           category='Soccer',
                           description='Jersey description'),
        CategoryItemsTable(name='Soccer Cleats',
                           category='Soccer',
                           description='Soccer Cleats description'),
    ]

    session.add_all(initialCategoryList)
    session.add_all(initialCategoryItems)
    session.commit()
