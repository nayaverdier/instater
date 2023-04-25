def test_module_import():
    import instater

    assert instater.__all__ == ["InstaterError", "__version__", "run_tasks"]


def test_direct_import():
    from instater import InstaterError  # noqa: F401
    from instater import __version__  # noqa: F401
    from instater import run_tasks  # noqa: F401
