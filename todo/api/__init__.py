#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    api/__init__.py
    ~~~~~~~~~~~~~~~

    Initialization & DB Connections for the Todo.rip APIs

    :copyright: (c) 2017 by mek.
    :license: see LICENSE for more details.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import graphene
from configs import DB_URI, DEBUG

engine = create_engine(DB_URI, echo=DEBUG, client_encoding='utf8')
db = scoped_session(sessionmaker(bind=engine))

from . import todo

