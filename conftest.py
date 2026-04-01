def pytest_pycollect_makeitem(collector, name, obj):
    """Skip base test classes that have no test methods of their own."""
    if isinstance(obj, type) and not any(
        m.startswith("test_") for m in obj.__dict__
    ):
        return None
