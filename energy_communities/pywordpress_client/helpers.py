import os


def getenv_or_fail(env_name, default=None):
    value = os.getenv(env_name, default)
    if value:
        return value
    raise Exception("Can't find envvar {}".format(env_name))
