# poetry-commit-date-versioning

Date-based versioning for Poetry projects. Reads the commit date and sha from
git and uses it to set the project version. Nothing else. No attempt is made to
work with anything other than git.

To use:

1. `poetry self add poetry-commit-date-versioning`
1. In pyproject.toml add a stanza to enable the plugin for a given project

```.toml
[tool.poetry-commit-date-versioning]
enable = true
```

You can optionally indicate whether the plugin should generate zero-padded
version segments or pep440 canonicalized segments. With padding, version number
segments are left-padded with zeros to extend to the maximum possible width of
the field. For example a version number including the month of January 1980
would be padded to start with `1980.01`. With canonicalization that same version
number would be `1980.1`. By default, pep440 canonicaization is used but padding
can be enabled with the `version-style` configuration field. This field accepts
one of two values: `"pep440-canonicalized"` or `"zero-padded"`

```.toml
[tool.poetry-commit-date-versioning]
enable = true
version-style = "zero-padded"
```

As the version number is not written into source code files anywhere, we
suggest using `importlib` to determine your module's version number.

```.py
from importlib import metadata

__version__ = metadata.version(__name__)

```

This project was created as an alternative to

- [poetry dynamic
  versioning](https://github.com/mtkennerly/poetry-dynamic-versioning) because
  it rewrites the pyproject.toml file with every invocation (even if nothing
  has changed) and is thus incompatible with a development process that uses
  pyproject.toml file in Makefile dependencies.
- [poetry date versioning
  plugin](https://github.com/miigotu/poetry-date-version-plugin) which may be
  abandoned and incomplete and which is definitely centered around writing
  version numbers into python source files.

