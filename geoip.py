import sys
import os
import urllib.request
import zipfile
import pandas as pd

geoip_url = 'http://geolite.maxmind.com/download/geoip/database/GeoLite2-Country-CSV.zip'
dest_file_name = 'GeoLite2-Country-CSV.zip'
data_root = '.'
last_percent_reported = None
target_csv_name = 'GeoLite2-Country-Blocks-IPv4.csv'
geoname_id_cn = '1814991'
def main(*args):
    #download_geoip(dest_file_name)
    unzip()


def download_progress_hook(count, blockSize, totalSize):
    global last_percent_reported
    percent = int(count * blockSize * 100 / totalSize)

    if last_percent_reported != percent:
        if percent % 5 == 0:
            sys.stdout.write("%s%%" % percent)
            sys.stdout.flush()
        else:
            sys.stdout.write(".")
            sys.stdout.flush()
        last_percent_reported = percent


def download_geoip(dest_file_name):
    """Download a file if not present, and make sure it's the right size."""
    #file_name = os.path.basename(geoip_url)
    dest_path = os.path.join(data_root, dest_file_name)
    filename, _ = urllib.request.urlretrieve(geoip_url, dest_path, reporthook=download_progress_hook)
    print('\n')
    print('{} is downloaded.'.format(dest_file_name))

def unzip():
    with zipfile.ZipFile(dest_file_name) as zf:
        file_list = zf.namelist();
        csv_names = list(filter(lambda file_name: target_csv_name in file_name,file_list))
        if len(csv_names) >0 :
            with zf.open(csv_names[0]) as csv_file:
                geo_data = pd.read_csv(csv_file, dtype={'network':object, 'geoname_id':object})
                cn_geo_data = geo_data.loc[geo_data['geoname_id']==geoname_id_cn]
                print(geo_data)
        print(csv_names)

if __name__ == '__main__':
    main(*sys.argv[1:])
