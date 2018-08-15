from datetime import datetime
from sqlalchemy import Column, DateTime, String, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()


class UserTable(Base):
    __tablename__= 'user_table'
    user_id = Column(String(250), primary_key=True)

    @property
    def serialize(self):
        return {
            'user_id': self.user_id
        }


class CategoriesTable(Base):
    __tablename__ = 'categories_table'
    category_name = Column(String(80), primary_key=True)
    user_id = Column(String(250), ForeignKey('user_table.user_id'))
    user = relationship(UserTable)
    items = relationship("CategoryItemsTable")

    @property
    def serialize(self):
        return {
            'user_id': self.user_id,
            'category_name': self.category_name
        }


class CategoryItemsTable(Base):
    __tablename__ = 'category_items_table'
    category = Column(String(80), ForeignKey('categories_table.category_name'),
                      primary_key=True)
    item_name = Column(String(80), primary_key=True)
    entry_date = Column(DateTime, default=datetime.now())
    description = Column(String(4000))
    category_table = relationship(CategoriesTable)

    @property
    def serialize(self):
        return {
            'item_name': self.item_name,
            'category': self.category
        }


if __name__ == '__main__':
    engine = create_engine('sqlite:///catalog.db')
    Base.metadata.create_all(engine)
