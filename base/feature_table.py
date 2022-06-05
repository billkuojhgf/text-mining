import csv
import re

from base.exceptions import FeatureCodeIsEmpty


class FeatureTable:
    def __init__(self, feature_table_position):
        self.table = self._create_table(feature_table_position)

    @classmethod
    def _create_table(cls, feature_table_position):
        table = {}
        special_field_sets = ('model', "feature", "code", "code_system", "data_alive_time")
        with open(feature_table_position, newline='') as feature_table_file:
            rows = csv.DictReader(feature_table_file)
            for row in rows:
                # 新建以model name 為key 的Dictionary value
                if row['model'] not in table:
                    table[row['model']] = {}
                # 在model name 的Dictionary 裡新建一個以feature name 為key 的Dictionary value
                if row['feature'] not in table[row['model']]:
                    table[row['model']][row['feature']] = {}

                # 處理code 的變數內容，如果有code system 就再新增進去
                code = row['code']
                if row['code_system'] != '':
                    code = "{}|{}".format(row['code_system'], row['code'])

                # 如果code 變數內沒內容
                if code == '' and row["type_of_data"] != "patient":
                    raise FeatureCodeIsEmpty(row['feature'])

                # Feature 有兩種以上的code
                if 'code' in table[row['model']][row['feature']]:
                    table[row['model']][row['feature']]['code'] = table[row['model']][row['feature']]['code'] \
                                                                  + ",{}".format(code)
                else:
                    table[row['model']][row['feature']]['code'] = code

                table[row['model']][row['feature']]['data_alive_time'] = DataAliveTime(
                    row['data_alive_time'])
                # 剩餘的key value就用迴圈建立，因為沒什麼特別的了
                for key, value in row.items():
                    if key not in special_field_sets:
                        table[row['model']][row['feature']][key] = value

            return table

    def get_model_feature_dict(self, model_name):
        if model_name not in self.table:
            raise KeyError("Model is not exist in the feature table.")

        return self.table[model_name]


class DataAliveTime:
    def __init__(self, data_alive_time):
        self._years = 0
        self._months = 0
        self._days = 0
        self._hours = 0
        self._minutes = 0
        self._seconds = 0
        self.__set_data_alive_time(data_alive_time)

    def __set_data_alive_time(self, data_alive_time):
        time_prog = re.compile(
            r"\d{4}-(0\d|1[12])-([12]\d|3[01]|0\d)T(20|21|22|23|[0-1]\d):[0-5]\d:[0-5]\d")
        if time_prog.search(data_alive_time):
            date, time = data_alive_time.split(
                'T')[0], data_alive_time.split('T')[1]
            self._years = int(date.split('-')[0])
            self._months = int(date.split('-')[1])
            self._days = int(date.split('-')[2])
            self._hours = int(time.split(':')[0])
            self._minutes = int(time.split(':')[1])
            self._seconds = int(time.split(':')[2])
        else:
            raise ValueError(
                "Time Format is incorrect, " + data_alive_time)

    def get_years(self):
        return self._years

    def get_months(self):
        return self._months

    def get_days(self):
        return self._days

    def get_hours(self):
        return self._hours

    def get_minutes(self):
        return self._minutes

    def get_seconds(self):
        return self._seconds


if __name__ == '__main__':
    from exceptions import FeatureCodeIsEmpty
    test_table = FeatureTable("../config/features.csv")
    pass
