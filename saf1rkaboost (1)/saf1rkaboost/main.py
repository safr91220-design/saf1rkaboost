import sys

def main():
    if sys.platform != "win32":
        print("saf1rkaboost работает только в Windows 10/11."); return 1
    from saf1rkaboost.logger import setup, log
    setup()
    if "--restore" in sys.argv:
        from saf1rkaboost.desktop import force_restore
        force_restore(); print("Панель задач и значки возвращены."); return 0
    from PySide6.QtWidgets import QApplication
    from saf1rkaboost.ui import MainWindow
    from saf1rkaboost.menu import MenuWindow
    app = QApplication(sys.argv)
    win = MainWindow() if "--full" in sys.argv else MenuWindow()

    def hook(t, v, tb):
        log.critical("Необработанная ошибка", exc_info=(t, v, tb))
        try:
            win.engine.disable()
        except Exception:
            pass
    sys.excepthook = hook
    app.aboutToQuit.connect(win.engine.disable)
    win.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
