import typing as tp

from yara.apps.auth.services import AuthService
from yara.core.commands import Option, command, echo


@command
async def create_superuser(  # type: ignore [no-untyped-def]
    email: tp.Annotated[
        str,
        Option(
            prompt=True,
            help="Email of the superuser",
        ),
    ],
    password: tp.Annotated[
        str,
        Option(
            prompt=True,
            confirmation_prompt=True,
            hide_input=True,
            help="Password of the superuser",
        ),
    ],
    group_name: tp.Annotated[
        str,
        Option(
            prompt=True,
            help="Group Name of the superuser",
        ),
    ],
    root_app=Option(None, hidden=True),
) -> None:
    auth_service = AuthService(root_app)
    await auth_service.create_user(
        email,
        password,
        group_name=group_name,
        is_superuser=True,
        is_group_moderator=True,
    )
    echo("Super User has been created")


@command
async def create_group_moderator(  # type: ignore [no-untyped-def]
    email: tp.Annotated[
        str,
        Option(
            prompt=True,
            help="Email of the superuser",
        ),
    ],
    password: tp.Annotated[
        str,
        Option(
            prompt=True,
            confirmation_prompt=True,
            hide_input=True,
            help="Password of the superuser",
        ),
    ],
    group_name: tp.Annotated[
        str,
        Option(
            prompt=True,
            help="Group Name of the superuser",
        ),
    ],
    root_app=Option(None, hidden=True),
) -> None:
    auth_service = AuthService(root_app)
    await auth_service.create_user(
        email,
        password,
        group_name=group_name,
        is_superuser=False,
        is_group_moderator=True,
    )
    echo("Group Moderator has been created")
