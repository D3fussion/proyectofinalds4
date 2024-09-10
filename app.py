"""
Proyecto final Desarrollo De Sistemas 4
Nombres de los alumnos:
    Quijada Castillo Juan Diego
    Jasso Ibarra Sergio Ivan
    Perez Green Julian Antonio
"""

from flask import Flask, request, render_template
from funciones import crear_diccionario_palabras, crear_diccionario_letras, \
    ordenar_diccionario, find_best_match, modificar_csv, valores_iguales_en_diccionarios, conseguir_nombre_catalogo, \
    crear_diccionario_final

links = [  # Los links solo deben tener categoria
    'https://www.scimagojr.com/journalrank.php?category=1902',
    'https://www.scimagojr.com/journalrank.php?category=1706'
]

diccionario_catalogos = conseguir_nombre_catalogo(links)
diccionario = crear_diccionario_final(diccionario_catalogos)
diccionario_palabras = ordenar_diccionario(crear_diccionario_palabras(diccionario))
diccionario_letras = ordenar_diccionario(crear_diccionario_letras(diccionario_palabras))

app = Flask(__name__)


@app.route('/')
def inicio():
    return render_template('Inicio.html')


@app.route('/Explorar')
def explorar():
    return render_template('Explorar.html', diccionario_letras=diccionario_letras)


@app.route('/ExplorarPalabras')
def explorar_palabras():
    id = request.args.get('param')
    id = [i.capitalize() for i in id.split(" ")]
    lista_diccionarios = []
    for i in id:
        diccionario_enviar = {}
        diccionario_matches = find_best_match(diccionario_palabras, i)
        for j in diccionario_matches.values():
            for k in j:
                diccionario_enviar[k] = diccionario[k]
        lista_diccionarios.append(diccionario_enviar)
    diccionario_enviar = valores_iguales_en_diccionarios(lista_diccionarios)
    id = [f"'{i}'" for i in id]
    return render_template('ExplorarPalabras.html', diccionario_palabras=diccionario_enviar, titulo=', '.join(id))


@app.route('/Creditos')
def creditos():
    return render_template('Creditos.html')


@app.route('/Revista')
def revista():
    global diccionario
    nombre = request.args.get('param')
    nombre = " ".join([i for i in nombre.split("%")])
    for catalogo in diccionario_catalogos.keys():
        modificar_csv(catalogo, nombre)
    diccionario = crear_diccionario_final(diccionario_catalogos)

    return render_template('Revista.html', nombre=nombre, datos=diccionario[nombre])


if __name__ == '__main__':
    app.run(Debug=True)
