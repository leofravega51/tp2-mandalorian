from flask import Flask, render_template, request, redirect, url_for
import redis
import json

app = Flask(__name__, template_folder='templates')

def connect_db():
    """Crear conexion a la base de datos"""
    conexion = redis.StrictRedis(host='db-mandalorian', port=6379, db=0, decode_responses=True)
    if(conexion.ping()):
        print("Conectado al servidor de redis")
    else:
        print("Error...")
    return conexion

mandaloriandb = connect_db()


@app.route('/')
@app.route('/index')
def index():
    """Retorna la pagina index."""
    setDefault()
    return render_template('index.html')



def setDefault():
    """Agregamos un capitulo al contenedor themandalorian"""
    chapters = ['Chapter 1: The Mandalorian', 'Chapter 2: The Child', 'Chapter 3: The Sin', 'Chapter 4: Sanctuary', 'Chapter 5: The Gunslinger', 'Chapter 6: The Prisoner', 'Chapter 7: The Reckoning', 'Chapter 8: Redemption']
    dbchapters = mandaloriandb.lrange('themandalorian', 0, -1)

    for chapter in chapters:
        if(chapter not in(dbchapters)):
            mandaloriandb.lpush("themandalorian", chapter)   #Agregamos el capitulo si no existe, a la lista themandalorian

            mandaloriandb.hset(chapter, "name", chapter)        #Agregamos el nombre del capitulo
            mandaloriandb.hset(chapter, "state", 'Available')    #Añadimos el hash con el nombre del capitulo y el campo estado

            resp = [str(s) for s in chapter.split()]  #Separamos en palabras el capitulo recibido
            index = resp[1][0]                      #Obtenemos la segunda palabra (la cual tiene el numero de capitulo) y guardamos el numero

            mandaloriandb.hset(chapter, "number", index)     #Agregamos el campo numero para identificar que capitulo es

    return "Capitulos agregados con exito!"


def statusChapters():
    """Actualizamos los estados de los capitulos en base a si las claves-estado ya expiraron"""
    chapters = mandaloriandb.lrange("themandalorian", 0,-1, )
    chapters.sort()

    for chapter in chapters:
        if(mandaloriandb.pttl('Reserved'+chapter) == -2 and mandaloriandb.pttl('Rented'+chapter) == -2):
            mandaloriandb.hset(chapter, "state", 'Available')  



@app.route('/themandalorian/chapters')
def chapters():
    """Retornamos una lista con los capitulos de The Mandalorian y su estado"""
    statusChapters()
    chapters = mandaloriandb.lrange("themandalorian", 0,-1, )
    chapters.sort()
    states = []
    numbers = []


    for chapter in chapters:
        response = mandaloriandb.hgetall(chapter)
        estado = response['state']
        numero = response['number']
        states.append(estado)
        numbers.append(numero) 

    return render_template('chapters.html', capitulos=chapters, estados=states)


@app.route('/themandalorian/chapters/payment/<int:id>')
def payment(id):
    """Retornamos un menu para confirmar el pago de alquiler de un capitulo, poniendo en estado reservado al mismo"""
    chapters = mandaloriandb.lrange("themandalorian", 0, -1)
    chapters.sort()
    chapter = chapters[id-1]

    mandaloriandb.hset(chapter, "state", 'Reserved')
    mandaloriandb.setex('Reserved'+chapter, 240, chapter)

    return render_template('payment.html', capitulo=chapter, number=id)

@app.route('/themandalorian/chapters/payment/<int:id>/<int:prec>')
def rented(id, prec):
    """Confirmamos el pago del alquiler, poniendo en estado alquilado al capitulo"""
    chapters = mandaloriandb.lrange("themandalorian", 0, -1)
    chapters.sort()
    chapter = chapters[id-1]

    if(mandaloriandb.pttl('Reserved'+chapter) != -2):
        mandaloriandb.delete('Reserved'+chapter)
        mandaloriandb.hset(chapter, "price", prec)
        mandaloriandb.hset(chapter, "state", 'Rented')
        mandaloriandb.setex('Rented'+chapter, 86400, chapter)
    else:
        mandaloriandb.hset(chapter, "state", 'Available')
    
    return redirect(url_for('chapters'))


if __name__ == '__main__':
    app.run(host='web-flask', port='5000', debug=False)
