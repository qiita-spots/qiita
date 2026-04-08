import importlib
import pkgutil


def pytest_configure(config):
    success = 0
    failed = 0
    failed_modules = []
    for package_name in ["qiita_db", "qiita_pet", "qiita_core", "qiita_ware"]:
        try:
            package = importlib.import_module(package_name)
            for importer, modname, ispkg in pkgutil.walk_packages(
                package.__path__, prefix=package.__name__ + "."
            ):
                try:
                    importlib.import_module(modname)
                    success += 1
                except Exception as e:
                    failed += 1
                    failed_modules.append(f"{modname}: {e}")
        except Exception as e:
            failed_modules.append(f"{package_name}: {e}")

    print(f"\n=== Module import summary ===")
    print(f"Successfully imported: {success}")
    print(f"Failed to import: {failed}")
    if failed_modules:
        print("Failed modules:")
        for m in failed_modules:
            print(f"  {m}")
    print(f"=== End import summary ===\n", flush=True)


def pytest_pycollect_makeitem(collector, name, obj):
    """Undo inheritance of __test__ = False from base classes.

    Nosetests did not inherit __test__ = False to subclasses,
    but pytest does. This restores the nosetests behavior."""
    import inspect

    if inspect.isclass(obj) and name.startswith("Test"):
        # If __test__ = False is inherited (not defined directly on this class),
        # remove it so pytest collects the class
        if not obj.__dict__.get("__test__", True) is False:
            if getattr(obj, "__test__", True) is False:
                obj.__test__ = True
