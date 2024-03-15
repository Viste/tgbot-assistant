class DependencyContainer:
    def __init__(self):
        self.dependencies = {}

    def add(self, name, dependency):
        self.dependencies[name] = dependency

    def get(self, name):
        return self.dependencies.get(name)


container = DependencyContainer()
