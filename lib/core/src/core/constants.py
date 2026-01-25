# region Docstring
"""
core.constants
Shared constants and enumerations for file system scanning and processing operations.
Overview:
- Provides filtering lists for file system scanning operations to exclude common
    non-essential directories and file types.
- Defines mappings from file extensions to markdown syntax highlighters for code
    documentation and display purposes.
- Provides enumerations for commonly supported media and data file formats.
Contents:
- Filtering Lists:
    - IGNORE_PARTS: List of directory/file name patterns to skip during recursive scans.
        Includes version control directories, build artifacts, virtual environments,
        IDE configurations, cache directories, and system folders.
    - IGNORE_EXTENSIONS: List of file extensions to exclude from processing. Includes
        compiled binaries, temporary files, databases, archives, and system files.
- Extension Mappings:
    - MD_XREF: Dictionary mapping file extensions and filenames to their corresponding
        markdown/syntax highlighter language identifiers. Used for code block rendering
        in documentation and display contexts.
- Format Enumerations:
    - ImageFormats: Enum of supported image file formats (.png, .jpeg, .jpg, .bmp, .svg,
        .gif, .webp, .tiff, .heic, .nef).
    - DataFormats: Enum of supported data file formats (.csv, .json, .xml, .yaml, .xlsx,
        .parquet, .avro, .orc).
    - VideoFormats: Enum of supported video file formats (.mp4, .avi, .mkv, .mov, .wmv,
        .flv, .webm, .mpg, .m4v).
- Derived Lists:
    - IMAGE_FORMAT_LIST: List of image format extension strings derived from ImageFormats.
    - DATA_FORMAT_LIST: List of data format extension strings derived from DataFormats.
    - VIDEO_FORMAT_LIST: List of video format extension strings derived from VideoFormats.
    - MARKDOWN_EXTENSIONS: List of all file extensions with markdown syntax highlighting support.
Design Notes:
- IGNORE_PARTS and IGNORE_EXTENSIONS are designed to be comprehensive defaults for
    scanning operations, reducing noise from build artifacts and system files.
- The MD_XREF mapping supports a wide variety of programming languages and configuration
    file types for accurate syntax highlighting in rendered markdown.
- Format enums inherit from both str and enum.Enum, allowing direct string comparison
    while maintaining type safety and IDE autocompletion support.
"""
# endregion
# region Imports
# Patterns for file parts to ignore (matched anywhere in path)
import enum
from typing import List

# endregion
# region Constants -- IGNORE_PARTS
IGNORE_PARTS: List[str] = [
    ".hg",
    ".svn",
    "node_modules",
    "__pycache__",
    ".idea",
    ".tox",
    ".pytest_cache",
    ".mypy_cache",
    ".ipynb_checkpoints",
    ".eggs",
    "logs",
    "tmp",
    "temp",
    "cache",
    "bin",
    "obj",
    "out",
    "AppData",
    "Local",
    "Roaming",
    ".anaconda",
    ".devcontainer",
    ".aider",
    ".aitk",
    ".android",
    ".gradle",
    ".astropy",
    ".aws",
    ".azure",
    ".cache",
    ".cargo",
    ".chocolatey",
    ".codium",
    ".continuum",
    ".cursor",
    ".dbclient",
    ".ddl_mappings",
    ".dev",
    ".docker",
    ".dotnet",
    ".embedchain",
    ".gnupg",
    ".ipython",
    ".jdks",
    ".kivy",
    ".llama",
    ".local",
    ".m2",
    ".matplotlib",
    ".nuget",
    ".ollama",
    ".pki",
    ".pyenv",
    ".pylint.d",
    ".pypoetry",
    ".python-eggs",
    ".shiv",
    ".slack",
    ".ssh",
    ".streamlit",
    ".swarm_ui",
    ".spyder-py3",
    ".templateengine",
    ".testEmbedding",
    ".torrent_bak",
    ".u2net",
    ".ubuntu",
    ".vagrant",
    ".virtualenvs",
    ".vsts",
    ".wallaby",
    ".winget_portable_root",
    ".winget",
    ".zenmap",
    ".zsh_history",
    ".zshrc",
    "bower_components",
    ".vscode",
    ".venv",
    "venv",
    "env",
    "site-packages",
    "dist",
    "build",
    "pip-wheel-metadata",
    ".egg-info",
    ".eggs",
    ".log",
    ".tmp",
    "3D Objects",
    "Contacts",
    "Scans",
    "Saved Games",
    "Searches",
    "pipx",
    "StreamBooth",
    ".mypy_cache*",
    ".mypy.ini",
    "packages",
    "uv.lock",
    ".python-version",
]
"""List[str]: List of file or directory parts to ignore during scans."""
# endregion
# region Constants -- IGNORE_EXTENSIONS
IGNORE_EXTENSIONS: List[str] = [
    ".pyc",
    ".pyo",
    ".db",
    ".sqlite",
    ".log",
    ".DS_Store",
    ".lock",
    ".dll",
    ".exe",
    ".lnk",
    "Thumbs.db",
    ".tmp",
    ".bak",
    ".swp",
    ".pyd",
    ".egg",
    ".egg-info",
    ".pkl",
    ".pickle",
    ".so",
    ".dylib",
    ".o",
    ".a",
    ".lib",
    ".obj",
    ".class",
    ".jar",
    ".war",
    ".ear",
    ".zip",
    ".tar",
    ".tar.gz",
    ".tgz",
    ".gz",
    ".bz2",
    ".xz",
    ".7z",
    ".rar",
    ".iso",
]
"""List[str]: List of file extensions to ignore during scans."""
# endregion
# region Constants -- MD_XREF
MD_XREF = {
    ".feature": "cucumber",
    ".abap": "abap",
    ".adb": "ada",
    ".ads": "ada",
    ".ada": "ada",
    ".ahk": "ahk",
    ".ahkl": "ahk",
    ".htaccess": "apacheconf",
    "apache.conf": "apacheconf",
    "apache2.conf": "apacheconf",
    ".applescript": "applescript",
    ".as": "as",
    ".asy": "asy",
    ".sh": "bash",
    ".ksh": "bash",
    ".bash": "bash",
    ".ebuild": "bash",
    ".eclass": "bash",
    ".bat": "bat",
    ".cmd": "bat",
    ".befunge": "befunge",
    ".bmx": "blitzmax",
    ".boo": "boo",
    ".bf": "brainfuck",
    ".b": "brainfuck",
    ".c": "c",
    ".h": "c",
    ".cfm": "cfm",
    ".cfml": "cfm",
    ".cfc": "cfm",
    ".tmpl": "cheetah",
    ".spt": "cheetah",
    ".cl": "cl",
    ".lisp": "cl",
    ".el": "cl",
    ".clj": "clojure",
    ".cljs": "clojure",
    ".cmake": "cmake",
    "CMakeLists.txt": "cmake",
    ".coffee": "coffeescript",
    ".sh-session": "console",
    "control": "control",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".c++": "cpp",
    ".h++": "cpp",
    ".cc": "cpp",
    ".hh": "cpp",
    ".cxx": "cpp",
    ".hxx": "cpp",
    ".pde": "cpp",
    ".cs": "csharp",
    ".css": "css",
    ".pyx": "cython",
    ".pxd": "cython",
    ".pxi": "cython",
    ".d": "d",
    ".di": "d",
    ".pas": "delphi",
    ".diff": "diff",
    ".patch": "diff",
    ".dpatch": "dpatch",
    ".darcspatch": "dpatch",
    ".duel": "duel",
    ".jbst": "duel",
    ".dylan": "dylan",
    ".dyl": "dylan",
    ".erb": "erb",
    ".erl-sh": "erl",
    ".erl": "erlang",
    ".hrl": "erlang",
    ".evoque": "evoque",
    ".factor": "factor",
    ".flx": "felix",
    ".flxh": "felix",
    ".f": "fortran",
    ".f90": "fortran",
    ".s": "gas",
    ".S": "gas",  # noqa: F601
    ".kid": "genshi",
    ".gitignore": "gitignore",
    ".vert": "glsl",
    ".frag": "glsl",
    ".geo": "glsl",
    ".plot": "gnuplot",
    ".plt": "gnuplot",
    ".go": "go",
    ".(1234567)": "groff",
    ".man": "groff",
    ".haml": "haml",
    ".hs": "haskell",
    ".html": "html",
    ".htm": "html",
    ".xhtml": "html",
    ".xslt": "html",  # noqa: F601
    ".hx": "hx",
    ".hy": "hybris",
    ".hyb": "hybris",
    ".ini": "ini",
    ".cfg": "ini",
    ".io": "io",
    ".ik": "ioke",
    ".weechatlog": "irc",
    ".jade": "jade",
    ".java": "java",
    ".js": "js",
    ".jsp": "jsp",
    ".lhs": "lhs",
    ".ll": "llvm",
    ".lgt": "logtalk",
    ".lua": "lua",
    ".wlua": "lua",
    ".mak": "make",
    "Makefile": "make",
    "makefile": "make",
    "Makefile.": "make",
    "GNUmakefile": "make",
    ".mao": "mako",
    ".maql": "maql",
    ".mhtml": "mason",
    ".mc": "mason",
    ".mi": "mason",
    "autohandler": "mason",
    "dhandler": "mason",
    ".md": "markdown",
    ".mo": "modelica",
    ".def": "modula2",
    ".mod": "modula2",
    ".moo": "moocode",
    ".mu": "mupad",
    ".mxml": "mxml",
    ".myt": "myghty",
    "autodelegate": "myghty",
    ".asm": "nasm",
    ".ASM": "nasm",
    ".ns2": "newspeak",
    ".objdump": "objdump",
    ".m": "objectivec",
    ".j": "objectivej",
    ".ml": "ocaml",
    ".mli": "ocaml",
    ".mll": "ocaml",
    ".mly": "ocaml",
    ".ooc": "ooc",
    ".pl": "perl",  # noqa: F601
    ".pm": "perl",
    ".php": "php",
    ".php(345)": "php",
    ".ps": "postscript",
    ".eps": "postscript",
    ".pot": "pot",
    ".po": "pot",
    ".pov": "pov",
    ".inc": "pov",
    ".prolog": "prolog",
    ".pro": "prolog",
    ".pl": "prolog",  # noqa: F601
    ".properties": "properties",
    ".proto": "protobuf",
    ".py3tb": "py3tb",
    ".pytb": "pytb",
    ".py": "python",
    ".pyw": "python",
    ".sc": "python",
    "SConstruct": "python",
    "SConscript": "python",
    ".tac": "python",
    ".R": "r",  # noqa: F601
    ".rb": "rb",
    ".rbw": "rb",
    "Rakefile": "rb",
    ".rake": "rb",
    ".gemspec": "rb",
    ".rbx": "rb",
    ".duby": "rb",
    ".Rout": "rconsole",
    ".r": "rebol",
    ".r3": "rebol",
    ".cw": "redcode",
    ".rhtml": "rhtml",
    ".rst": "rst",
    ".rest": "rst",
    ".sass": "sass",
    ".scala": "scala",
    ".scaml": "scaml",
    ".scm": "scheme",
    ".scss": "scss",
    ".st": "smalltalk",
    ".tpl": "smarty",
    "sources.list": "sourceslist",
    ".S": "splus",  # noqa: F601
    ".R": "splus",  # noqa: F601
    ".sql": "sql",
    ".sqlite3-console": "sqlite3",
    "squid.conf": "squidconf",
    ".ssp": "ssp",
    ".tcl": "tcl",
    ".tcsh": "tcsh",
    ".csh": "tcsh",
    ".tex": "tex",
    ".aux": "tex",
    ".toc": "tex",
    ".txt": "text",
    ".toml": "toml",
    ".v": "v",
    ".sv": "v",
    ".vala": "vala",
    ".vapi": "vala",
    ".vb": "vbnet",
    ".bas": "vbnet",
    ".vm": "velocity",
    ".fhtml": "velocity",
    ".vim": "vim",
    ".vimrc": "vim",
    ".xml": "xml",
    ".xsl": "xml",  # noqa: F601
    ".rss": "xml",  # noqa: F601
    ".xslt": "xml",  # noqa: F601
    ".xsd": "xml",
    ".wsdl": "xml",
    ".xqy": "xquery",
    ".xquery": "xquery",
    ".xsl": "xslt",  # noqa: F601
    ".xslt": "xslt",  # noqa: F601
    ".yaml": "yaml",
    ".yml": "yaml",
}
"""Dict[str, str]: Mapping of file extensions to markdown syntax highlighters."""
# endregion
# region Constants -- Format Enums


class ImageFormats(str, enum.Enum):
    """Enumeration of supported image formats."""

    PNG = ".png"  # Portable Network Graphics
    JPEG = ".jpeg"  # Joint Photographic Experts Group
    JPG = ".jpg"  # Common abbreviation for JPEG
    BMP = ".bmp"  # Bitmap Image File
    SVG = ".svg"  # Scalable Vector Graphics
    GIF = ".gif"  # Graphics Interchange Format
    WEBP = ".webp"  # Web Picture format
    TIFF = ".tiff"  # Tagged Image File Format
    HEIC = ".heic"  # High Efficiency Image Coding
    NEF = ".nef"  # Nikon Electronic Format


class DataFormats(str, enum.Enum):
    """Enumeration of supported data formats."""

    CSV = ".csv"  # Comma-Separated Values
    JSON = ".json"  # JavaScript Object Notation
    XML = ".xml"  # eXtensible Markup Language
    YAML = ".yaml"  # YAML Ain't Markup Language
    XLSX = ".xlsx"  # Microsoft Excel Open XML Spreadsheet
    PARQUET = ".parquet"  # Apache Parquet
    AVRO = ".avro"  # Apache Avro
    ORC = ".orc"  # Optimized Row Columnar


class VideoFormats(str, enum.Enum):
    """Enumeration of supported video formats."""

    MP4 = ".mp4"  # MPEG-4 Part 14
    AVI = ".avi"  # Audio Video Interleave
    MKV = ".mkv"  # Matroska Video File
    MOV = ".mov"  # Apple QuickTime Movie
    WMV = ".wmv"  # Windows Media Video
    FLV = ".flv"  # Flash Video
    WEBM = ".webm"  # WebM Video File
    MPG = ".mpg"  # MPEG Video File
    M4V = ".m4v"  # iTunes Video File


# endregion
# region Constants -- Derived Lists

IMAGE_FORMAT_LIST: List[str] = [fmt.value for fmt in ImageFormats]
"""List[str]: Lists of supported formats for images, data, and videos."""
DATA_FORMAT_LIST: List[str] = [fmt.value for fmt in DataFormats]
"""List[str]: Lists of supported formats for images, data, and videos."""
VIDEO_FORMAT_LIST: List[str] = [fmt.value for fmt in VideoFormats]
"""List[str]: Lists of supported formats for images, data, and videos."""
MARKDOWN_EXTENSIONS: list[str] = list(MD_XREF.keys())
"""[List[str]]: List of markdown file extensions for syntax highlighting."""

# endregion


__all__ = [
    "IGNORE_PARTS",
    "IGNORE_EXTENSIONS",
    "ImageFormats",
    "DataFormats",
    "VideoFormats",
    "IMAGE_FORMAT_LIST",
    "DATA_FORMAT_LIST",
    "VIDEO_FORMAT_LIST",
    "MARKDOWN_EXTENSIONS",
]
