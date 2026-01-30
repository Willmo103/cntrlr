from hashlib import sha256
from pathlib import Path

import pytest

from core.models import file_system as fs


TEST_DATA_FOLDER = Path(__file__).parent / "test_data"
TEST_MP3_FILE = TEST_DATA_FOLDER / "file_example_MP3_700KB.mp3"
TEST_MP4_FILE = TEST_DATA_FOLDER / "file_example_MP4_480_1_5MG.mp4"
TEST_SQLITE_FILE = TEST_DATA_FOLDER / "file_example_SQLITE.db"
TEST_PNG_FILE = TEST_DATA_FOLDER / "file_example_PNG_500kB.png"
TEST_MARKDOWN_FILE = TEST_DATA_FOLDER / "file_example_MARKDOWN.md"
TEST_CSV_FILE = TEST_DATA_FOLDER / "file_example_CSV.csv"
TEST_GENERIC_FILE = TEST_DATA_FOLDER / "file_example_GENERIC.bin"


@pytest.fixture(scope="module")
def test_dir_path() -> fs.BaseDirectory:
    """Create a temporary directory for testing."""
    folder = TEST_DATA_FOLDER
    return fs.BaseDirectory.populate(Path(folder))


@pytest.fixture(scope="module")
def test_markdown_file_path() -> fs.BaseTextFile:
    """Create a temporary markdown file for testing."""
    md_path = TEST_MARKDOWN_FILE
    return fs.BaseTextFile.populate(Path(md_path))


@pytest.fixture(scope="module")
def test_image_file_path() -> fs.ImageFile:
    """Create a temporary image file for testing."""
    image_path = TEST_PNG_FILE
    return fs.ImageFile.populate(Path(image_path))


@pytest.fixture(scope="module")
def test_video_file_path() -> fs.VideoFile:
    """Create a temporary video file for testing."""
    video_path = TEST_MP4_FILE
    return fs.VideoFile.populate(Path(video_path))


@pytest.fixture(scope="module")
def test_data_file_path() -> fs.DataFile:
    """Create a temporary data file for testing."""
    data_path = TEST_CSV_FILE
    return fs.DataFile.populate(Path(data_path))


@pytest.fixture(scope="module")
def test_sqlite_file_path() -> fs.SQLiteFile:
    """Create a temporary SQLite file for testing."""
    sqlite_path = TEST_SQLITE_FILE
    return fs.SQLiteFile.populate(Path(sqlite_path))


@pytest.fixture(scope="module")
def test_generic_file_path() -> fs.GenericFile:
    """Create a temporary generic file for testing."""
    generic_path = TEST_GENERIC_FILE
    return fs.GenericFile.populate(Path(generic_path))


@pytest.fixture(scope="module")
def test_base_text_file_path() -> fs.BaseTextFile:
    """Create a temporary base text file for testing."""
    md_path = TEST_MARKDOWN_FILE
    return fs.BaseTextFile.populate(Path(md_path))


def test_file_system_setup(
    test_dir_path,
    test_markdown_file_path,
    test_image_file_path,
    test_video_file_path,
    test_data_file_path,
    test_sqlite_file_path,
    test_generic_file_path,
):
    """Test that the file system fixtures are set up correctly."""
    tmp_dir = test_dir_path.Path
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
    # check basemodel attributes
    assert sqlite_file.path_json is not None and isinstance(
        sqlite_file.path_json, fs.FilePath
    )
    assert sqlite_file.stat_json is not None and isinstance(
        sqlite_file.stat_json, fs.BaseFileStat
    )
    assert sqlite_file.sha256 is not None and isinstance(sqlite_file.sha256, str)
    assert sqlite_file.mime_type == "application/vnd.sqlite3"
    # check metadata attributes
    assert sqlite_file.short_description is None
    assert sqlite_file.long_description is None
    assert sqlite_file.tags == []
    # check sqlite-specific attributes
    assert sqlite_file.db_schema is not None
    assert "users" in sqlite_file.tables


def test_markdown_file_contents(test_markdown_file_path):
    """Test that the Markdown file contents are correctly read."""
    md_file = test_markdown_file_path
    assert md_file.path_json is not None
    assert md_file.stat_json is not None
    assert md_file.sha256 is not None
    assert md_file.mime_type == "text/markdown"
    # check metadata attributes
    assert md_file.short_description is None
    assert md_file.long_description is None
    assert md_file.tags == []
    # check sqlite-specific attributes
    content = md_file.content
    assert "# Test Markdown File" in content
    assert "def hello_world():" in content
    # test lines_json
    assert isinstance(md_file.lines_json, list)
    line = md_file.lines_json[0]
    assert isinstance(line, fs.TextFileLine)
    assert line.line_number == 1
    assert line.id is not None
    assert line.content.startswith("# Test Markdown File")
    assert line.content_hash == sha256(line.content.encode("utf-8")).hexdigest()


def test_image_file_contents(test_image_file_path):
    """Test that the image file contents are correctly read."""
    img_file = test_image_file_path
    assert img_file.path_json is not None
    assert img_file.stat_json is not None
    assert img_file.sha256 is not None
    assert img_file.mime_type == "image/png"
    # check metadata attributes
    assert img_file.short_description is None
    assert img_file.long_description is None
    assert img_file.tags == []
    # check image-specific attributes
    assert img_file.exif_data is not None
    assert img_file.thumbnail_b64_data is not None
    assert img_file.html_img_tag.startswith("<img ")
    assert img_file.md_img_tag.startswith("![")
    assert img_file.html_thumbnail_tag.startswith("<img ")
    assert img_file.md_thumbnail_tag.startswith("![")
    assert img_file.b64_data is not None
    assert img_file.thumbnail_b64_data is not None


def test_video_file_contents(test_video_file_path):
    """Test that the video file contents are correctly read."""
    vid_file = test_video_file_path
    assert vid_file.path_json is not None
    assert vid_file.stat_json is not None
    assert vid_file.sha256 is not None
    assert vid_file.mime_type == "video/mp4"
    # check metadata attributes
    assert vid_file.short_description is None
    assert vid_file.long_description is None
    assert vid_file.tags == []
    # check sqlite-specific attributes
    content = vid_file
    assert content.height > 0
    assert content.width > 0
    assert content.duration > 0


def test_data_file_contents(test_data_file_path):
    """Test that the data file contents are correctly read."""
    data_file = test_data_file_path
    assert data_file.path_json is not None
    assert data_file.stat_json is not None
    assert data_file.sha256 is not None
    assert data_file.mime_type == "application/vnd.ms-excel"
    # check metadata attributes
    assert data_file.short_description is None
    assert data_file.long_description is None
    assert data_file.tags == []
    # check sqlite-specific attributes
    content = data_file.content
    assert "id,name,age" in content
    assert "Alice" in content
    assert "Bob" in content


def test_generic_file_contents(test_generic_file_path):
    """Test that the generic file contents are correctly read."""
    generic_file = test_generic_file_path
    assert generic_file.path_json is not None
    assert generic_file.stat_json is not None
    assert generic_file.sha256 is not None
    assert generic_file.mime_type == "application/octet-stream"
    # check metadata attributes
    assert generic_file.short_description is None
    assert generic_file.long_description is None
    assert generic_file.tags == []
    # check sqlite-specific attributes
    assert generic_file.stat_json is not None
    assert generic_file.path_json is not None


def test_base_text_file_contents(test_base_text_file_path):
    """Test that the base text file contents are correctly read."""
    text_file = test_base_text_file_path
    assert text_file.path_json is not None
    assert text_file.stat_json is not None
    assert text_file.sha256 is not None
    assert text_file.mime_type == "text/markdown"
    # check metadata attributes
    assert text_file.short_description is None
    assert text_file.long_description is None
    assert text_file.tags == []
    # check text-specific attributes
    lines_json = text_file.lines_json
    assert len(lines_json) > 0
    assert lines_json[0].line_number == 1
    assert lines_json[0].content.startswith("# Test Markdown File")
    content = text_file.content
    assert "# Test Markdown File" in content
    assert "def hello_world():" in content
