import datetime

from base.searchsets import *  # fhir server search


def model_feature_search_with_patient_id(patient_id, table, model_name):
    default_time = datetime.datetime.now()

    data = dict()
    for key in table:
        data[key] = dict()
        data[key] = get_patient_resources(patient_id, table[key], default_time)

    result_dict = dict()
    for key in data:
        result_dict[key] = dict()
        result_dict[key]['date'] = get_resource_datetime(
            data[key], default_time)
        result_dict[key]['value'] = get_resource_value(data[key])

    return result_dict


if __name__ == '__main__':
    from searchsets import *
