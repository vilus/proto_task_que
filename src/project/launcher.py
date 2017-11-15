#!/bin/env python

import argparse
try:
    import Queue as queue
except ImportError:
    import queue
import os
import requests
import threading
import time
import subprocess
import sys


class Sender(threading.Thread):
    def __init__(self, que, try_count=3, try_timeout=60):
        super(Sender, self).__init__()
        self.que = que
        self.try_count = try_count
        self.try_timeout = try_timeout
        self.daemon = True

    def run(self):
        while True:
            send_info = self.que.get()
            for _ in range(self.try_count):
                try:
                    print('try to send {0}'.format(send_info['data']))
                    requests.post(send_info['url'], json=send_info['data'], timeout=60)
                except requests.Timeout:
                    time.sleep(self.try_timeout)
                else:
                    break
            self.que.task_done()


def detach_proc():
    nullfd = os.open(os.devnull, os.O_RDWR)
    os.dup2(nullfd, sys.stdin.fileno())
    os.dup2(nullfd, sys.stdout.fileno())
    os.dup2(nullfd, sys.stderr.fileno())

    if os.fork():
        sys.exit(0)


def wait_job(job, timeout, waittime):
    time_begin = time.time()
    result = None
    while time.time() - time_begin < timeout:
        result = job()
        if result:
            return result
        time.sleep(waittime)
    return result


if __name__ == '__main__':
    detach_proc()
    # --
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--timeout', default=3600)
    parser.add_argument('-s', '--callback_started_url')
    parser.add_argument('-f', '--callback_finished_url')
    parser.add_argument('-c', '--cmdline')
    args = parser.parse_args()
    # --
    send_que = queue.Queue()
    sender = Sender(send_que)
    sender.start()
    # --
    print('pre run cmd: {0}'.format(args.cmdline.split()))
    p = subprocess.Popen(args.cmdline.split())
    started_info = {
        'url': args.callback_started_url,
        'data': {'pid': p.pid}
    }
    print('pre send started_info')
    send_que.put(started_info)
    wait_job(lambda: p.poll() is not None, timeout=args.timeout, waittime=10)
    finished_info = {
        'url': args.callback_finished_url,
        'data': {'ret_code': p.returncode}
    }
    print('pre send finish info')
    # TODO: exit if not send started info
    # send_que.put(finished_info)
    # --
    # send_que.join()
    subprocess.Popen("curl -d '{\"ret_code\": \"%s\"}' %s -H \"Content-Type: application/json\"" %
                     (p.returncode, args.callback_finished_url), shell=True)
    # --max-time, --connect-timeout
    # NOTE: may be need to demonize
