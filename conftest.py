import pkgutil
import importlib

def pytest_configure(config):
    """Import all modules to replicate nosetests --with-doctest behavior.
    This ensures module-level code is executed and measured by coverage."""
    for package_name in ['qiita_db', 'qiita_pet', 'qiita_core', 'qiita_ware']:
        try:
            package = importlib.import_module(package_name)
            for importer, modname, ispkg in pkgutil.walk_packages(
                package.__path__, prefix=package.__name__ + '.'
            ):
                try:
                    importlib.import_module(modname)
                except Exception:
                    pass
        except Exception:
            pass
