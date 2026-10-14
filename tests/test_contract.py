import importlib.resources

import indgroup

# The public API. Add every exported name here as the library grows; this list is the
# contract and the test below fails if the module and this list disagree.
PUBLIC_API: list[str] = [
    "Grouping",
    "Number",
    "NumberSymbols",
    "cldr_version",
    "format_indian",
    "format_number",
    "number_symbols",
    "parse_indian",
    "parse_number",
    "resolve_locale",
    "supported_locales",
]


def test_all_lists_exactly_the_public_api() -> None:
    assert sorted(indgroup.__all__) == sorted(PUBLIC_API)


def test_every_exported_name_resolves() -> None:
    for name in indgroup.__all__:
        assert hasattr(indgroup, name)


def test_version_is_a_three_part_string() -> None:
    parts = indgroup.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_the_package_ships_type_information_and_its_table() -> None:
    package = importlib.resources.files("indgroup")
    assert package.joinpath("py.typed").is_file()
    assert package.joinpath("_cldr.json").is_file()
