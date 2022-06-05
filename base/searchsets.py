import datetime
import re
import configparser
from fhirpy import SyncFHIRClient
from fhirpy.base.searchset import *
from fhirpy.base.exceptions import ResourceNotFound
from dateutil.relativedelta import relativedelta


config = configparser.ConfigParser()
config.read("./config.ini")
CLIENT = SyncFHIRClient('http://localhost:8080/fhir')
"""FHIR_DATE_FORMAT = "%Y-%m-%d"""


def get_patient_resources(patient_id, table, default_time, data_alive_time=None):
    """

    :param patient_id: patient's id
    :param table: feature's table,
            example:{""}
    :param default_time:
    :param data_alive_time:
    :return:
    """
    if table['type_of_data'].lower() == 'observation':
        resources = CLIENT.resources('Observation')
        search = resources.search(
            subject=patient_id,
            date__ge=(default_time - relativedelta(
                years=table['data_alive_time'].get_years(),
                months=table['data_alive_time'].get_months(),
                days=table['data_alive_time'].get_days(),
                hours=table['data_alive_time'].get_hours(),
                minutes=table['data_alive_time'].get_minutes(),
                seconds=table['data_alive_time'].get_seconds()
            )).strftime(FHIR_DATE_FORMAT),
            code=table['code']
        ).sort('-date').limit(1)
        results = search.fetch()
        is_in_component = False

        if len(results) == 0:
            """
            如果resources的長度為0，代表Server裡面沒有這個病患的code data，
            可能是在component-code之中，所以再透過component-code去搜尋
            """

            search = resources.search(
                subject=patient_id,
                date__ge=(default_time - relativedelta(
                    years=table['data_alive_time'].get_years(),
                    months=table['data_alive_time'].get_months(),
                    days=table['data_alive_time'].get_days(),
                    hours=table['data_alive_time'].get_hours(),
                    minutes=table['data_alive_time'].get_minutes(),
                    seconds=table['data_alive_time'].get_seconds()
                )).strftime(FHIR_DATE_FORMAT),
                component_code=table['code']
            ).sort('-date').limit(1)
            results = search.fetch()
            is_in_component = True
            if len(results) == 0:
                """
                如果resources的長度還是為0，代表Server裡面真的沒有這個病患的code data，
                所以就回傳Resource not found error
                """
                raise ResourceNotFound(
                    'Could not find the resources {code} under time {time}, no enough data for the patient'.format(
                        code=table['code'],
                        time=default_time - relativedelta(
                            years=table['data_alive_time'].get_years(),
                            months=table['data_alive_time'].get_months(),
                            days=table['data_alive_time'].get_days(),
                            hours=table['data_alive_time'].get_hours(),
                            minutes=table['data_alive_time'].get_minutes(),
                            seconds=table['data_alive_time'].get_seconds()
                        )
                    )
                )
        for result in results:
            return {'resource': result, 'is_in_component': is_in_component,
                    'component-code': table['code'] if is_in_component else '', 'type': 'laboratory'}

    elif table['type_of_data'].lower() == 'condition':
        resources = CLIENT.resources('Condition')
        search = resources.search(
            # subject=id, code=table['code']).sort('-date').limit(1) doesn't know why it would go wrong in HAPI
            subject=patient_id, code=table['code']).limit(1)
        results = search.fetch()
        if len(results) == 0:  # 沒有此condition的搜尋結果
            return {'resource': None, 'is_in_component': False, 'type': 'diagnosis'}
        else:
            for result in results:
                return {'resource': result, 'is_in_component': False, 'type': 'diagnosis'}

    else:
        raise Exception('unknown type of data')


def get_age(patient_id, default_time):
    # TODO: 把取得Patient資料的這個流程加入到get_resources中
    # Getting patient data from server
    resources = CLIENT.resources('Patient')
    search = resources.search(_id=patient_id).limit(1)
    patient = search.get()
    patient_birthdate = datetime.datetime.strptime(
        patient.birthDate, '%Y-%m-%d')
    # If we need the data that is 1 year before or so, return the real age at the time
    age = default_time - patient_birthdate
    return int(age.days / 365)


def get_resource_value(dictionary):
    # For value that are not a json format, maybe it is just numeric type object
    if type(dictionary) is not dict:
        return dictionary

    # dictionary = {'resource': resource, 'is_in_component': type(boolean), 'component-code': type(str),
    # 'type': 'laboratory' or 'diagnosis'}
    if dictionary['type'] == 'diagnosis':
        return False if dictionary['resource'] is None else True
    elif dictionary['type'] == 'laboratory':
        # Two situation: one is to get the value of resource, the other is to get the value of resource.component
        if dictionary['is_in_component']:
            for component in dictionary['resource'].component:
                for coding in component.code.coding:
                    if coding.code == dictionary['component-code']:
                        return component.valueQuantity.value
        else:
            try:
                return dictionary['resource'].valueQuantity.value
            except KeyError:
                return dictionary['resource'].valueString
            except Exception as e:
                raise Exception(e)


def get_resource_datetime(dictionary, default_time):
    # dictionary = {'resource': resource, 'is_in_component': type(boolean), 'component-code': type(str),
    # 'type': 'laboratory' or 'diagnosis'} 如果給過來的資料並非是object，就直接回傳該數值的time格式
    if type(dictionary) is not dict:
        return default_time.strftime("%Y-%m-%d")

    if dictionary['type'] == 'diagnosis':
        try:
            return return_date_time_formatter(dictionary['resource'].recordedDate)
        except AttributeError:
            return None
    elif dictionary['type'] == 'laboratory':
        try:
            return return_date_time_formatter(dictionary['resource'].effectiveDateTime)
        except KeyError:
            try:
                return return_date_time_formatter(dictionary['resource'].effectivePeriod.start)
            except KeyError:
                return None


def return_date_time_formatter(self):
    """
        This is a function that returns a standard DateTime format
        While using it, make sure the self parameter is datetime string
    """

    date_regex = '([0-9]([0-9]([0-9][1-9]|[1-9]0)|[1-9]00)|[1-9]000)(-(0[1-9]|1[0-2])(-(0[1-9]|[1-2][0-9]|3[0-1])))'
    date_time_without_sec_regex = '([0-9]([0-9]([0-9][1-9]|[1-9]0)|[1-9]00)|[1-9]000)(-(0[1-9]|1[0-2])(-(0[1-9]|[' \
                                  '1-2][0-9]|3[0-1])(T([01][0-9]|2[0-3]):[0-5][0-9]))) '
    if type(self) == str:
        if re.search(date_time_without_sec_regex, self):
            return self[:16]
        elif re.search(date_regex, self):
            return self[:10] + 'T00:00'

    return None


if __name__ == '__main__':
    resources = CLIENT.resources('Condition')
    search = resources.search(
        # subject=id, code=table['code']).sort('-date').limit(1) doesn't know why it would go wrong in HAPI
        subject="test-03121002", code="I10").sort('recorded-date').limit(1)
    resources = search.fetch()
    print(resources)
