from typing import Dict
from enum import Enum
import pandas as pd
from pathlib import Path

# from sdnist.gui.windows.metadata.labels import *

class FilterSetType(Enum):
    Inclusion_Filter = "Inclusion Filter"
    Exclusion_Filter = "Exclusion Filter"


FSetType = FilterSetType
INDEX = 'Index'

class FilterData:
    def __init__(self,
                 data: pd.DataFrame,
                 path: Path):
        self.data = data
        self.path = path

        self.data = self.data.fillna('nan')
        self.data = self.data.astype(str)
        self.data = self.process_data()

        self.filter_data = {
            FSetType.Inclusion_Filter: dict(),
            FSetType.Exclusion_Filter: dict()
        }

    def process_data(self):
        cols = [INDEX] + self.data.columns.to_list()
        if 'Unnamed: 0' in self.data.columns.to_list():
            self.data[INDEX] = self.data['Unnamed: 0'].values
            self.data = self.data.drop(columns=['Unnamed: 0'])
            cols.remove('Unnamed: 0')
        if INDEX not in self.data.columns.to_list():
            self.data[INDEX] = self.data.index.tolist()
        self.data = self.data[cols]
        return self.data

    def update(self, filter_set_name: str, filter_id: str, filter_data: dict):
        filter_type = self.filter_type(filter_set_name)
        if filter_set_name not in self.filter_data[filter_type]:
            self.filter_data[filter_type][filter_set_name] = dict()
        if len(filter_data):
            self.filter_data[filter_type][filter_set_name][filter_id] = filter_data
        elif filter_id in self.filter_data[filter_type][filter_set_name]:
            self.filter_data[filter_type][filter_set_name].pop(filter_id)

    def remove(self, filter_set_name: str, filter_id: str) -> bool:
        filter_type = self.filter_type(filter_set_name)
        if filter_set_name in self.filter_data[filter_type] and \
                filter_id in self.filter_data[filter_type][filter_set_name]:
            self.filter_data[filter_type][filter_set_name].pop(filter_id)
            return True
        return False

    def get_filters(self, filterset_name: str) -> Dict[str, any]:
        filter_type = self.filter_type(filterset_name)
        if filterset_name in self.filter_data[filter_type]:
            return self.filter_data[filter_type][filterset_name]
        return dict()

    def apply_filters(self) -> pd.DataFrame:

        def select_indexes(filter_type: FSetType):
            res_df = pd.DataFrame([], columns=self.data.columns)
            ft = self.filter_data[filter_type]
            # merge similar features in featureset
            proc_filters = dict()  # processed filters
            for fset_name, filters in ft.items():
                for f_id, f_data in filters.items():
                    f = list(f_data.keys())[0]
                    v = f_data[f]
                    if len(v) == 0:
                        continue
                    if fset_name not in proc_filters:
                        proc_filters[fset_name] = dict()
                    if f not in proc_filters[fset_name]:
                        proc_filters[fset_name][f] = v
                    else:
                        proc_filters[fset_name][f].extend(v)
            filter_applied_count = 0
            # apply filters to the data
            for fset_name, filters in proc_filters.items():
                dc = self.data.copy()
                if self.is_filterset_empty(fset_name):
                    continue
                for f, vals in filters.items():
                    if len(vals):
                        dc = dc[dc[f].isin(vals)]
                        filter_applied_count += 1
                dc = dc[~dc.index.isin(res_df.index)]
                res_df = pd.concat([res_df, dc])

            if filter_applied_count == 0 \
                    and filter_type == FSetType.Inclusion_Filter:
                return self.data.index.tolist()
            if res_df.shape[0] == 0:
                return []
            return res_df.index.tolist()

        inc_indexes = select_indexes(FSetType.Inclusion_Filter)
        exc_indexes = select_indexes(FSetType.Exclusion_Filter)
        f_indexes = list(set(inc_indexes) - set(exc_indexes))
        f_indexes = sorted(f_indexes)
        res_df = self.data[self.data.index.isin(f_indexes)]
        res_df = res_df.sort_index()
        return res_df

    def is_filterset_empty(self, filterset_name: str):
        for fid, fdata in self.get_filters(filterset_name).items():
            for f, vals in fdata.items():
                if len(vals):
                    return False
        return True

    @staticmethod
    def filterset_name(filterset_type: FSetType, filterset_num: int) -> str:
        prefix = 'i' if filterset_type == FSetType.Inclusion_Filter \
            else 'e'
        return f'{prefix}{filterset_num}'

    @staticmethod
    def filter_type(filterset_name: str):
        return FSetType.Inclusion_Filter if filterset_name.startswith("i") \
            else FSetType.Exclusion_Filter
