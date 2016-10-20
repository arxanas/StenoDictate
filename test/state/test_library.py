import py.path
import pytest

from stenodictate.state import Library


@pytest.fixture
def _make_texts(state_path, tmpdir):
    foo_text_file = tmpdir.join("foo")
    foo_text_file.write("foo")
    bar_text_file = tmpdir.join("bar")
    bar_text_file.write("bar")

    library = Library.from_app_state()
    library.add_text(title="Foo", path=str(foo_text_file))
    library.add_text(title="Bar", path=str(bar_text_file))


def test_library_store_text_info(_make_texts, state_path):
    library = Library.from_app_state()
    foo, bar = library.get_texts()
    assert foo.title == "Foo"
    assert bar.title == "Bar"
    assert py.path.local(foo.path).check()
    assert py.path.local(bar.path).check()
    assert foo.path != bar.path


def test_library_read_texts(_make_texts, state_path):
    library = Library.from_app_state()
    foo, bar = library.get_texts()
    assert foo.get_text() == "foo"
    assert bar.get_text() == "bar"
