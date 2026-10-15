from .app_config import AppConfig
from .application import ChatApplication


def main():
    ChatApplication(AppConfig.load()).run()


if __name__ == "__main__":
    main()
