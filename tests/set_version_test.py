import datetime
import time

import dulwich.objects
import dulwich.repo

import dateversioning as dv


def test_version_style_values():
    assert dv.VersionStyle.PEP440_CANONICALIZED == "pep440-canonicalized"
    assert dv.VersionStyle.ZERO_PADDED == "zero-padded"
    assert (
        dv.VersionStyle(str(dv.VersionStyle.ZERO_PADDED)) == dv.VersionStyle.ZERO_PADDED
    )
    assert (
        dv.VersionStyle(str(dv.VersionStyle.PEP440_CANONICALIZED))
        == dv.VersionStyle.PEP440_CANONICALIZED
    )


def test_config_defaults():
    toml = {}
    cfg = dv._Config.from_toml_data(toml)
    assert not cfg.enable
    assert cfg.version_style == dv.VersionStyle.PEP440_CANONICALIZED


def test_config():
    toml = {
        "tool": {
            "poetry-commit-date-versioning": {
                "enable": True,
                "version-style": "zero-padded",
            }
        }
    }
    cfg = dv._Config.from_toml_data(toml)
    assert cfg.enable
    assert cfg.version_style == dv.VersionStyle.ZERO_PADDED


def test_padded():
    utc_timestamp = datetime.datetime(2010, 6, 1, 7, 5, 2, 0, datetime.timezone.utc)
    offset = datetime.timedelta(hours=-4)
    commit_ts = utc_timestamp.astimezone(datetime.timezone(offset))
    repo = repo_with_commit(commit_ts)
    shortsha = repo.head().decode("ASCII")[:7]

    v = dv.version_from_repo(repo, dv.VersionStyle.ZERO_PADDED)
    assert v.to_string() == f"2010.06.01.070502+{shortsha}"

    v = dv.version_from_repo(repo, dv.VersionStyle.PEP440_CANONICALIZED)
    assert v.to_string() == f"2010.6.1.70502+{shortsha}"


def repo_with_commit(commit_ts: datetime.datetime) -> dulwich.repo.BaseRepo:
    repo = dulwich.repo.MemoryRepo()
    blob = dulwich.objects.Blob.from_string(b"file content\n")
    tree = dulwich.objects.Tree()
    tree.add(b"spam", 0o100644, blob.id)
    commit = dulwich.objects.Commit()
    commit.tree = tree.id
    author = b"Arthur Author <arthur@example.com>"
    commit.author = commit.committer = author
    commit.commit_time = commit.author_time = int(time.mktime(commit_ts.timetuple()))
    offset = commit_ts.utcoffset() or datetime.timedelta()
    commit.commit_timezone = commit.author_timezone = offset.seconds
    commit.encoding = b"UTF-8"
    commit.message = b"Initial commit"
    object_store = repo.object_store
    object_store.add_object(blob)
    object_store.add_object(tree)
    object_store.add_object(commit)
    repo.refs[b"refs/heads/main"] = commit.id
    repo.refs.set_symbolic_ref(b"HEAD", b"refs/heads/main")
    return repo
