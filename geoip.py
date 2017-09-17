import datetime
import os
import sys
import urllib.request
import zipfile
from datetime import datetime

import numpy as np
import pandas as pd
import paramiko
import librouteros as ros

geoip_url = 'http://geolite.maxmind.com/download/geoip/database/GeoLite2-Country-CSV.zip'
dest_file_name = 'GeoLite2-Country-CSV.zip'
data_root = '.'
last_percent_reported = None
target_csv_name = 'GeoLite2-Country-Blocks-IPv4.csv'
geoname_id_cn = '1814991'
mikrotik_firewall_entry = 'add address="$1" list=novpn'
mikrotik_host = '192.168.1.1'
mikrotik_user = 'admin'
mikrotik_pass = 're1WnEZ9prY5'


def main(*args):
    download_geoip(dest_file_name)
    firewall_file_name =  retrive_cn_cidrs()
    upload_and_update(firewall_file_name)



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
    # file_name = os.path.basename(geoip_url)
    dest_path = os.path.join(data_root, dest_file_name)
    filename, _ = urllib.request.urlretrieve(geoip_url, dest_path, reporthook=download_progress_hook)
    print('\n')
    print('{} is downloaded.'.format(dest_file_name))


def unzip_retrieve_cn():
    with zipfile.ZipFile(dest_file_name) as zf:
        file_list = zf.namelist();
        csv_names = list(filter(lambda file_name: target_csv_name in file_name, file_list))
        if len(csv_names) > 0:
            with zf.open(csv_names[0]) as csv_file:
                geo_data = pd.read_csv(csv_file, dtype={'network': object, 'geoname_id': object})
                cn_geo_data = geo_data.loc[geo_data['geoname_id'] == geoname_id_cn]
                return cn_geo_data['network']


def retrive_cn_cidrs():
    cn_ips = unzip_retrieve_cn()
    cidrs = cn_ips.map(lambda x: 'add address="{}" list=novpn'.format(x).strip())
    values = cidrs.values
    rsc_file_name = datetime.now().strftime("%Y-%m-%d[%H:%M:%S].rsc")
    np.savetxt(rsc_file_name, values, fmt='%s', newline='\n')
    return rsc_file_name


def upload_and_update(firewall_file_name):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=mikrotik_host, username=mikrotik_user, password=mikrotik_user)
    with ssh.open_sftp() as sftp:
        sftp.put(firewall_file_name, '/')
    ssh.close()

    api = ros.connect(host=mikrotik_host, username=mikrotik_user, password=mikrotik_user)
    api(cmd='/ip firewall address-list remove [/ip firewall address-list find list="novpn"]')
    api(cmd='import file-name={}'.format(firewall_file_name))

if __name__ == '__main__':
    main(*sys.argv[1:])
