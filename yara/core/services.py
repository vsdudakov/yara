from yara.main import YaraRootApp


class YaraService:
    root_app: YaraRootApp

    def __init__(self, root_app: YaraRootApp) -> None:
        self.root_app = root_app
