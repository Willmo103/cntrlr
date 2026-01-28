from pathlib import Path
from core.models import file_system as fs
import pytest


@pytest.fixture(scope="module")
def temp_dir_path(tmp_path_factory) -> fs.BaseDirectory:
    """Create a temporary directory for file system tests."""
    dir_path = tmp_path_factory.mktemp("test_dir")
    return fs.BaseDirectory.populate(Path(dir_path))


@pytest.fixture(scope="module")
def test_markdown_file_path(tmp_path_factory) -> fs.BaseTextFile:
    """Create a temporary markdown file for testing."""
    md_path = tmp_path_factory.mktemp("test_markdown") / "test_file.md"
    md_path.write_text("""
# Test Markdown File

This is a sample markdown file for testing purposes.

**Ipsums Delor:**

- Item 1
- Item 2
- Item 3

```python
def hello_world():
    print("Hello, World!")
```
    """)
    return fs.BaseTextFile.populate(Path(md_path))


@pytest.fixture(scope="module")
def test_image_file_path(tmp_path_factory) -> fs.ImageFile:
    """Create a temporary image file for testing."""
    image_path = tmp_path_factory.mktemp("test_images") / "test_image.png"
    image_path.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
        b"\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01"
        b"\x0d\n\x2d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return fs.ImageFile.populate(Path(image_path))


@pytest.fixture(scope="module")
def test_video_file_path() -> fs.VideoFile:
    """Create a temporary video file for testing."""
    video_path = "C:/src/cntrlr/lib/core/.private/test_video.mp4"
    return fs.VideoFile.populate(Path(video_path))


@pytest.fixture(scope="module")
def test_data_file_path(tmp_path_factory) -> fs.DataFile:
    """Create a temporary data file for testing."""
    data_path = tmp_path_factory.mktemp("test_data") / "test_data.csv"
    data_path.write_text("id,name,age\n" "1,Alice,30\n" "2,Bob,25\n" "3,Charlie,35\n")
    return fs.DataFile.populate(Path(data_path))


@pytest.fixture(scope="module")
def test_sqlite_file_path(tmp_path_factory) -> fs.SQLiteFile:
    """Create a temporary SQLite file for testing."""
    sqlite_path = tmp_path_factory.mktemp("test_sqlite") / "test_db.sqlite"
    import sqlite3

    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER NOT NULL
        )
        """)
    cursor.executemany(
        "INSERT INTO users (name, age) VALUES (?, ?)",
        [("Alice", 30), ("Bob", 25), ("Charlie", 35)],
    )
    conn.commit()
    conn.close()
    return fs.SQLiteFile.populate(Path(sqlite_path))


@pytest.fixture(scope="module")
def test_generic_file_path(tmp_path_factory) -> fs.GenericFile:
    """Create a temporary generic file for testing."""
    generic_path = tmp_path_factory.mktemp("test_generic") / "test_file.bin"
    generic_path.write_bytes(b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09")
    return fs.GenericFile.populate(Path(generic_path))


def test_file_system_setup(
    temp_dir_path,
    test_markdown_file_path,
    test_image_file_path,
    test_video_file_path,
    test_data_file_path,
    test_sqlite_file_path,
    test_generic_file_path,
):
    """Test that the file system fixtures are set up correctly."""
    tmp_dir = temp_dir_path.Path
    assert tmp_dir.exists()
    assert test_markdown_file_path.Path.exists()
    assert test_image_file_path.Path.exists()
    assert test_video_file_path.Path.exists()
    assert test_data_file_path.Path.exists()
    assert test_sqlite_file_path.Path.exists()
    assert test_generic_file_path.Path.exists()


def test_file_types(
    test_markdown_file_path,
    test_image_file_path,
    test_video_file_path,
    test_data_file_path,
    test_sqlite_file_path,
    test_generic_file_path,
):
    """Test that the file types are correctly identified."""
    assert isinstance(test_markdown_file_path, fs.BaseTextFile)
    assert isinstance(test_image_file_path, fs.ImageFile)
    assert isinstance(test_video_file_path, fs.VideoFile)
    assert isinstance(test_data_file_path, fs.DataFile)
    assert isinstance(test_sqlite_file_path, fs.SQLiteFile)
    assert isinstance(test_generic_file_path, fs.GenericFile)


def test_sqlite_file_contents(test_sqlite_file_path):
    """Test that the SQLite file contents are correctly read."""
    sqlite_file = test_sqlite_file_path
    assert sqlite_file.db_schema is not None
    assert "users" in sqlite_file.tables
