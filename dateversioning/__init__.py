import datetime
import pathlib
import typing

import dulwich.porcelain
import dulwich.repo
from cleo.io.io import IO
from poetry.core.constraints.version import Version as PoetryVersion
from poetry.core.version.pep440.segments import Release as PoetryRelease
from poetry.plugins.plugin import Plugin as PoetryPlugin
from poetry.poetry import Poetry


class Version(PoetryVersion):
    """Wrap the to_string behavior of the base poetry version type to just return the
    base object's text field if that field has been set. By default the poetry version
    type will normalize integers - the right thing to do in general but not for date-
    based version schemes."""

    def to_string(self, short: bool = False) -> str:
        return self.text if self.text else super().to_string(short)


class Plugin(PoetryPlugin):
    def activate(self, poetry: Poetry, io: IO):
        if not _enabled(poetry):
            return
        gitroot = _find_git_root()
        if not gitroot:
            io.write_error_line(
                "poetry-commit-date-versioning plugin is enabled but this is not a git repository"
            )
            return
        with dulwich.porcelain.open_repo_closing(str(gitroot)) as repo:
            head = repo[repo.head()]
            shortsha = head.sha().hexdigest()[:7]
            dt = datetime.datetime.fromtimestamp(
                head.author_time,
                datetime.timezone(datetime.timedelta(seconds=head.author_timezone)),
            )
            extra = (dt.hour * 10000) + (dt.minute * 100) + dt.second
            vtxt = f"{dt.year}.{dt.month:02}.{dt.day:02}.{extra:06}"
            v = Version(
                release=PoetryRelease(
                    major=dt.year,
                    minor=dt.month,
                    patch=dt.day,
                    extra=(extra,),
                ),
                text=f"{vtxt}+{shortsha}",
                local=shortsha,
            )
            poetry.package.version = v


def _find_git_root(
    path: pathlib.Path = pathlib.Path.cwd(),
) -> typing.Optional[pathlib.Path]:
    if (path / ".git").is_dir():
        return path
    parent = path.parent
    if parent == path:
        return None
    return _find_git_root(parent)


def _enabled(poetry: Poetry) -> bool:
    """looks up [tool.poetry-commit-date-versioning] enable = true|false"""
    return (
        poetry.pyproject.data.get("tool", {})
        .get("poetry-commit-date-versioning", {})
        .get("enable", False)
    )
