from uuid import UUID

from yara.apps.orm.models import UUIDModel


class FeatureFlag(UUIDModel):
    __table__ = "yara__featureflags__featureflag"

    for_id: UUID
    for_type: str

    feature_flag: str
    enabled: bool = False
