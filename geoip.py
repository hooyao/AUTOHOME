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
import ipaddress

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
exclude_cidrs = ['203.208.32.0/19']


def main(*args):
    # download_geoip(dest_file_name)
    firewall_file_name = retrieve_cn_cidrs()
    upload_and_update(firewall_file_name)


def download_progress_hook(count, block_size, total_size):
    global last_percent_reported
    percent = int(count * block_size * 100 / total_size)

    if last_percent_reported != percent:
        if percent % 5 == 0:
            sys.stdout.write("%s%%" % percent)
            sys.stdout.flush()
        else:
            sys.stdout.write(".")
            sys.stdout.flush()
        last_percent_reported = percent


def download_geoip(save_file_name):
    dest_path = os.path.join(data_root, save_file_name)
    filename, _ = urllib.request.urlretrieve(geoip_url, dest_path, reporthook=download_progress_hook)
    print('\n')
    print('{} is downloaded.'.format(save_file_name))


def unzip_retrieve_cn():
    with zipfile.ZipFile(dest_file_name) as zf:
        file_list = zf.namelist();
        csv_names = list(filter(lambda file_name: target_csv_name in file_name, file_list))
        if len(csv_names) > 0:
            with zf.open(csv_names[0]) as csv_file:
                geo_data = pd.read_csv(csv_file, dtype={'network': object, 'geoname_id': object})
                cn_geo_data = geo_data.loc[geo_data['geoname_id'] == geoname_id_cn]
                return cn_geo_data['network']


def retrieve_cn_cidrs():
    cn_cidrs = unzip_retrieve_cn()

    filtered_cidrs = cn_cidrs[cn_cidrs.apply(lambda x: not test_cidr_equal(x))]
    cidrs = filtered_cidrs.map(lambda x: 'add address={} list=novpn'.format(x).strip())
    values = cidrs.values
    rsc_file_name = datetime.now().strftime("%Y-%m-%d[%H-%M-%S].rsc")
    with_header = np.insert(values, 0, '/ip firewall address-list',axis=0)
    np.savetxt(rsc_file_name, with_header, fmt='%s', newline='\n')
    return rsc_file_name


def test_cidr_equal(cidr_addr):
    n1 = ipaddress.ip_network(cidr_addr)
    for exc in exclude_cidrs:
        exci_n = ipaddress.ip_network(exc)
        if n1.overlaps(exci_n):
            print('{} is overlapped with {} to exclude.'.format(cidr_addr, exc))
            return n1 == exci_n
    return False


def upload_and_update(firewall_file_name):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(mikrotik_host, username=mikrotik_user, password=mikrotik_pass,
                allow_agent=False, look_for_keys=False)
    with ssh.open_sftp() as sftp:
        sftp.put(firewall_file_name, '/{}'.format(firewall_file_name))
    ssh.close()

    api = ros.connect(host=mikrotik_host, username=mikrotik_user, password=mikrotik_pass)
    api(cmd='/ip firewall address-list remove [/ip firewall address-list find list="novpn"]')
    api(cmd='import file-name={}'.format(firewall_file_name))


if __name__ == '__main__':
    main(*sys.argv[1:])
