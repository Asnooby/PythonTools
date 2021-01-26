#coding=utf8

try:
    import py7zr
except Exception as e:
    os.system('pip3 install py7zr')
    import py7zr

import ThreadPool as ThreadPool

def unzip_zip_file_async(zipfilename, unziptodir, end_cb=None):
    if not os.path.exists(unziptodir):
        os.makedirs(unziptodir)
    def unzip(zipfilename, unziptodir, end_cb=None):
        zfobj = zipfile.ZipFile(zipfilename,'r')
        for name in zfobj.namelist():
            name = name.replace('\\','/')
            if name.endswith('/'):
                os.makedirs(os.path.join(unziptodir, name))
            else:
                ext_filename = os.path.join(unziptodir, name)
                ext_dir = os.path.dirname(ext_filename)

                if not os.path.exists(ext_dir):
                    os.makedirs(ext_dir)

                data = zfobj.read(name)
                outfile = open(ext_filename, 'wb')
                outfile.write(data)
                outfile.close()
        if None != end_cb:
            end_cb(zipfilename, zfobj.namelist())

    t = ThreadPool.ThreadPool().Thread(target=unzip,args=(zipfilename, unziptodir, end_cb))
    t.start()
    return t

def unzip_7z_file_async(zipfilename, unziptodir, end_cb=None):
    if not os.path.exists(unziptodir):
        os.makedirs(unziptodir)
    def unzip(zipfilename, unziptodir, end_cb=None):
        try:
            archive = py7zr.SevenZipFile(zipfilename, mode='r')
            names = archive.getnames()
            archive.extractall(path=unziptodir)
            archive.close()
            if None != end_cb:
                end_cb(zipfilename, names)
        except Exception as e:
            print(e)

    t = ThreadPool.ThreadPool().Thread(target=unzip,args=(zipfilename, unziptodir, end_cb))
    t.start()
    return t
