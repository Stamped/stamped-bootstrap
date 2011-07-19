#!/usr/bin/env python

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2011 Stamped.com"
__license__ = "TODO"

__all__ = [ "Source", "Template", "StaticFile" ]

import environment, os, utils
from errors import *

class Source(object):
    def _get_content(self):
        raise NotImplementedError()

    def _get_checksum(self):
        return None

    def __call__(self):
        return self._get_content()

class StaticFile(Source):
    def __init__(self, name, env=None):
        self.name = name
        self.env  = env or environment.Environment.getInstance()
    
    def _get_content(self):
        try:
            cookbook, name = self.name.split('/', 1)
        except ValueError:
            raise Fail("[StaticFile(%s)] Path must include cookbook name (e.g. 'nginx/nginx.conf')" % self.name)
        
        cb = self.env.cookbooks[cookbook]
        path = os.path.join(cb.path, "files", name)
        with open(path, "rb") as fp:
            return fp.read()

try:
    from jinja2 import Environment, BaseLoader, TemplateNotFound
except ImportError:
    class Template(Source):
        def __init__(self, name, variables=None, env=None):
            raise Exception("Jinja2 required for Template")
else:
    class TemplateLoader(BaseLoader):
        def __init__(self, env=None):
            self.env = env or environment.Environment.getInstance()
        
        def get_source(self, environment, template):
            try:
                cookbook, name = template.split('/', 1)
            except ValueError:
                raise Fail("[Template(%s)] Path must include cookbook name (e.g. 'nginx/nginx.conf.j2')" % template)
            cb = self.env.cookbooks[cookbook]
            path = os.path.join(cb.path, "templates", name)
            if not os.path.exists(path):
                raise TemplateNotFound("%s at %s" % (template, path))
            mtime = os.path.getmtime(path)
            with open(path, "rb") as fp:
                source = fp.read().decode('utf-8')
            return source, path, lambda:mtime == os.path.getmtime(path)
    
    class Template(Source):
        def __init__(self, name, variables=None, env=None):
            self.name = name
            self.env = env or environment.Environment.getInstance()
            self.context = variables.copy() if variables else {}
            self.template_env = Environment(loader=TemplateLoader(self.env), autoescape=False)
            self.template = self.template_env.get_template(self.name)
        
        def _get_content(self):
            self.context.update(
                env = self.env,
                repr = repr,
                str = str,
                bool = bool,
            )
            
            rendered = self.template.render(self.context)
            
            if rendered.endswith('\n'):
                return rendered
            else:
                return rendered + '\n'

