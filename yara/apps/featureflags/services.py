from uuid import UUID

from yara.adapters.orm.adapter import ORMAdapter
from yara.adapters.orm.backends.schemas import SelectClause, where_clause
from yara.apps.featureflags.models import FeatureFlag
from yara.core.services import YaraService
from yara.main import YaraRootApp


class FeatureFlagService(YaraService):
    orm_adapter: ORMAdapter[FeatureFlag]

    def __init__(self, root_app: YaraRootApp) -> None:
        super().__init__(root_app)
        self.orm_adapter: ORMAdapter[FeatureFlag] = self.root_app.get_adapter(ORMAdapter)

    async def get_feature_flags(self, for_id: UUID, for_type: str) -> list[str]:
        rows = await self.orm_adapter.backend.select(
            FeatureFlag.__table__,
            SelectClause(
                columns=["feature_flag"],
                where=where_clause(
                    for_id=str(for_id),
                    for_type=for_type,
                    enabled=True,
                ),
            ),
        )
        return [r["feature_flag"] for r in rows]
