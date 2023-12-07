import dataclasses
import datetime
import enum
import pathlib
import typing

import dulwich.porcelain
import dulwich.repo
from cleo.io.io import IO
from poetry.core.constraints.version import Version as PoetryVersion
from poetry.core.version.pep440.segments import Release as PoetryRelease
from poetry.plugins.plugin import Plugin as PoetryPlugin
from poetry.poetry import Poetry


class VersionStyle(str, enum.Enum):
    @staticmethod
    def _generate_next_value_(
        member_name: str, start: int, count: int, last_values: list
    ) -> str:
        return member_name.lower().replace("_", "-")

    PEP440_CANONICALIZED = enum.auto()
    ZERO_PADDED = enum.auto()

    def __str__(self) -> str:
        return self.value

    def build_version(self, dt: datetime.datetime, local: str) -> PoetryVersion:
        extra = (dt.hour * 10000) + (dt.minute * 100) + dt.second
        release = PoetryRelease(
            major=dt.year,
            minor=dt.month,
            patch=dt.day,
            extra=(extra,),
        )
        if self == VersionStyle.PEP440_CANONICALIZED:
            return PoetryVersion(release=release, local=local)

        vtxt = f"{dt.year}.{dt.month:02}.{dt.day:02}.{extra:06}"
        return _Version(release=release, text=f"{vtxt}+{local}", local=local)


@dataclasses.dataclass(frozen=True)
class _Config:
    enable: bool = False
    version_style: VersionStyle = VersionStyle.ZERO_PADDED

    @staticmethod
    def from_toml_data(data: dict) -> "_Config":
        section = data.get("tool", {}).get("poetry-commit-date-versioning", {})
        return _Config(
            enable=section.get("enable", False),
            version_style=VersionStyle(
                section.get("version-style", VersionStyle.PEP440_CANONICALIZED.value)
            ),
        )


class _Version(PoetryVersion):
    """Wrap the to_string behavior of the base poetry version type to just return the
    base object's text field if that field has been set. By default the poetry version
    type will normalize integers - the right thing to do in general but not for date-
    based version schemes."""

    def to_string(self, short: bool = False) -> str:
        return self.text if self.text else super().to_string(short)


def version_from_repo(
    repo: dulwich.repo.BaseRepo, style: VersionStyle
) -> PoetryVersion:
    head = repo[repo.head()]
    dt = datetime.datetime.fromtimestamp(
        head.commit_time,
        datetime.timezone(datetime.timedelta(seconds=head.commit_timezone)),
    ).astimezone(datetime.timezone.utc)
    return style.build_version(dt, head.sha().hexdigest()[:7])


class Plugin(PoetryPlugin):
    def activate(self, poetry: Poetry, io: IO):
        config = _Config.from_toml_data(poetry.pyproject.data)
        if not config.enable:
            return

        gitroot = _find_git_root()
        if not gitroot:
            io.write_error_line(
                "poetry-commit-date-versioning plugin is enabled but this is not a git repository"
            )
            return
        with dulwich.porcelain.open_repo_closing(str(gitroot)) as repo:
            poetry.package.version = version_from_repo(repo, config.version_style)


def _find_git_root(
    path: pathlib.Path = pathlib.Path.cwd(),
) -> typing.Optional[pathlib.Path]:
    if (path / ".git").is_dir():
        return path
    parent = path.parent
    if parent == path:
        return None
    return _find_git_root(parent)
