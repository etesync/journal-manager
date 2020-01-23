import sys  # noqa


class AppSettings:
    def __init__(self, prefix):
        self.prefix = prefix

    def import_from_str(self, name):
        from importlib import import_module

        p, m = name.rsplit('.', 1)

        mod = import_module(p)
        return getattr(mod, m)

    def _setting(self, name, dflt):
        from django.conf import settings
        return getattr(settings, self.prefix + name, dflt)

    @property
    def API_PERMISSIONS(self):
        perms = self._setting("API_PERMISSIONS", ('rest_framework.permissions.IsAuthenticated', ))
        ret = []
        for perm in perms:
            ret.append(self.import_from_str(perm))
        return ret

    @property
    def API_AUTHENTICATORS(self):
        perms = self._setting("API_AUTHENTICATORS", ('rest_framework.authentication.TokenAuthentication',
                                                     'rest_framework.authentication.SessionAuthentication'))
        ret = []
        for perm in perms:
            ret.append(self.import_from_str(perm))
        return ret


# Ugly? Guido recommends this himself ...
# http://mail.python.org/pipermail/python-ideas/2012-May/014969.html
app_settings = AppSettings('JOURNAL_')
app_settings.__name__ = __name__  # pylint: disable=attribute-defined-outside-init
sys.modules[__name__] = app_settings
