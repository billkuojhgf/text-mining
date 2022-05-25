import re
import configparser

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
from typing import Dict
from fhirpy import SyncFHIRClient
from fhirpy.lib import SyncFHIRResource
from fhirpy.base.searchset import FHIR_DATE_FORMAT
from fhirpy.base.exceptions import ResourceNotFound
from dateutil.relativedelta import relativedelta

config = configparser.ConfigParser()
config.read("./config.ini")
CLIENT = SyncFHIRClient(config['fhir_server']['FHIR_SERVER_URL'])


# FHIR_DATE_FORMAT='%Y-%m-%d'

class GetFuncMgmt:
    """
    The Context defines the interface of interest to clients.
    """

    def __init__(self, strategy: GetFuncInterface) -> None:
        """
        First, the Context accepts a strategy through the constructor, but
        also provides a setter to change it at runtime.
        """

        self._strategy = strategy

    @property
    def strategy(self) -> GetFuncInterface:
        """
        The Context maintains a reference to one of the Strategy objects. The
        Context does not know the concrete class of a strategy. It should work
        with all strategies via the Strategy interface.
        """

        return self._strategy

    @strategy.setter
    def strategy(self, strategy: GetFuncInterface) -> None:
        """
        Usually, the Context allows replacing a Strategy object at runtime.
        """

        self._strategy = strategy

    def get_patient_resources(self, resources: List, table: Dict) -> SyncFHIRResource:
        """
        The Context delegates some work to the Strategy object instead of
        implementing multiple versions of the algorithm on its own.
        """

        # ...

        print("Getting patient's data with the {} method".format(self._strategy.__name__))
        resource = self._strategy.execute()
        return resource

        # ...


class GetFuncInterface(ABC):
    """
    The Strategy interface declares operations common to all supported versions
    of some algorithm.

    The Context uses this interface to call the algorithm defined by Concrete
    Strategies.
    """

    @abstractmethod
    def execute(self, data: List) -> SyncFHIRResource:
        pass


class GetMax(GetFuncInterface):
    def execute(self, data: List) -> SyncFHIRResource:
        return sorted(data)


class GetMin(GetFuncInterface):
    def execute(self, data: List) -> SyncFHIRResource:
        return sorted(data)


class GetLatest(GetFuncInterface):
    def execute(self, data: List) -> SyncFHIRResource:
        return sorted(data)


class GetResourcesMgmt

def get_patient_resources(patient_id, table, default_time, data_alive_time=None) -> SyncFHIRResource:
    """
    The function will get the patient's resources from the database and return
    :param patient_id: patient's id
    :param table: feature's table,
                  dict type with {'code', 'data_alive_time', 'type_of_data', 'default_value', 'search_type'}
    :param default_time: the time of the default, for model training used. DEFAULT=datetime.now()
    :param data_alive_time: the time range, start from the default_time.
                            e.g. if the data_alive_time is 2 years, and the default_time is not, the server will search
                                 the data that is between now and two years ago
    :return:
    """

    pass


if __name__ == "__main__":
    # The client code picks a concrete strategy and passes it to the context.
    # The client should be aware of the differences between strategies in order
    # to make the right choice.

    context = GetFuncMgmt(ConcreteStrategyA())
    print("Client: Strategy is set to normal sorting.")
    context.get_patient_resources()
    print()

    print("Client: Strategy is set to reverse sorting.")
    context.strategy = ConcreteStrategyB()
    context.get_patient_resources()
