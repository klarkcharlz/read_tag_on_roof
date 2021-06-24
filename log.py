import logging


logger = logging.getLogger('sllurp')
log_level = logging.INFO
log_format = '%(asctime)s %(name)s: %(levelname)s: %(message)s'
formatter = logging.Formatter(log_format)
stderr = logging.StreamHandler()
stderr.setFormatter(formatter)
root = logging.getLogger()
root.setLevel(log_level)
root.handlers = [stderr]
logger.log(log_level, 'log level: %s', logging.getLevelName(log_level))
