from streamlit.testing.v1 import AppTest


def test_app_boots_without_exception():
    at = AppTest.from_file("app/app.py")
    at.run()
    assert not at.exception


def test_app_renders_toy_case_without_exception():
    at = AppTest.from_file("app/app.py")
    at.run()
    at.selectbox[0].set_value("toy").run()
    assert not at.exception
    assert len(at.markdown) > 0


def test_app_renders_eggs_case_without_exception():
    at = AppTest.from_file("app/app.py")
    at.run()
    at.selectbox[0].set_value("eggs").run()
    assert not at.exception
    assert len(at.markdown) > 0
