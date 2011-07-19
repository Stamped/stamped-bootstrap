#!/usr/bin/env python

__author__ = "Stamped (dev@stamped.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2011 Stamped.com"
__license__ = "TODO"

__all__ = [
    "ResourceArgumentSchema", 
    "ResourceArgument", 
    "ResourceArgumentList", 
    "ResourceArgumentBoolean", 
    "Resource", 
    "Template", 
]

import copy, utils
from utils import AttributeDict, OrderedDict
from environment import Environment
from errors import *

# TODO: cleanup the code duplication between ResourceArgument.validate, 
# ResourceArgumentList.validate, and ResourceArgumentBoolean.validate.

class ResourceArgument(object):
    def __init__(self, default=None, required=False, expectedType=None):
        self.required = False
        self.expectedType = expectedType
        
        if hasattr(default, '__call__'):
            self.default = default
        else:
            self.default = self.validate(default)
        
        self.required = required
    
    def validate(self, value):
        if hasattr(value, '__call__'):
            return value
        
        if value is None:
            if self.required:
                raise InvalidArgument("invalid value for arg %s" % str(value))
            else:
                return value
        elif self.expectedType is not None and not isinstance(value, self.expectedType):
            raise InvalidArgument("invalid value for arg %s" % str(value))
        else:
            return value

class ResourceArgumentSchema(OrderedDict, ResourceArgument):
    def __init__(self, items=[], default=None, required=False):
        OrderedDict.__init__(self)
        ResourceArgument.__init__(self, 
                                  default=default, 
                                  required=required, 
                                  expectedType=None)
        
        # hack to make ordering work... would be *much* nicer if python 
        # supported an option for order-preserving **kwargs ala:
        # http://groups.google.com/group/python-ideas/browse_thread/thread/f3663e5b1f4fe7d4
        for d in items:
            self[d[0]] = d[1]
    
    def validate(self, value):
        if value is None:
            if self.required:
                raise InvalidArgument("invalid value for arg %s" % str(value))
            else:
                return value
        
        if not isinstance(value, dict):
            raise InvalidArgument("invalid value for arg %s" % str(value))
        
        output = AttributeDict()
        
        # validate resource arguments
        for arg in value:
            if arg not in self:
                raise InvalidArgument("Unexpected argument %s" % (arg, ))
            elif arg in output:
                raise InvalidArgument("Duplicate argument %s" % (arg, ))
            else:
                try:
                    resourceArg = self[arg]
                    
                    sub_value = value[arg]
                    print "%s) %s" % (type(resourceArg), sub_value)
                    sub_value = resourceArg.validate(sub_value)
                    output[arg] = sub_value
                    #utils.log("added '%s'='%s' to resource '%s'" % (arg, str(sub_value), str(self)))
                except InvalidArgument:
                    utils.log("Error initializing argument '%s'" % (arg, ))
                    utils.printException()
                    raise
        
        for key in self:
            if not key in output:
                if self[key].required:
                    raise Fail("Required argument '%s' not found" % (key, ))
                
                output[key] = self[key].default
        
        return output

class ResourceArgumentList(ResourceArgument):
    def __init__(self, default=None, required=False, expectedType=None, options=None):
        self._options = options
        ResourceArgument.__init__(self, default, required, expectedType)
    
    def validate(self, value):
        if hasattr(value, '__call__'):
            return value
        
        if value is None:
            if self.required:
                raise InvalidArgument("invalid value for arg %s" % str(value))
            else:
                return value
        
        if not isinstance(value, (tuple, list)):
            value = [ value ]
        
        # validate each element in the argument list
        for v in value:
            if hasattr(v, '__call__'):
                continue
            elif (self.expectedType is not None and not isinstance(v, self.expectedType)) or \
                (self._options is not None and not v in self._options):
                raise InvalidArgument("invalid value '%s'" % str(v))
        
        return value

class ResourceArgumentBoolean(ResourceArgument):
    def validate(self, value):
        if hasattr(value, '__call__'):
            return value
        
        value = ResourceArgument.validate(self, value)
        
        if not value in (None, True, False):
            raise InvalidArgument("Expected a boolean but received %r" % value)
        
        return value

class Resource(AttributeDict):
    s_globalSchema = ResourceArgumentSchema([
        ("action",          ResourceArgumentList(default=None)), 
        ("ignoreFailures",  ResourceArgumentBoolean(default=False)), 
        ("notifies",        ResourceArgumentList(default=[])), 
        ("subscribes",      ResourceArgumentList(default=[])), 
        ("not_if",          ResourceArgument(expectedType=basestring)), 
        ("only_if",         ResourceArgument(expectedType=basestring)), 
        ("provider",        ResourceArgument(expectedType=basestring)), 
    ])
    
    def __init__(self, *args, **kwargs):
        AttributeDict.__init__(self)
        
        self.env  = Environment.getInstance()
        self.resourceType = self.__class__.__name__
        self.isUpdated = False
        
        seen = set()
        
        if not hasattr(self, '_schema'):
            raise Fail("Resource failed to define a valid _schema")
        
        if 'content' in self._schema:
            print "%s %s" % (type(self._schema.content), self._schema.content)
        # union global schema with local schema
        #schema = copy.deepcopy(self._schema)
        schema = self._schema
        for key in self.s_globalSchema:
            if not key in schema:
                schema[key] = self.s_globalSchema[key]
        
        resolvedArgs = { }
        keys = schema.keys()
        keysLen = len(keys)
        index = 0
        
        # resolve unnamed arguments with names corresponding to the order 
        # they were passed to Resource's ctor and their relative definitions 
        # in the subclass' ResourceArgumentSchema (which is an OrderedDict, 
        # so as to retain this ordering information).
        for arg in args:
            if index < keysLen:
                key = keys[index]
                resolvedArgs[keys[index]] = arg
            else:
                raise InvalidArgument("Invalid unnamed argument %s provided to resource %s" % (arg, str(self)))
            
            index += 1
        
        for arg in kwargs:
            if arg in resolvedArgs:
                raise InvalidArgument("Invalid mixture of named and unnamed arguments provided to resource %s, possibly around argument %s" % (str(self), arg))
            else:
                resolvedArgs[arg] = kwargs[arg]
        
        utils.log("Initializing resource '%s' with args: %s" % (self.resourceType, resolvedArgs))
        
        # validate resource arguments
        output = schema.validate(resolvedArgs)
        for key in output:
            self[key] = output[key]
        
        self.subscriptions = {
            'immediate' : set(), 
            'delayed' : set()
        }
        
        for sub in self.subscribes:
            if len(sub) == 2:
                action, resource = sub
                immediate = False
            else:
                action, resource, immediate = sub
            
            resource.subscribe(action, self, immediate)
        
        for sub in self.notifies:
            self.subscribe(*sub)
        
        self._validate()
        self._register()
        utils.log("Added new resource '%s'" % (str(self), ))
    
    def updated(self):
        self.isUpdated = True
    
    def subscribe(self, action, resource, immediate=False):
        imm = "immediate" if immediate else "delayed"
        sub = (action, resource)
        self.subscriptions[imm].add(sub)
    
    def _validate(self):
        if not 'name' in self:
            raise Fail("Unable to find name for resource %s" % str(self))
        
        if not 'provider' in self:
            raise Fail("Unable to resolve provider for resource %s" % self.name)
    
    def _register(self):
        resourceType = self.resourceType
        
        # briefly check for conflicting duplicate resources
        for resource in self.env.resources:
            if resource.name == self.name and resource.provider != self.provider:
                if self.provider == None:
                    self.provider = resource.provider
                else:
                    raise Fail("Duplicate resource %r with different providers: %r != %r" % \
                               (resource, self.provider, resource.provider))
        
        # TODO: use self.env.resources[resourceType][name] to support this usage case:
        # notifies = [("restart", env.resources["Service"]["apache2"])])
        self.env.resources.append(self)
    
    def __str__(self):
        return repr(self)
    
    def __repr__(self):
        if 'name' in self:
            return "%s(name=%s)" % (self.resourceType, self.name)
        else:
            return "%s(no name)" % (self.resourceType, )
    
    def __getitem__(self, name):
        item = super(Resource, self).__getitem__(name)
        
        if hasattr(item, '__call__'):
            return item(self)
        else:
            return item

class Template(object):
    
    def __init__(self, path):
        self.path = path
        # TODO

