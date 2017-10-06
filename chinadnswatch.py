import sys
import time
from datetime import datetime
from string import Template

import dns.resolver
import docker
import logging

FORMAT = '%(asctime)s %(levelname)s: %(message)s'
logging.basicConfig(filename='chinadnswatch.log', level=logging.INFO, format=FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('filelogger')

testHosts = ['www.google.com',
             'www.6park.com',
             'www.youtube.com',
             'www.github.com',
             'www.rarbg.to']

client = docker.from_env()

dnsnetwork = 'dnsnet'


def main(*args):
    while True:
        check_dns_network()
        check_dns_status()
        time.sleep(20)


def check_dns_network():
    dnsnet_list = list(filter(lambda network: network.name == 'dnsnet', client.networks.list()))
    if len(dnsnet_list) == 0:
        client.networks.create(dnsnetwork, driver='bridge')


def check_dns_status():
    try:
        container_list = client.containers.list(all=True)
        illegal_container_list = list(
            filter(lambda container: container.name != 'chinadns' and
                                     list(filter(lambda key: '53' in key,
                                                 container.attrs['NetworkSettings'][
                                                     'Ports'].keys())), container_list))
        for container in illegal_container_list:
            container.remove(force=True)

        chinadns_container_list = list(filter(lambda container: container.name == 'chinadns', container_list))
        dnsforwarder_container_list = list(filter(lambda container: container.name == 'dnsforwarder', container_list))
        if_restart_container = False
        if len(chinadns_container_list) > 0 and len(dnsforwarder_container_list) > 0:
            chinadns_container = chinadns_container_list[0]
            dnsforwarder_container = dnsforwarder_container_list[0]
            if chinadns_container.status == 'running' and dnsforwarder_container.status == 'running':
                for host in testHosts:
                    ifResolve = resolve(host)
                    if not ifResolve:
                        if_restart_container = True
                        break
                    else:
                        logger.info('%s is resolved', host)
                if if_restart_container:
                    s = Template('Restart Chinadns at $time')
                    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    s.substitute(time=time_str)
                    chinadns_container.restart(timeout=30)
                    dnsforwarder_container.restart(timeout=30)
                    logger.warning('Restart Chinadns.')
            else:
                cleanup_containers(chinadns_container_list, dnsforwarder_container_list)
                run_chinadns()
        else:
            run_chinadns()
    except BaseException as error:
        logger.error('An exception occurred: {}'.format(error))


def run_chinadns():
    client.containers.run('chenhw2/hev-dns-forwarder:latest',
                          name='dnsforwarder',
                          command='-p 53 -s 8.8.8.8:53',
                          network=dnsnetwork,
                          detach=True)
    client.containers.run('daocloud.io/hooyao/docker-chinadns:latest', ports={'53/udp': 53},
                          name='chinadns',
                          entrypoint='chinadns',
                          command='-m -c /usr/local/share/chnroute.txt -s 223.5.5.5,dnsforwarder',
                          network=dnsnetwork,
                          detach=True)
    logger.info('Run chinadns.')


def cleanup_containers(chinadns_container_list, dnsforwarder_container_list):
    for container in chinadns_container_list:
        container.remove(force=True)
    for container in dnsforwarder_container_list:
        container.remove(force=True)


def resolve(addr):
    try:
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['127.0.0.1']
        answer = resolver.query(addr)
        return len(answer) > 0
    except:
        return 0


if __name__ == '__main__':
    main(*sys.argv[1:])
