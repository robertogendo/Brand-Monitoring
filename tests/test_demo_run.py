def test_demo_run_executes_without_errors():
    """
    Run the demo runner (which injects demo seeds and clears state).
    External services are stubbed via tests/conftest.py so this should run quickly.
    """
    import demo.demo_run as demo
    # run_demo prints and returns None; it should not raise
    demo.run_demo()