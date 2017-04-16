#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    endpoints.py
    ~~~~~~~~~~~~

    :copyright: (c) 2017 by Mek.
    :license: see LICENSE for more details.
"""

from flask import request
from flask.views import MethodView
from datetime import datetime
from api import todo
from views import paginate, rest, search

class Router(MethodView):

    @rest
    def get(self, cls, _id=None):
        if request.args.get('action') == 'search':
            return {cls: [r.dict() for r in search(todo.core.models[cls])]}
        if _id:
            return todo.core.models[cls].get(_id).dict()
        return {cls: [v.dict() for v in todo.core.models[cls].all()]}

    @rest
    def post(self, cls, _id=None):
        return getattr(self, cls)(cls, _id=_id)

    def todos(self, cls, _id):
        desc = request.form.get('desc', '')
        tokens = desc.split()

        if not desc:
            return {'error': 'desc is required'}

        if desc.startswith('/'):
            directive = tokens[0][1:].lower()
            tid = int(tokens[1].replace('#', ''))

            states = {
                'start': 'In Progress',
                'rip': 'Complete',
                'cancel': 'Canceled',
                'punt': 'Backlog'
                }

            t = todo.Todo.get(tid)
            t.modified = datetime.utcnow()

            if directive in states:
                e = todo.Event.get(name=states[directive])
                te = todo.TodoEvents(todo_id=t.id, event_id=e.id)
                te.create()
                t.events.append(te)
                t.status = e.id
                t.save()
                return {
                    'success': 'status',
                    'todo': t.dict()
                    }

            elif directive == 'rm':
                return {
                    'error': 'rm',
                    'msg': 'deletion not yet implemented',
                    }
                
            elif directive == 'note':
                t.notes = desc.split(" ", 2)[-1]
                t.save()
                return {
                    'success': 'note',
                    'todo': t.dict()
                    }

            elif directive == 'edit':
                t.desc = desc.split(" ", 2)[-1]
                t.save()
                return {
                    'success': 'edit',
                    'todo': t.dict()
                    }

            elif directive == 'todo':
                return {
                    'error': 'todo',
                    'msg': 'nested dependencies not yet implemented',
                    }

            elif directive == 'requires':
                return {
                    'error': 'requires',
                    'msg': 'requires not yet implemented',
                    }

            elif directive == 'tag':
                topics = [token.strip()[1:] for token in tokens if token.startswith('@')]
                for name in topics:
                    topic = todo.Topic.upget(name=name)
                    t.topics.append(topic)
                t.save()
                return {
                    'success': 'tag',
                    'todo': t.dict()
                    }
            return {'error': 'invalid directive'}

        topics, dependencies = [], []
        for token in tokens:
            prefix, word = token[0], token[1:]
            if prefix == '#':
                dependencies.append(word)
            elif prefix == '@':
                topics.append(word)

        status = todo.Event.get(name="Backlog")
        t = todo.Todo(desc=desc, status=status.id)
        t.create()
        initial_event = todo.TodoEvents(todo_id=t.id, event_id=status.id)
        initial_event.create()
        t.events.append(initial_event)
        for name in topics:
            topic = todo.Topic.upget(name=name)
            t.topics.append(topic)
        t.save()

        return {
            'success': 'created',
            'todo': t.dict()
            }


class Index(MethodView):
    @rest
    def get(self):
        # TODO: Query.execute ...
        return {"endpoints": todo.core.models.keys()}


urls = (
    '/<cls>/<_id>', Router,
    '/<cls>', Router,    
    '/', Index # will become graphql endpoint
)
