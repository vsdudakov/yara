import typing as tp
from uuid import UUID

from yara.apps.auth.helpers import get_authenticated_group_id
from yara.apps.auth.models import Group
from yara.apps.featureflags.services import FeatureFlagService
from yara.core.api_router import Depends, YaraApiRouter, get_root_app

feature_flags_router = YaraApiRouter(
    prefix="/feature-flags",
    tags=["feature-flags"],
)


@feature_flags_router.get("", response_model=list[str])
async def get_feature_flags(
    authenticated_group_id: UUID = Depends(get_authenticated_group_id),
    root_app: tp.Any = Depends(get_root_app),
) -> list[str]:
    service = FeatureFlagService(root_app)
    return await service.get_feature_flags(authenticated_group_id, Group.__table__)
