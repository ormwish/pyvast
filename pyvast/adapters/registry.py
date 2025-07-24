REGISTRY = {}

def register_adapter(name, cls):
    REGISTRY[name] = cls

def get_adapter(name):
    return REGISTRY[name]
