import itertools
from pathlib import Path
import threading
import time
import py7zr


chars = '!"№;%:?*()'
filename = r'C:\Users\danis\PycharmProjects\p.7z'

event = threading.Event()
i = 0
num = 0
password = ''


def pr(n, running):
    running.set()
    time.sleep(0.1)
    while running.is_set():
        print(f'\r{password}, {i-n}/s', end='')
        n = i
        time.sleep(1)


if Path(filename).exists():
    mask = input('Mask: ')
    min_length = int(input('Min length: ')) - len(mask)
    max_length = int(input('Max length: ')) - len(mask)

    pbar = threading.Thread(target=pr, args=(num, event, ))
    pbar.start()
    start = time.time()
    for length in range(min_length, max_length + 1):
        for s in itertools.product(chars, repeat=length):
            password = mask + ''.join(s)
            i += 1
            try:
                py7zr.SevenZipFile(filename, mode='r', password=password)
                print(f'\rPassword is found for {int(time.time()-start)}s: {password}')
                break
            except Exception:
                pass

    event.clear()
    time.sleep(0.1)

    print('Completed!')
    input('Press enter...')

else:
    print(filename, '!!!')

event.clear()
