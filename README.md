### Dynamic Data Downsampling Service

This is a Dockerized Flask service served via an Nginx proxy. It acts as middleware between the client and Solr to fetch data from Solr, cache it, downsample it within the specified bounds, and send the reduced data load to the client. This enables greater interaction for larger datasets.

### Caching

This uses a simple file-based cache of HDF5 files. Cache eviction must be done manually.

### Downsampling

Downsampling is done using the Largest-Triangle-Three-Buckets (LTTB) downsampling algorithm.
This duplicates the code from here: https://github.com/vvangelovski/ulttb.py/tree/master

### API

 * GET `/getData` with the following query parameters
    * `keys`: list of keys to pull from Solr for the specified datasets. Ex. `keys=time,depth`
    * `bounds`: the min,max of the data to downsample within. Ex. `bounds=10,50`
    * `target`: the downsample target (number of points). Ex. `target=20000`
    * `project`: the project field for the solr query. Ex. `project=xyz`
    * `source_id`: the source_id field for the solr query. Ex. `source_id=abc`
    * `format`: the desired return format, either CSV or JSON. Ex. `format=text/csv`

### Deployment

```
docker-compose build
docker-compose up
```