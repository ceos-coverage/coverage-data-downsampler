import os
import math
from urllib.parse import urlencode
import pandas as pd
import numpy as np
from ulttb import downsample
from bottle import abort

import config

class App():
    def __init__(self, *args, **kwargs):
        # set up output dir
        if not os.path.exists(config.APP_CONFIG["OUTPUT_DIR"]):
            os.makedirs(config.APP_CONFIG["OUTPUT_DIR"])

    def get_data(self, request):
        # check for params
        if (request.query.get("keys") is None or
            request.query.get("project") is None or
            request.query.get("source_id") is None):
            abort(400, "missing query parameter")

        # pull out parameters from the request
        bounds = [float(x) for x in request.query.get("bounds").split(",")] if request.query.get("bounds") else []
        in_keys = request.query.get("keys").split(",") if request.query.get("keys") else config.APP_CONFIG["DEFAULT_KEYS"]
        threshold = int(request.query.get("target")) if request.query.get("target") else config.APP_CONFIG["DEFAULT_TARGET"]
        project = request.query.get("project") if request.query.get("project") else "NONE"
        source_id = request.query.get("source_id") if request.query.get("source_id") else "NONE"
        output_format = request.query.get("format") if request.query.get("format") else config.APP_CONFIG["DEFAULT_FORMAT"]

        # deal with idioms
        keys = self._fix_keys(in_keys)
        
        # download the file if it's not cached
        filename = self._build_filename(project, source_id, keys)
        if not os.path.isfile(filename):
            url = self._build_url(project, source_id, keys)
            self._download_file(url, filename, keys)

        # decimate the data into the desired format
        data = None
        if "csv" in output_format:
            output_format = config.APP_CONFIG["AVAILABLE_FORMATS"]["csv"]
            data = self._decimate_data(filename, bounds, keys, in_keys, threshold, output_format).to_csv(index=False)
        elif "json" in output_format:
            output_format = config.APP_CONFIG["AVAILABLE_FORMATS"]["json"]
            data = self._decimate_data(filename, bounds, keys, in_keys, threshold, output_format)

        if data is None:
            abort(500, "Failed to decimate data")

        # clear cached data
        if not config.APP_CONFIG["CACHE_FILES"] and os.path.isfile(filename):
            os.remove(filename)
        
        return (output_format, data)

    def _fix_keys(self, in_keys):
        keys = ["_".join(key.split(" ")).lower() for key in in_keys]

        if len(keys) < 2:
            keys = [key for key in config.APP_CONFIG["DEFAULT_KEYS"]]
        
        time_found = False
        for i, key in enumerate(keys):
            if "time" in key:
                keys[i] = "measurement_date_time"
                time_found = True
            elif not key in config.APP_CONFIG["NO_MOD_KEYS"] and not key.endswith("_d"):
                keys[i] = key + "_d"

        # ensure there is always time in the data
        if not time_found:
            keys.append("measurement_date_time")

        return keys

    def _build_url(self, project, source_id, keys):
        query = {
            "facet": "on",
            "wt": "csv",
            "rows": "10000000",
            "sort": "%s asc" % (keys[0]),
            "fl": ",".join(keys),
            "q": "datatype:data AND project:%s AND source_id: %s" % (project, source_id)
        }

        return config.APP_CONFIG["SOLR_URL"] + "?" + urlencode(query)

    def _build_filename(self, project, source_id, keys):
        filename = "%s/%s__%s__%s.h5" % (config.APP_CONFIG["OUTPUT_DIR"], project, source_id, "_".join(keys))

        return filename
    
    def _download_file(self, url, filename, keys):
        # download file
        data = pd.read_csv(url)

        # remove empty lines
        data.dropna(inplace=True)

        # edit time entries 
        for key in keys:
            if "time" in key.lower():            
                to_sec = 10**9
                data[key] = (pd.to_datetime(data[key]).astype(np.int64)/to_sec).astype(np.int64)

        # mask out no data values
        masks = [data[key] != -9999 for key in keys]
        datamask = masks[0]
        for mask in masks:
            datamask = datamask & mask
        data = data[datamask]

        # save to hdf file
        data.to_hdf(filename, "table", append=True, data_columns=True)

        return filename
    
    def _decimate_data(self, filename, bounds=[], keys=[], header_keys=[], threshold=config.APP_CONFIG["DEFAULT_TARGET"], output_format=config.APP_CONFIG["DEFAULT_FORMAT"]):
        if len(keys) < 2:
            return None

        # edit time bounds
        if "time" in keys[0].lower():
            bounds = [ x / 1000 if self._magnitude(x) > 9 else x for x in bounds ]

        # read data from hdf file
        if(len(bounds) == 2):
            filter_str = "%s >= %f & %s <= %f" % (keys[0], bounds[0], keys[0], bounds[1])
            data = pd.read_hdf(filename, "table", where = filter_str)
        else:
            data = pd.read_hdf(filename, "table")

        # reset index bounds
        sub_data = data.reset_index(drop=True)

        # rearrange columns
        sub_data = sub_data[keys]

        # sort the data
        sub_data = sub_data.sort_values(by=[keys[0]])
        
        # decimate the data
        dec_data = sub_data.values.tolist()
        if(threshold != config.APP_CONFIG["NO_DECIMATION_TARGET"] and len(dec_data) > threshold):
            dec_data = downsample(dec_data, threshold)

        # format the data
        col_names = list(sub_data)
        if len(header_keys) > 0:
            col_names = [x for x in header_keys] # duplicate the list
            col_names.extend(list(sub_data)[len(header_keys):]) # add any additional columns (hidden time column)
        if output_format == config.APP_CONFIG["AVAILABLE_FORMATS"]["csv"]:
            dec_data = pd.DataFrame(dec_data, columns=col_names)
        elif output_format == config.APP_CONFIG["AVAILABLE_FORMATS"]["json"]:
            dec_data = {
                "data": dec_data,
                "meta": {
                    "sub_size": len(sub_data),
                    "dec_size": len(dec_data),
                    "columns": col_names
                }
            }

        return dec_data
    
    def _magnitude(self, x):
        return int(math.floor(math.log10(x)))
