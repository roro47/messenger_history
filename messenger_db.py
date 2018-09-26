import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    name = Column(String(250))
    user_uid = Column(Integer, primary_key=True)


class Message(Base):
    __tablename__ = "messages"
    timestamp = Column(Integer, primary_key=True)
    user_uid = Column(Integer, ForeignKey('users.uid'), \
                      primary_key=True)
    message_uid = Column(Integer)
    text = Column(String)
    author_uid = Column(Integer)
    user = relationship("User", back_populates="messages")

class File(Base):
    __tablename__ = "file"
    file_uid = Column(Integer, primary_key=True)
    user_uid = Column(Integer, ForeignKey('users.uid'))
    name = Column(String)
    url = Column(String)
    size = Column(Integer)
    timestamp = Column(Integer)

class Url(Base):
    __tablename__ = "urls"
    url = Column(String, primary_key=True)
    user_uid = Column(Integer, ForeignKey('users.uid'))
    author_uid = Column(Integer, ForeignKey('users.uid'))
    timestamp = Column(Integer)

class Image(Base):
    __tablename__ = "images"

    image_uid = Column(Integer, primary_key=True)
    user_uid = Column(Integer, ForeignKey('users.uid'))
    url = Column(String)
    timestamp = Column(Integer)

class Video(Base):
    __tablename__ = "videos"
    video_uid = Column(Integer, primary_key=True)
    user_uid = Column(Integer, ForeignKey('users.uid'))
    timestamp = Column(Integer)

User.messages = relationship("Message", order_by=Message.timestamp, \
                             back_populates="user")
engine = create_engine("sqlite:///message.db")

Base.metadata.create_all(engine)
