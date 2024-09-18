
from typing import Dict, List

from torch import Value

from eesrep.components.generic_component import GenericComponent

import numpy as np
import pandas as pd

class TimeSerieManager:

    def __init__(self, 
                    time_serie_data:pd.DataFrame = None, 
                    intensives:Dict[str, bool] = None, 
                    is_future=False):
        """Init 

        Parameters
        ----------
        time_serie_data : pd.DataFrame, optional
            Dataframe containing the time series of the manager, by default None
        intensives : Dict[str, bool], optional
            Required if time_serie_data is provided, tells which column is intensive, by default None
        is_future : bool, optional
            This manager will be used to compute the "future" of past horizons: extrapolates with Nan, by default False

        Raises
        ------
        ValueError
            time_serie_data is provided but not intensives
        ValueError
            time column missing from time_serie_data
        ValueError
            column prensent in time_serie_data but not in intensives
        """
        self.__intensives:Dict[str, bool] = {}
        self.is_future = is_future

        if time_serie_data is not None:
            if intensives is None:
                raise ValueError("'intensives' must be provided if 'time_serie_data' is provided.")
            self.__intensives = intensives
            
            if not "time" in time_serie_data:
                raise ValueError("Provided time series don't have a 'time' column.")
            
            for column in time_serie_data:
                if column is not "time" and (not column in intensives):
                    raise ValueError(f"Column {column} is in time_serie_data but not in intensives.")
                 
            self.__time_series = time_serie_data
            
            time_serie_data.reset_index(inplace=True)
            time_serie_data = time_serie_data.set_index("time")
        else:
            self.__time_series: pd.DataFrame = pd.DataFrame()

    def add_time_serie(self, time_serie_name:str, time_serie:pd.DataFrame, intensive:bool):
        """Adds a time serie dictionnary to the time series dataframe.

        Parameters
        ----------
        time_serie_name : str
            Name of the time serie
        time_serie : pd.DataFrame
            Time serie dataframe
        intensive : bool
            If the added time serie is intensive
        """
        if len(self.__time_series.columns) == 0:
            time_serie.set_index("time", inplace=True, drop=False)
            self.__time_series = time_serie
            self.__time_series = self.__time_series.rename(columns={"value":time_serie_name})
        else:
            time_serie.set_index("time", inplace=True)
            time_serie = (time_serie[["value"]]).rename(columns={"value":time_serie_name})

            self.__time_series = pd.concat([self.__time_series, time_serie], axis=1)

        self.__intensives[time_serie_name] = intensive

    def interpolate_time_series(self):
        """Interpolates the potential NaN values in the time series dataframe. 
        """
        self.__time_series = self.__time_series.interpolate()

    def interpolate(self, times:list, column_name:str, extrapolate_with_nan:bool=False) -> np.ndarray:
        """Get the values at the given times of the requested column in a pandas dataframe.

        Parameters
        ----------
        times : list
            Times at which interpolate
        column_name : str
            Column to interpolate name.
        extrapolate_with_nan : bool
            All time above the time series max time will be interpolated as Nan.

        Returns
        -------
        np.ndarray
            interpolated data
            
        Raises
        ------
        KeyError
            The dataframe doesn't have a 'time' column
        KeyError
            The dataframe doesn't have the requested column
        """
        if not "time" in self.__time_series:
            raise KeyError("The given dataframe has no column 'time'.")
        
        if not column_name in self.__time_series:
            raise KeyError(f"The given dataframe has no column '{column_name}'.")
        
        # print(column_name, "Time to interpolate", times, 
        # "\nserie times", list(self.__time_series["time"]), 
        # "\nserie data", list(self.__time_series[column_name]), 
        # "\nresult", np.interp(times, self.__time_series["time"], self.__time_series[column_name]))

        if extrapolate_with_nan:
            return np.interp(times, self.__time_series["time"], self.__time_series[column_name], right=np.nan)
        else:
            return np.interp(times, self.__time_series["time"], self.__time_series[column_name])

    def __make_ts_integrated_column(self, column_name:str):
        """Adds to the time series dataframe the integral of a column.

        Parameters
        ----------
        column_name : str
            Column name to integrate.

        Raises
        ------
        KeyError
            The self.__time_series dataframe doesn't have the requested column
        """
        if not column_name in self.__time_series:
            raise KeyError(f"The self.__time_series dataframe has no column '{column_name}'.")

        time_serie = pd.DataFrame()
        time_serie.loc[:, "average_"+column_name] = self.__time_series[column_name].rolling(2, min_periods=1).sum()*0.5

        if "diff_time" not in self.__time_series.columns:
            self.__time_series = pd.concat([self.__time_series, pd.DataFrame({"diff_time":self.__time_series["time"].diff()})], axis=1)
            self.__time_series.loc[0, "diff_time"] = 0.
            
        time_serie.loc[:, "local_integral_"+column_name] = \
            self.__time_series[column_name]*self.__time_series["diff_time"]
        
        time_serie.loc[0, "local_integral_"+column_name] = 0.

        time_serie.loc[:, "integrated_"+column_name] = \
            time_serie["local_integral_"+column_name].cumsum()

        del time_serie["local_integral_"+column_name]
        
        self.__time_series = pd.concat([self.__time_series, time_serie], axis=1)

    def get_time_serie_extract(self, current_solve_time_steps:List[float], component:GenericComponent) -> pd.DataFrame:
        """Gets the time series at the current solve time steps of a given component.

        Parameters
        ----------
        current_solve_time_steps : List[float]
            List of time steps at which we want the time series.
        component : GenericComponent
            Component of which we want the time series.

        Returns
        -------
        pd.DataFrame
            Requested time series

        Raises
        ------
        RuntimeError
            Can't extract time series before defining time range.
        KeyError
            Requested a missing column.
        """
        ts_extract = {}

        component_name = component.name

        list_keys = [key for key in component.io_from_parameters() if component.io_from_parameters()[key].continuity] if self.is_future else component.time_series 

        for key in list_keys:
            column_name = component_name+"_"+key

            if not column_name in self.__time_series:
                raise KeyError(f"Column {column_name} is not in the time_serie dataframe.")

            if not "integrated_"+column_name in self.__time_series:
                self.__make_ts_integrated_column(column_name)

            if self.is_future:
                interpolated_values = self.interpolate(current_solve_time_steps, "integrated_"+column_name, extrapolate_with_nan=True)
            else:
                interpolated_values = self.interpolate(current_solve_time_steps, "integrated_"+column_name)

            if self.__intensives[column_name]:
                ts_extract[key] = np.diff(interpolated_values)/np.diff(np.array(current_solve_time_steps))
            else:
                ts_extract[key] = np.diff(interpolated_values)

        return pd.DataFrame(ts_extract)
