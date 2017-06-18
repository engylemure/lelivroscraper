# coding: utf-8

import mechanize
from time import sleep
import urllib
from urlparse import urlparse
from os.path import basename, join, exists
from os import makedirs

from multiprocessing import Pool

filetype = r'.mobi'     # Formato que desejar baixar
folder = 'downloaded'   # Local de download do arquivo
PROCESSES_INDEX = 8     # Número de instancias para indexar em paralelo
PROCESSES_DOWN = 4      # Número de instancias para baixar em paralelo
LAST_PAGE_NUMBER = 425  # Quantidade de paginas do site

pool = None


def decoder(m):
    disassembled = urlparse(m)
    filename = basename(disassembled.path)
    url = urllib.unquote(filename).decode('utf8')
    return join(folder, '.'.join([url, filetype.lstrip('.')]))


def validate_url(element):
    # Verifica se é uma URL válida
    return (
        '-em-' in element and
        '-epub' in element and
        '-pdf' in element and
        '-e-' in element and
        '-mobi' in element or
        'Baixar ou Ler Online' in element
    )


def scraper_one_page(page_number):
    # Faz a busca por links dada uma página
    try:
        br = mechanize.Browser()
        print("Indexando pagina " + str(page_number))
        br.open('http://lelivros.me/page/'+str(page_number))

        # iterando pelos links do lelivros.
        # se a URL for válida, adiciona a um set
        return {l.url for l in br.links() if validate_url(str(l))}
    except KeyboardInterrupt:
        pool.terminate()


def iterador():  # cria arquivo.txt com os links de todos os livros ate range
    global pool
    pool = Pool(processes=PROCESSES_INDEX)
    try:
        result = pool.map(scraper_one_page, range(LAST_PAGE_NUMBER))

        # "expande" as listas; Operacao conhecida como "flatten"
        # result = [[a,b,c], [d,e,f], [g,h,i], ...]
        # mylinks = [a,b,c,d,e,f,g,h,i,...]

        mylinks = {item for sublist in result for item in sublist}

        # Grava os resultados num arquivo
        with open('lelivros.txt', 'w') as f:
            for item in mylinks:
                f.write("%s\n" % item)
        return mylinks

    except KeyboardInterrupt:
        pool.close()
        pool.terminate()
        pool.join()
        raise KeyboardInterrupt
    finally:
        pool = None


def download_one_item(url_page):
    # Baixa um único item da página
    try:
        br = mechanize.Browser()
        br.open(url_page)
        for element in br.links():
            if filetype in str(element):
                url = str(element.url)
                nome = decoder(url)
                print("Baixando " + nome)
                urllib.urlretrieve(url, nome)
                sleep(1)
    except KeyboardInterrupt:
        pool.terminate()


def downloader():
    global pool
    pool = Pool(processes=PROCESSES_DOWN)

    try:
        # Cria uma pasta se não existir
        if not exists(folder):
            makedirs(folder)

        # lê o arquivo com os links e lança o pool de download
        with open('lelivros.txt', 'r') as f:
            pool.map(download_one_item, f.readlines())

    except KeyboardInterrupt:
        pool.close()
        pool.terminate()
        pool.join()
        raise KeyboardInterrupt
    finally:
        pool = None


if __name__ == "__main__":
    iterador()
    downloader()

