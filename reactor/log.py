import logging

format_str = '%(levelname)s: %(asctime)s: %(filename)s:%(lineno)d * %(thread)d %(message)s'
datefmt = '%y-%m-%d %H:%M:%S'
formatter = logging.Formatter(format_str, datefmt)
logging.basicConfig(filename='web-app.log', level=logging.INFO, format=format_str)
log = logging.getLogger()

def with_log(cls):
    """属性方法
    """
    @property
    def log(self):
        try:
            return self._log
        except AttributeError:
            self._log = logging.root.getChild(
                self.__class__.__module__ + '.' + self.__class__.__name__
            )
            return self._log
    cls.log = log
    return cls
