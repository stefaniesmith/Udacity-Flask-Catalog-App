import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(30), nullable=False, unique=True)

    @property
    def serialize(self):
        return {
            'name': self.name,
            'id': self.id,
        }


class Book(Base):
    __tablename__ = 'book'

    title = Column(String(100), nullable=False)
    id = Column(Integer, primary_key=True)
    author = Column(String(50))
    description = Column(String(1000))
    category_id = Column(Integer, ForeignKey('category.id'), nullable=False)
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'title': self.title,
            'author': self.author,
            'description': self.description,
            'category': self.category.name,
            'id': self.id,
        }


engine = create_engine('sqlite:///catalog.db')
Base.metadata.create_all(engine)
