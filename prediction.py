import pandas as pd
import pickle
import numpy as np
from sklearn.neural_network import MLPRegressor
import json
from config import DATA_PATH, MODEL_FILE, SAFE_FILE_, VAR_FILE, DATA_FILE, TARGET_COLUMN, \
    PREDICTOR_EDGE_MIN, PREDICTOR_EDGE_MAX


class Predictor:
    model = None
    encoder = {}
    max_encoder = {}
    data_format = {}
    col_order = []
    INT_CNST, STR_CNST = 0, 1

    def __init__(self, min_edge=PREDICTOR_EDGE_MIN, max_edge=PREDICTOR_EDGE_MAX, model_file=None, var_file=None):
        if model_file is not None:
            self.model = pickle.load(open(model_file, 'rb'))
            with open(var_file) as f:
                params = json.load(f)
                print(params)
                self.encoder = params['encoder']
                self.max_encoder = params['max_encoder']
                self.col_order = params['col_order']
                self.data_format = params['data_format']
        else:
            self.model = MLPRegressor()
            x, y = self.preprocess(data=self.load_data(min_edge=min_edge, max_edge=max_edge), update=True)
            if x is None or y is None:
                print('Error: Cant create a model')
                return
            self.model.fit(x, y)
            pickle.dump(self.model, open(DATA_PATH + MODEL_FILE, 'wb'))
            params = {'encoder': self.encoder,
                      'max_encoder': self.max_encoder,
                      'col_order': self.col_order,
                      'data_format': self.data_format}
            with open(DATA_PATH + VAR_FILE, 'w') as f:
                json.dump(params, f)

    @staticmethod
    def load_data(min_edge, max_edge, file=DATA_FILE):
        try:
            data = pd.read_csv(file, nrows=max_edge)
            return data.iloc[min_edge:]
        except Exception as e:
            print('Error during reading a file: ', e)
            return None

    def preprocess(self, data, update=False):
        y = []
        if update:
            self.col_order = data.columns.tolist()
            if TARGET_COLUMN in self.col_order:
                self.col_order.remove(TARGET_COLUMN)
            for col in self.col_order:
                try:
                    data[col] = pd.to_numeric(data[col])
                    data = data.replace(np.nan, 0)
                    self.data_format[col] = self.INT_CNST
                except Exception:
                    self.data_format[col] = self.STR_CNST

        else:
            if TARGET_COLUMN in data.columns:  # Test mode. Should not be called in real case
                y = data[TARGET_COLUMN]
                data = data.drop(columns=TARGET_COLUMN)

            # check the existence & need & order of columns
            data = data.reindex(columns=self.col_order)

        if TARGET_COLUMN in data.columns:
            y = data[TARGET_COLUMN]
            data = data.drop(columns=TARGET_COLUMN)

        data = data.apply(lambda x: x.fillna(0 if self.data_format[x.name] == self.INT_CNST else ''))
        try:
            data['timestamp'] = data['timestamp'].apply(
                lambda x: sum(int(i) * j for i, j in zip(x.split('-'), [10000, 100, 1]))
            )
        except Exception as e:
            data['timestamp'] = 20100000  # 2010 - YYYY, 00 - MM, 00 - DD
        finally:
            self.data_format['timestamp'] = self.INT_CNST

        # encoding
        for col in data.columns:
            if self.data_format[col] == self.INT_CNST:
                try:
                    data[col] = pd.to_numeric(data[col])
                    data = data.replace(np.nan, 0)
                except Exception as e:
                    print(col, e)
                    data[col] = 0
                continue
            if col not in self.encoder:
                self.encoder[col] = {}
                self.max_encoder[col] = 0
            cur_data = []

            for i in data[col]:
                if i not in self.encoder[col]:
                    self.encoder[col][i] = self.max_encoder[col]
                    self.max_encoder[col] += 1
                cur_data.append(self.encoder[col][i])
            data[col] = np.array(cur_data)
        return data, y

    def predict_x(self, params):
        y = {}
        for col in self.col_order:
            if params.get(col) is not None:
                y[col] = pd.to_numeric(params[col]) if self.data_format[col] == self.INT_CNST else params[col]
            else:
                y[col] = 0 if self.data_format[col] == self.INT_CNST else ''
        data = pd.DataFrame(columns=self.col_order)
        data.loc[0] = pd.Series(y)
        xnew = self.preprocess(data)[0]
        return abs(self.model.predict(xnew)[0])

    def predict_xs(self, min_edge, max_edge, file=DATA_FILE, test=False):
        data = self.load_data(min_edge=min_edge, max_edge=max_edge, file=file)
        xnew, ynew = self.preprocess(data)

        y_predicted = self.model.predict(xnew)
        y_predicted = [abs(i) for i in y_predicted]

        data[TARGET_COLUMN] = y_predicted
        data.to_csv(DATA_PATH + SAFE_FILE_, index=False, na_rep='NA')

        if test:
            print('original: ', ynew.tolist()[:10])
            print('predicted: ', y_predicted[:10])
            print('score: ', self.model.score(xnew, ynew))
            return self.model.score(xnew, ynew)
        return DATA_PATH + SAFE_FILE_

    def safe(self, file):
        pickle.dump(self.model, open(file, 'wb'))


predictor = Predictor(model_file=DATA_PATH + MODEL_FILE, var_file=DATA_PATH + VAR_FILE)
