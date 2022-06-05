import importlib
import configparser

from flask import Flask
from flask import jsonify
from flask import request
from flask import abort
from flask_cors import CORS
from base import feature_table
from base import patient_data_search as ds
from models import *

app = Flask(__name__)
CORS(app)

# Map the csv into dictionary
config = configparser.ConfigParser()
config.read("./config.ini")
table = feature_table.FeatureTable(config['table_path']['FEATURE_TABLE'])


def import_model():
    # get a handle on the module
    mdl = importlib.import_module('models')

    # is there an __all__?  if so respect it
    if "__all__" in mdl.__dict__:
        names = mdl.__dict__["__all__"]
    else:
        # otherwise we import all names that don't begin with _
        names = [x for x in mdl.__dict__ if not x.startswith("_")]

    # now drag them in
    globals().update({k: getattr(mdl, k) for k in names})


@app.route('/', methods=["GET"])
def index():
    return "<h1>Hello World!</h1>For more information about Quick COVID Severity Index(QCSI), please lookup our \
     document: <a href=\"https://fhirproject.docs.apiary.io/#\">https://fhirproject.docs.apiary.io/#</a>"


@app.route('/<api>', methods=['GET'])
def api_with_id(api):
    """
    Description:
        This api gets the request with patient's id and model, then the server would return the model's result
        and patient's data.

    :param api:<base>/<model name>?id=<patient's id>&hour_alive_time
    :return: json object
        {
            "predict_value": <int> or <double>
            "<feature's name>": {
                "date": YYYY-MM-DDThh:mm:ss,
                "value": <boolean> or <int> or <double> or <string> // depends on the data
            }
        }
    """
    # TODO: the hour_alive_time request value
    if request.values.get('id') is None:
        abort(400, description="Please fill in patient's ID.")
    patient_id = request.values.get('id')
    hour_alive_time = None

    if request.values.get('data_alive_time') is not None:
        hour_alive_time = request.values.get('hour_alive_time')

    patient_data_dictionary = ds.model_feature_search_with_patient_id(
        patient_id, table.get_model_feature_dict(api), None, hour_alive_time)
    print(patient_data_dictionary)
    patient_data_dictionary["predict_value"] = return_model_result(patient_data_dictionary, api)
    return jsonify(patient_data_dictionary)


def verify_data(patient_data_dict, api):
    # MUST HAVE: 1. Keys with each feature. 2. Value with Dict type and has Key with "value".
    try:
        validation_table = table.get_model_feature_dict(api)
    except KeyError:
        raise KeyError("{} Model is not in the table".format(api))

    for key in validation_table.keys():
        if key not in patient_data_dict.keys():
            raise KeyError("{} was not given".format(key))

        if "value" not in patient_data_dict[key].keys():
            raise KeyError("{}'s value has no 'value' key.".format(key))


@app.route('/<api>/change', methods=['POST'])
def api_with_post(api):
    """
    Description:
        This api gets the request with patient's id and model, then the server would return the model's result
        and patient's data.

    :param api:<base>/<model name>?id=<patient's id>&hour_alive_format
    :return: json object
        {
            "predict_value": <int> or <double>
            "<feature's name>": {
                "date": YYYY-MM-DDThh:mm:ss,
                "value": <boolean> or <int> or <double> or <string> // depends on the data
            }
        }
    """
    patient_data_dict = request.get_json()
    # TODO: A function to verify data whether is in right format.
    # MUST HAVE: 1. Keys with each features. 2. Value with Dict type and has Key with "value"
    verify_data(patient_data_dict, api)
    print(patient_data_dict)
    patient_data_dict["predict_value"] = return_model_result(patient_data_dict, api)
    return jsonify(patient_data_dict)


def return_model_result(patient_data_dict, api):
    """
        Function return_model_result會對 model執行 predict的動作，回傳 model的結果
    """
    model_results = globals()[api].predict(patient_data_dict)
    # try:
    #     model_results = globals()[api].predict(patient_data_dict)
    # except KeyError:
    #     abort(400, description="Model was not found in system.")
    # except Exception as e:
    #     abort(500, description=e)

    return model_results


import_model()

if __name__ == '__main__':
    app.debug = True
    app.run()
