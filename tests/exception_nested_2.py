from logger_tt import setup_logging
from logging import getLogger


__author__ = "Duc Tin"
setup_logging()
logger = getLogger(__name__)


class Base:
    def __init__(self):
        self.name = 'Nested dot'


class Dummy:
    def __init__(self):
        self.value = 3
        self.divisor = 0
        self.base = Base()

    def details(self, arg):
        print(f'{self.value} {self.non_exist} {self.base.name}')

    def __str__(self):
        return 'Dummy(my dummy class)'


def my_function(var_in, *arg, **kwargs):
    my_local_var = 345
    var_in.details(my_local_var)


if __name__ == '__main__':
    a = Dummy()
    my_function(a, 456, 789, my_kw='hello', another_kw='world')
