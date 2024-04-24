from uuid import UUID

from yara.apps.auth.helpers import get_authenticated_group_id
from yara.apps.auth.models import Group
from yara.apps.featureflags.services import FeatureFlagService
from yara.core.api_router import Depends, YaraApiRouter, get_service

feature_flags_router = YaraApiRouter(
    prefix="/feature-flags",
    tags=["feature-flags"],
)


@feature_flags_router.get("", response_model=list[str])
async def get_feature_flags(
    authenticated_group_id: UUID = Depends(get_authenticated_group_id),
    feature_flag_service: FeatureFlagService = Depends(get_service(FeatureFlagService)),
) -> list[str]:
    return await feature_flag_service.get_feature_flags(authenticated_group_id, Group.__table__)
