from datetime import date

from cadwyn.structure import Version, VersionBundle, VersionChange, schema
from monite_common.context import context_vars

from .latest import ResponseModel


class RenameMyVersion1ToMyVersion2(VersionChange):
    description = "Rename my_version1 to my_version2 in the response model to validate that the versioning works."
    instructions_to_migrate_to_previous_version = (
        schema(ResponseModel).field("my_version2").didnt_exist,
        schema(ResponseModel).field("my_version1").existed_as(type=int),
    )


version_bundle = VersionBundle(
    Version(date(2022, 2, 2), RenameMyVersion1ToMyVersion2),
    Version(date(2021, 1, 1)),
    api_version_var=context_vars["api_version"],
)
