import aiogram
import pkgutil

def print_modules(package, indent=0):
    prefix = " " * indent
    print(f"{prefix}{package.__name__}")
    for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
        full_name = f"{package.__name__}.{modname}"
        print(f"{prefix}  - {modname} ({'package' if ispkg else 'module'})")
        if ispkg:
            subpackage = __import__(full_name, fromlist=["dummy"])
            print_modules(subpackage, indent + 4)

print_modules(aiogram)
