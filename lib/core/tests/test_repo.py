from hashlib import sha256
from pathlib import Path

from pytest import fixture

import core.base as cb
import core.models.repo as rp
import core.models.file_system as fs


@fixture
def sample_repo() -> rp.Repo:
    """Create a sample Repo instance from this repository."""
    repo_path = Path(__file__).parent.parent.parent.parent.resolve()
    print(f"Loading sample repo from path: {repo_path}")
    return rp.Repo.populate(repo_path)


def test_repo(sample_repo: rp.Repo):
    """Test the Repo model population and attributes."""
    repo = sample_repo
    assert repo.path_json is not None and isinstance(repo.path_json, cb.FilePath)
    assert repo.stat_json is not None and isinstance(repo.stat_json, fs.BaseFileStat)
    assert repo.git_metadata is not None and isinstance(
        repo.git_metadata, rp.GitMetadata
    )
    assert repo.git_metadata.latest_commit is not None and isinstance(
        repo.git_metadata.latest_commit, rp.GitCommit
    )
    assert len(repo.files) > 0
    for file in repo.files:
        assert isinstance(file, rp.RepoFile)
        assert file.path_json is not None and isinstance(file.path_json, cb.FilePath)
        assert file.stat_json is not None and isinstance(
            file.stat_json, fs.BaseFileStat
        )
        assert file.sha256 is not None and isinstance(file.sha256, str)
        assert file.id is not None and isinstance(file.id, str)
        assert file.repo_id == repo.id
        assert file.uuid is not None and isinstance(file.uuid, str)
        if file.lines:
            for line in file.lines:
                assert isinstance(line, fs.TextFileLine)
                assert line.file_id == file.id
                assert (
                    line.content_hash
                    == sha256(line.content.encode("utf-8")).hexdigest()
                )
