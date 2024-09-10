"""
Proyecto final Desarrollo De Sistemas 4
Nombres de los alumnos:
    Quijada Castillo Juan Diego
    Jasso Ibarra Sergio Ivan
    Perez Green Julian Antonio
"""

import os
import re
import csv
import string
import requests
from bs4 import BeautifulSoup
from difflib import get_close_matches


def crear_scrapper(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup


def web_crawling(scrapper, url, nombre_csv):
    pagina = scrapper.find_all(class_='pagination_buttons')[0].find_all('a')[-1].get('href').split('?')[1].split('&')
    numero_paginas = int((int(pagina[2].split('=')[1]) / 50) + 1)
    for i in range(1, numero_paginas + 1):
        url = f'{url}&page={i}'
        scrapper = crear_scrapper(url)
        scrapear_datos_general(scrapper, nombre_csv)


def scrapear_datos_general(scrapper, nombre_csv):
    lista_revistas = []
    for i in scrapper.find_all('tbody')[0].find_all('tr'):
        lista_texto = ([j for j in i.find_all('td')])

        # Excepciones para los valores que no tienen datos
        if len(lista_texto[3].text.split(" ")) == 1:
            q = "N/A"
        else:
            q = lista_texto[3].text.split(" ")[1]
        if lista_texto[3].text.split(" ")[0] == "":
            sjr = "N/A"
        else:
            sjr = lista_texto[3].text.split(" ")[0]

        lista_revistas.append({lista_texto[1].text: {
            "type": lista_texto[2].text,
            "sjr": sjr,
            "q": q,
            "h_index": lista_texto[4].text,
            "total_docs": lista_texto[5].text,
            "total_docs_3_years": lista_texto[6].text,
            "total_refs": lista_texto[7].text,
            "total_cites_3_years": lista_texto[8].text,
            "citable_docs_3_years": lista_texto[9].text,
            "cites_doc_2_years": lista_texto[10].text,
            "ref_doc": lista_texto[11].text,
            "country": lista_texto[13].find("img").get('title'),
            "url": f"https://www.scimagojr.com/{lista_texto[1].find_all('a')[0].get('href')}"
        }})
    crear_csv_general(lista_revistas, nombre_csv)


def scrapear_datos_revista(url):
    scrapper_revista = crear_scrapper(url)
    divs = scrapper_revista.find(class_='journalgrid').find_all('div')
    subject = ""
    lista_subject = divs[1].find_all('a')
    for i in range(len(lista_subject)):
        if i == len(lista_subject) - 1:
            subject += lista_subject[i].text
        else:
            subject += lista_subject[i].text + "<br>-"
    return [
        subject,  # Subject
        divs[2].find('a').text,  # Publisher
        divs[5].find('p').text,  # ISSN
        divs[6].find('p').text,  # Coverage
        re.sub(r'\s+', ' ', ''.join(divs[9].find_all(string=True, recursive=False)).strip()),  # Scope
        f"{scrapper_revista.find(id='embed_code').get('value')}"  # Graph
    ]


def crear_csv_general(lista_revistas, nombre_archivo):
    # En verdad no lo crea la mayoria del tiempo, pero me gusto el nombre asi
    # Verifica si el archivo ya existe
    if os.path.exists(nombre_archivo):
        modo_apertura = 'a'  # Si ya existe, se abre en modo append
    else:
        modo_apertura = 'w'  # Si no existe, se abre en modo write

    with open(nombre_archivo, modo_apertura, encoding="utf-8") as archivo:
        if modo_apertura == 'w':
            archivo.write(
                'Nombre;Tipo;SJR;Q;H_index;Total_docs;Total_docs_3_years;Total_refs;Total_cites_3_years;'
                'Citable_docs_3_years;Cites_doc_2_years;Ref_doc;Country;Url;Catalogue;Subject;Publisher;ISSN;Coverage;Scope;Graph\n'
            )

        # Escribe los contenidos de las revistas
        for revista in lista_revistas:
            for nombre, datos in revista.items():
                archivo.write(
                    f"{nombre.strip()};{datos['type']};{datos['sjr']};{datos['q']};{datos['h_index']};{datos['total_docs']};" +
                    f"{datos['total_docs_3_years']};{datos['total_refs']};{datos['total_cites_3_years']};" +
                    f"{datos['citable_docs_3_years']};{datos['cites_doc_2_years']};{datos['ref_doc']};" +
                    f"{datos['country']};{datos['url']};{nombre_archivo[:-4]}\n"
                    # {datos['subject']};{datos['publisher']};{datos['ISSN']};{datos['coverage']};" +
                    #                     f'{datos['scope'].replace(";", ".")};"{datos["graph"]}"\n
                )


def modificar_csv(archivo_csv, palabra_buscar):
    # Revisa si la palabra a buscar esta en el archivo, si esta, revisa si tiene los datos de la revista,
    # si no los tiene, los agrega
    lineas_modificadas = []

    with open(archivo_csv, 'r', newline='') as archivo:
        lector_csv = csv.reader(archivo, delimiter=';')
        romper = False
        for fila in lector_csv:
            if fila and fila[0] == palabra_buscar:
                if len(fila) == 15:
                    datos_a_agregar = scrapear_datos_revista(fila[13])
                    fila.extend(datos_a_agregar)
                else:
                    romper = True
                    break
            lineas_modificadas.append(fila)

    if romper:
        return

    with open(archivo_csv, 'w', newline='') as archivo:
        escritor_csv = csv.writer(archivo, delimiter=';')
        escritor_csv.writerows(lineas_modificadas)


def revistas_por_anio(nombre_csv, url):
    for anio in range(2023, 2024):  # Osea que solo va a buscar en 2023
        url = f'{url}&year={anio}'
        scrapper = crear_scrapper(url)
        web_crawling(scrapper, url, nombre_csv)


def comprobar_existencia_csv(archivo_csv, url):
    if os.path.exists(archivo_csv):
        datos = {}
        with open(archivo_csv, newline='') as archivo_csv:
            lector_csv = csv.DictReader(archivo_csv, delimiter=";", quotechar='"')
            for fila in lector_csv:
                datos[dict(fila)['Nombre']] = dict(fila)
        return datos
    else:
        revistas_por_anio(archivo_csv, url)
        return comprobar_existencia_csv(archivo_csv, url)


def crear_diccionario_palabras(diccionario: dict):
    # Crea un diccionario con cada palabra de cada nombre de las revistas,
    # donde la key es la palabra y el value es los nombres de las revistas que contienen esa palabra
    diccionario_palabras = {}
    for nombre, datos in diccionario.items():
        for palabra in nombre.split():
            if palabra.capitalize() not in diccionario_palabras:
                diccionario_palabras[palabra.capitalize()] = [nombre]
            else:
                diccionario_palabras[palabra.capitalize()].append(nombre)
    return diccionario_palabras


def crear_diccionario_letras(diccionario: dict):
    # Crea un diccionario con cada letra de cada nombre de las revistas,
    # donde la key es la letra con la que inicia y el value es los nombres de las revistas que contienen esa letra
    diccionario_letras = {}
    for nombre, datos in diccionario.items():
        for letra in nombre[0].upper():
            if letra not in diccionario_letras:
                diccionario_letras[letra] = [nombre.capitalize()]
            else:
                diccionario_letras[letra].append(nombre.capitalize())
    return diccionario_letras


def ordenar_diccionario(diccionario: dict):
    def custom_sort(key):
        letras = string.ascii_letters
        return (key[0] not in letras, key[0])
    llaves_ordenadas = sorted(diccionario.keys(), key=custom_sort)
    diccionario_ordenado = {key: diccionario[key] for key in llaves_ordenadas}
    return diccionario_ordenado


def find_best_match(diccionario, palabra):
    datos_exactos = {key: diccionario[key] for key in diccionario.keys() if key == palabra}

    if datos_exactos:
        return datos_exactos

    else:
        palabras_similares = get_close_matches(palabra, diccionario.keys())
        datos_similares = {key: diccionario[key] for key in palabras_similares}
        return datos_similares


def valores_iguales_en_diccionarios(lista_diccionarios):
    if not lista_diccionarios:
        return {}
    claves_comunes = set.intersection(*[set(diccionario.keys()) for diccionario in lista_diccionarios])
    valores_comunes = {}
    for clave in claves_comunes:
        valores = [diccionario[clave] for diccionario in lista_diccionarios]
        if all(valor == valores[0] for valor in valores):
            valores_comunes[clave] = valores[0]
    return valores_comunes


def combinar_diccionarios(dic1, dic2):
    for key, value in dic2.items():
        if key in dic1:
            print("Esta se repite entre las dos >", key, value['Catalogue'])
            dic1[key] = value
            dic1[key]['Catalogue'] = dic1[key]['Catalogue'] + ', ' + value['Catalogue']
        else:
            dic1[key] = value
    return dic1


def conseguir_nombre_catalogo(urls: list[str]):
    lista_catalogos = {}
    for url in urls:
        scrapper = crear_scrapper(url)
        scrap = scrapper.find(id='rankingcontrols').find_all(class_="dropdown")[1].find_all('a')
        for i in scrap:
            if i.get('href') == url.split('.com/')[1]:
                lista_catalogos = lista_catalogos | {f'{i.text}.csv': url}
                break
    return lista_catalogos


def crear_diccionario_final(diccionario_catalogos: dict):
    diccionario_final = {}
    for catalogo, url in diccionario_catalogos.items():
        diccionario_final = combinar_diccionarios(diccionario_final, comprobar_existencia_csv(catalogo, url))
    return ordenar_diccionario(diccionario_final)


if __name__ == '__main__':
    links = [
        'https://www.scimagojr.com/journalrank.php?category=1902',
        'https://www.scimagojr.com/journalrank.php?category=1706'
    ]
    diccionario_catalogos = conseguir_nombre_catalogo(links)

    diccionario_p = crear_diccionario_final(diccionario_catalogos)

    for i in diccionario_p.values():
        print(i)

    print("Modificando...")

    for i in diccionario_catalogos.keys():
        modificar_csv(i, 'AI Open')

    diccionario_p = crear_diccionario_final(diccionario_catalogos)

    for i in diccionario_p.values():
        print(i)
