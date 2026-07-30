import logging, sys
formatter=logging.Formatter('%(asctime)s|%(levelname)s|%(name)s|step=%(step)s|%(message)s', datefmt='%Y-%m-%dT%H:%M:%SZ')
handler=logging.StreamHandler(sys.stdout); handler.setFormatter(formatter)
logger=logging.getLogger('checkout.worker'); logger.handlers=[handler]; logger.setLevel(logging.INFO); logger.propagate=False
logger.info('accepted real request req-81', extra={'step': 1})
logger.warning('retrying payment authorization req-81', extra={'step': 2})
logger.error('authorization exhausted req-81', extra={'step': 3})
