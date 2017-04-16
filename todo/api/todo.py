#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    api/todo.py
    ~~~~~~~~~~~

    Todo.rip API

    :copyright: (c) 2017 by Mek.
    :license: see LICENSE for more details.
"""

from random import randint
from datetime import datetime, timedelta
from sqlalchemy import Column, Unicode, BigInteger, Integer, \
    Boolean, DateTime, ForeignKey, Table, exists, func
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import MetaData
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.orm.exc import ObjectDeletedError
from sqlalchemy.orm import relationship
from api import db, engine, core


def build_tables():
    """Builds database postgres schema"""
    MetaData().create_all(engine)


class Topic(core.Base):
    __tablename__ = "topics"

    id = Column(BigInteger, primary_key=True)
    name = Column(Unicode, unique=True)

    @classmethod
    def upget(cls, name):
        try:
            topic = Topic.get(name=name)
        except:
            topic = Topic(name=name)
            topic.create()
        return topic


todo_topics = \
    Table('todo_to_topics', core.Base.metadata,
          Column('id', BigInteger, primary_key=True),
          Column('todo_id', BigInteger,
                 ForeignKey('todos.id'), nullable=False),
          Column('topic_id', BigInteger,
                 ForeignKey('topics.id'), nullable=False),
          )

todo_dependencies = \
    Table('dependencies', core.Base.metadata,
          Column('id', BigInteger, primary_key=True),
          Column('todo_parent_id', BigInteger,
                 ForeignKey('todos.id'), nullable=False),
          Column('todo_child_id', BigInteger,
                 ForeignKey('todos.id'), nullable=False),
          )


class TodoEvents(core.Base):
    __tablename__ = "todo_to_events"

    id = Column(BigInteger, primary_key=True)
    todo_id = Column(BigInteger,
                     ForeignKey('todos.id'), nullable=False)
    event_id = Column(BigInteger,
                      ForeignKey('events.id'), nullable=False)
    timestamp = Column(DateTime(timezone=False),
                       default=datetime.utcnow, nullable=False)
    event = relationship('Event')

    def dict(self, verbose=False, minimal=False):
        t = super(TodoEvents, self).dict()
        t['name'] = self.event.name
        t['timestamp'] = self.timestamp.ctime()
        return t

class Todo(core.Base):
    __tablename__ = "todos"

    # use status and modified date to determine when task finished, etc

    id = Column(BigInteger, primary_key=True)
    desc = Column(Unicode, nullable=False, unique=True)
    notes = Column(Unicode, nullable=True)
    archived = Column(Boolean, nullable=False, default=False)
    status = Column(BigInteger, ForeignKey('events.id'), nullable=False)
    events = relationship('TodoEvents')
    topics = relationship('Topic', secondary=todo_topics, backref='topics')
    dependencies = relationship('Todo', secondary=todo_dependencies,
                                primaryjoin=id==todo_dependencies.c.todo_parent_id,
                                secondaryjoin=id==todo_dependencies.c.todo_child_id,
                                backref='parent')
    created = Column(DateTime(timezone=False), default=datetime.utcnow,
                     nullable=False)
    modified = Column(DateTime(timezone=False), default=datetime.utcnow,
                     nullable=False)

    def dict(self, verbose=False, minimal=False):
        t = super(Todo, self).dict()
        t['status'] = Event.get(self.status).dict()
        t['events'] = [e.dict() for e in self.events]
        if self.events:
            t['status']['timestamp'] = self.events[-1].timestamp
            if t['status']['name'] == 'In Progress':
                t['status']['days_active'] = (datetime.utcnow() - t['status']['timestamp']).days
        t['topics'] = [tp.dict() for tp in self.topics]

        if not minimal:
            t['dependencies'] = [d.dict(minimal=minimal) for d in self.dependencies]
        return t


Todo.status_modified = association_proxy('timestamp', 'todo_to_events')

class Event(core.Base):
    __tablename__ = "events"

    # backlog (needs-triage)
    # in-progress
    # complete
    # canceled

    id = Column(BigInteger, primary_key=True)
    name = Column(Unicode, nullable=False, unique=True)

    
for model in core.Base._decl_class_registry:
    m = core.Base._decl_class_registry.get(model)
    try:
        core.models[m.__tablename__] = m
    except:
        pass
