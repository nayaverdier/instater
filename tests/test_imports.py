def test_module_import():
    import instater

    assert instater.__all__ == ["InstaterError", "VERSION", "run_tasks"]


def test_direct_import():
    from instater import VERSION  # noqa: F401
    from instater import InstaterError  # noqa: F401
    from instater import run_tasks  # noqa: F401
