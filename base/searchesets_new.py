import re
import configparser

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
from typing import Dict
from fhirpy import SyncFHIRClient
from fhirpy.lib import SyncFHIRResource
from fhirpy.base.searchset import datetime
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

    def __init__(self, strategy: GetFuncInterface = None) -> None:
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

    def get_data_with_func(self, resources: List, table: Dict) -> SyncFHIRResource:
        """
        The Context delegates some work to the Strategy object instead of
        implementing multiple versions of the algorithm on its own.
        """

        # ...
        if self._strategy is None:
            raise AttributeError("Strategy was not set yet. Set the strategy with 'foo.strategy = bar()'")

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


class GetResourceMgmt:
    """
    The Context defines the interface of interest to clients.
    """

    def __init__(self, strategy: ResourcesInterface = None) -> None:
        """
        First, the Context accepts a strategy through the constructor, but
        also provides a setter to change it at runtime.
        """

        self._strategy = strategy

    @property
    def strategy(self) -> ResourcesInterface:
        """
        The Context maintains a reference to one of the Strategy objects. The
        Context does not know the concrete class of a strategy. It should work
        with all strategies via the Strategy interface.
        """

        return self._strategy

    @strategy.setter
    def strategy(self, strategy: ResourcesInterface) -> None:
        """
        Usually, the Context allows replacing a Strategy object at runtime.
        """

        self._strategy = strategy

    def get_patient_resources(self, patient_id: str,
                              table: Dict, default_time, data_alive_time=None) -> SyncFHIRResource:
        """
        The Context delegates some work to the Strategy object instead of
        implementing multiple versions of the algorithm on its own.
        """

        # ...
        if self._strategy is None:
            raise AttributeError("Strategy was not set yet. Set the strategy with 'foo.strategy = bar()'")

        print("Getting patient's data with the {} method".format(self._strategy.__name__))
        resource_list = self._strategy.search(patient_id, table, default_time, data_alive_time)
        return resource_list


class ResourcesInterface(ABC):
    """
    The Strategy interface declares operations common to all supported versions
    of some algorithm.

    The Context uses this interface to call the algorithm defined by Concrete
    Strategies.
    """

    @abstractmethod
    def search(self, patient_id: str, table: dict, default_time: str, data_alive_time=None) -> Dict:
        pass


class Observation(ResourcesInterface):
    def search(self, patient_id: str, table: dict, default_time: str, data_alive_time=None) -> Dict:
        data_time_since = (default_time - relativedelta(
            years=table['data_alive_time'].get_years(),
            months=table['data_alive_time'].get_months(),
            days=table['data_alive_time'].get_days(),
            hours=table['data_alive_time'].get_hours(),
            minutes=table['data_alive_time'].get_minutes(),
            seconds=table['data_alive_time'].get_seconds()
        )).strftime(FHIR_DATE_FORMAT)
        code = table['code']

        resources = CLIENT.resources('Observation')
        search = resources.search(
            subject=patient_id,
            data__ge=data_time_since,
            code=code
        ).sort('-date')
        results = search.fetch()
        is_in_component = False

        if len(results) == 0:
            """
            如果resources的長度為0，代表Server裡面沒有這個病患的code data，
            可能是在component-code之中，所以再透過component-code去搜尋
            """

            search = resources.search(
                subject=patient_id,
                date__ge=data_time_since,
                component_code=code
            ).sort('-date')
            results = search.fetch
            is_in_component = True

            if len(results) == 0:
                """
                如果再次搜尋後的結果依舊為0，代表資料庫中沒有此數據，回傳錯誤到前端(可能還可以想一些其他的解決方案)
                """

                raise ResourceNotFound(
                    'Could not find the resources {code} under time {time}, no enough data for the patient'.format(
                        code=code,
                        time=data_time_since
                    )
                )

        return {'resource': results, 'component_code': code if is_in_component else None,
                'type': 'Observation'}


class Condition(ResourcesInterface):
    def search(self, patient_id: str, table: dict, default_time: str, data_alive_time=None) -> Dict:
        code = table['code']

        resources = CLIENT.resources('Condition')
        search = resources.search(
            subject=patient_id,
            code=code
        ).sort('recorded-date')
        results = search.fetch()

        # 如果result的長度為0，代表病人沒有這個症狀，那就回傳None, 否則回傳結果
        # Consider: 如果這裡不回傳result, 而是回傳true or false，又會如何？
        # Consider: 我有需要回傳整個result list嗎？還是只要回傳一個就好？有什麼情況需要我回傳整個list？計算染疫次數嗎？
        return {'resources': None if len(resources) == 0 else results, 'component_code': None,
                'type': 'Condition'}


class Patient(ResourcesInterface):
    def search(self, patient_id: str, table: dict, default_time: str, data_alive_time=None) -> Dict:
        resources = CLIENT.resources('Patient')
        search = resources.search(_id=patient_id).limit(1)
        patient = search.get()

        result = None
        if table['code'] == 'age':
            result = getattr(self, "get_{}".format(str(table['code']).lower()))(patient, default_time)
        return {
            "resource": result, "component_code": None, 'type': "Patient"
        }

    @staticmethod
    def get_age(self, patient: SyncFHIRResource, default_time) -> int:
        patient_birthdate = datetime.datetime.strptime(
            patient.birthDate, FHIR_DATE_FORMAT)
        # If we need to calculate the real age that is 1 year before or so (depends on the default_time)
        # , then calculate it by minus method.
        age = default_time - patient_birthdate
        return int(age.days / 365)


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
    :return: SyncFHIRResources
    """
    get_patient_resources_mgmt = GetResourceMgmt()
    get_patient_resources_mgmt.strategy = globals()[str(table["type_of_data"]).capitalized()]
    resources_list = get_patient_resources_mgmt.get_patient_resources(patient_id, table, default_time)
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
