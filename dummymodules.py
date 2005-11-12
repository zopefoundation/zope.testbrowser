class DummyInterfaceModule(object):
    Interface = object

    def __getattr__(self, name):
        return lambda *args, **kws: None

interface = DummyInterfaceModule()

class DummySchemaModule(object):
    def __getattr__(self, name):
        return lambda *args, **kws: interface.Attribute('')

schema = DummySchemaModule()


