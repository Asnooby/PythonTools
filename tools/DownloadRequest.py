#coding=utf8

from tqdm import tqdm
import requests
from urllib.request import urlopen

import ThreadPool as ThreadPool

def getRemoteFileByUrlAsync(url, path, progress_cb=None, end_cb=None):
    file_size = 0
    try:
        file_size = int(urlopen(url).info().get('Content-Length', -1))
    except Exception as e:
        print(e)
        return None

    def getRemoteFunc(url, path, file_size, progress_cb=None, end_cb=None):
        try:
            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))

            pbar = tqdm( total=file_size, initial=0, desc=path, unit='B', unit_scale=True )
            r = requests.get(url, stream=True, verify=False)
            curSize = 0.0
            chunksize = 1024*1024 * 4
            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=chunksize):
                    f.write(chunk)
                    curSize = curSize + len(chunk)

                    if None != progress_cb:
                        progress_cb(curSize, file_size)
                    pbar.update(chunksize)
                f.close()
                pbar.close()
                if None != end_cb:
                    end_cb(path, True)
        except Exception as e:
            print(e)
            if None != end_cb:
                end_cb(path, False)

    t = ThreadPool.ThreadPool().Thread(target=getRemoteFunc,args=(url, path, file_size, progress_cb, end_cb))
    t.start()
    return t
