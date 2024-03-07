Давайте создадим веб -сервер.Часть 2.
============================================================================================================================


Помните, что в [Часть 1](6_Web_server/README1.md). Я задал вам вопрос: «Как  запустить приложение Django, приложение Flask  под вашим Веб -сервером, не внося ни одного изменения на сервер для размещения всех этих различных веб -структур? » Читайте дальше, чтобы узнать ответ.

Обычно, выбор фреймворка Python (например Django Flask  и тп), накладывает ограничения в выборе веб -сервера и наоборот. Т.е фреймворк и сервер должны быть разработаны для совместной работы, как на картинке:

![Server Framework Fit](https://ruslanspivak.com/lsbaws-part2/lsbaws_part2_before_wsgi.png)

Но вы могли столкнуться (и, возможно, так и есть) со следующей проблемой при попытке объединить сервер и фреймворк, которые не была разработана для работы вместе:

![Server Framework Clash](https://ruslanspivak.com/lsbaws-part2/lsbaws_part2_after_wsgi.png)

В основном вам приходилось использовать то, что работало вместе, а не то, что вы, возможно, хотели использовать.

Итак, как вы теперь убедитесь, вы можете запустить свой веб -сервер с несколькими веб -фреймворками, не внося изменения кода ни на веб -сервер, ни на веб -фреймворки?И ответ на эту проблему в **Python Web Server Gateway Interface** (or [WSGI](https://www.python.org/dev/peps/pep-0333/ "WSGI") из короткого, выражения _“wizgy”_ - изумительный) .

![WSGI Interface](https://ruslanspivak.com/lsbaws-part2/lsbaws_part2_wsgi_idea.png)

[WSGI](https://www.python.org/dev/peps/pep-0333/ "WSGI") Позволял разработчикам разделить выбор веб -фреймворка от выбора веб -сервера.Теперь вы можете смешать и смиксовать веб -серверы и веб -фреймворки и выбрать решение, которое соответствует вашим потребностям.Вы можете запустить [Django](https://www.djangoproject.com/ "Django"), [Flask](http://flask.pocoo.org/ "Flask"), or [Pyramid](http://trypyramid.com/ "Pyramid"), Например, с [Gunicorn](http://gunicorn.org/ "Gunicorn") or [Nginx/uWSGI](http://uwsgi-docs.readthedocs.org "uWSGI") or [Waitress](http://waitress.readthedocs.org "Waitress"). Реальное сочетание и миксование благодаря поддержке WSGI как на серверах, так и на платформах.:

![Mix & Match](https://ruslanspivak.com/lsbaws-part2/lsbaws_part2_wsgi_interop.png)

Так, [WSGI](https://www.python.org/dev/peps/pep-0333/ "WSGI") Ответ на вопрос, который я задал вам в [Part 1](http://ruslanspivak.com/lsbaws-part1/ "Part 1") и повторился в начале этой статьи. Ваш веб -сервер должен реализовать часть сервера интерфейса WSGI и все современные веб -фреймворки Python, которые уже реализуют фреймворскую сторону интерфейса WSGI, которая позволяет использовать их с вашим веб -сервером, не изменяя код вашего сервера для размещения определенной веб -структуры.

Теперь вы знаете, что поддержка WSGI с помощью веб -серверов и веб -фреймворков позволяет вам выбрать спаривание, которое вам подходит, но она также полезна для разработчиков сервера и фреймворка, потому что они могут сосредоточиться на своей предпочтительной области специализации, а не наступать на пятки друг друга.У других языков также есть похожие интерфейсы: например, на Java [Servlet API](https://en.wikipedia.org/wiki/Java_servlet "Servlet API") and Ruby has [Rack](https://en.wikipedia.org/wiki/Rack_%28web_server_interface%29 "Rack").

Это все хорошо, но держу пари, вы говорите: «Покажи мне код!»Хорошо, посмотрите на эту довольно минималистичную реализацию сервера WSGI:
```py
# Tested with Python 3.7+ (Mac OS X)
import io
import socket
import sys


class WSGIServer(object):

    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 1

    def __init__(self, server_address):
        # Create a listening socket
        self.listen_socket = listen_socket = socket.socket(
            self.address_family,
            self.socket_type
        )
        # Allow to reuse the same address
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind
        listen_socket.bind(server_address)
        # Activate
        listen_socket.listen(self.request_queue_size)
        # Get server host name and port
        host, port = self.listen_socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port
        # Return headers set by Web framework/Web application
        self.headers_set = []

    def set_app(self, application):
        self.application = application

    def serve_forever(self):
        listen_socket = self.listen_socket
        while True:
            # New client connection
            self.client_connection, client_address = listen_socket.accept()
            # Handle one request and close the client connection. Then
            # loop over to wait for another client connection
            self.handle_one_request()

    def handle_one_request(self):
        request_data = self.client_connection.recv(1024)
        self.request_data = request_data = request_data.decode('utf-8')
        # Print formatted request data a la 'curl -v'
        print(''.join(
            f'< {line}\n' for line in request_data.splitlines()
        ))

        self.parse_request(request_data)

        # Construct environment dictionary using request data
        env = self.get_environ()

        # It's time to call our application callable and get
        # back a result that will become HTTP response body
        result = self.application(env, self.start_response)

        # Construct a response and send it back to the client
        self.finish_response(result)

    def parse_request(self, text):
        request_line = text.splitlines()[0]
        request_line = request_line.rstrip('\r\n')
        # Break down the request line into components
        (self.request_method,  # GET
         self.path,            # /hello
         self.request_version  # HTTP/1.1
         ) = request_line.split()

    def get_environ(self):
        env = {}
        # The following code snippet does not follow PEP8 conventions
        # but it's formatted the way it is for demonstration purposes
        # to emphasize the required variables and their values
        #
        # Required WSGI variables
        env['wsgi.version']      = (1, 0)
        env['wsgi.url_scheme']   = 'http'
        env['wsgi.input']        = io.StringIO(self.request_data)
        env['wsgi.errors']       = sys.stderr
        env['wsgi.multithread']  = False
        env['wsgi.multiprocess'] = False
        env['wsgi.run_once']     = False
        # Required CGI variables
        env['REQUEST_METHOD']    = self.request_method    # GET
        env['PATH_INFO']         = self.path              # /hello
        env['SERVER_NAME']       = self.server_name       # localhost
        env['SERVER_PORT']       = str(self.server_port)  # 8888
        return env

    def start_response(self, status, response_headers, exc_info=None):
        # Add necessary server headers
        server_headers = [
            ('Date', 'Mon, 15 Jul 2019 5:54:48 GMT'),
            ('Server', 'WSGIServer 0.2'),
        ]
        self.headers_set = [status, response_headers + server_headers]
        # To adhere to WSGI specification the start_response must return
        # a 'write' callable. We simplicity's sake we'll ignore that detail
        # for now.
        # return self.finish_response

    def finish_response(self, result):
        try:
            status, response_headers = self.headers_set
            response = f'HTTP/1.1 {status}\r\n'
            for header in response_headers:
                response += '{0}: {1}\r\n'.format(*header)
            response += '\r\n'
            for data in result:
                response += data.decode('utf-8')
            # Print formatted response data a la 'curl -v'
            print(''.join(
                f'> {line}\n' for line in response.splitlines()
            ))
            response_bytes = response.encode()
            self.client_connection.sendall(response_bytes)
        finally:
            self.client_connection.close()


SERVER_ADDRESS = (HOST, PORT) = '', 8888


def make_server(server_address, application):
    server = WSGIServer(server_address)
    server.set_app(application)
    return server


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('Provide a WSGI application object as module:callable')
    app_path = sys.argv[1]
    module, application = app_path.split(':')
    module = __import__(module)
    application = getattr(module, application)
    httpd = make_server(SERVER_ADDRESS, application)
    print(f'WSGIServer: Serving HTTP on port {PORT} ...\n')
    httpd.serve_forever()
```

Это определенно больше, чем код сервера в [Часть 1] , но также достаточно мал (чуть менее 150 строк), чтобы вы могли понять, не вдаваясь в подробности. Приведенный выше сервер  делает даже больше - он может запустить ваше основное веб -приложение, написанное с вашей любимой Pyramid, Flask, Django, or some other Python WSGI framework.

Не верите мне?Попробуйте и убедитесь сами.Сохраните вышеуказанный код как _webserver2.py_ или скачать его напрямую с [GitHub](https://github.com/rspivak/lsbaws/blob/master/part2/webserver2.py). Если вы попытаетесь запустить его без каких -либо параметров, он будет жаловаться и нужно вот так написать.
```
$ python webserver2.py
Provide a WSGI application object as module:callable
```

Он действительно хочет обслуживать ваше веб -приложение, и именно здесь начинается веселье.Чтобы запустить сервер, единственное, что вам нужно установить, это Python (точнее Python 3.7+).Но для запуска приложений, написанных с Pyramid, Flask, и Django, вам нужно сначала установить эти пакеты. Давайте установим все три из них.Мой предпочтительный метод - с помощью[venv](https://packaging.python.org/tutorials/installing-packages/#creating-virtual-environments) (Он доступен по умолчанию в Python 3.3).Просто выполните следующие шаги, чтобы создать и активировать виртуальную среду, а затем установите все три веб -фреймворка.

```sh
$ python3 -m venv lsbaws
$ ls lsbaws
bin   include   lib   pyvenv.cfg
$ source lsbaws/bin/activate
(lsbaws) $ pip install -U pip
(lsbaws) $ pip install pyramid
(lsbaws) $ pip install flask
(lsbaws) $ pip install django
```
На этом этапе вам нужно создать веб -приложение.Давайте начнем с [Pyramid](http://trypyramid.com/ "Pyramid") первый.Сохраните следующий код как _pyramidapp.py_ в тот же каталог, где вы сохранили _webserver2.py_ или загрузить файл напрямую с [GitHub](https://github.com/rspivak/lsbaws/blob/master/part2/pyramidapp.py):
```py
from pyramid.config import Configurator
from pyramid.response import Response


def hello_world(request):
    return Response(
        'Hello world from Pyramid!\n',
        content_type='text/plain',
    )

config = Configurator()
config.add_route('hello', '/hello')
config.add_view(hello_world, route_name='hello')
app = config.make_wsgi_app()
```

Теперь вы готовы обслуживать свое приложение Pyramid с помощью собственного веб -сервера:
```
(lsbaws) $ python webserver2.py pyramidapp:app
WSGIServer: Serving HTTP on port 8888 ...
```

Вы только что сказали вашему серверу загрузить _‘app’_ вызов из модуля Python _‘pyramidapp’_ Ваш сервер теперь готов принять запросы и перенаправить их в ваше приложение Pyramid. Приложение сейчас обрабатывает только один маршрут: _/hello_ маршрут. Скопипастите [http://localhost:8888/hello](http://localhost:8888/hello) адрес в браузер, нажмите Enter и наблюдайте за результатом:

![Pyramid](https://ruslanspivak.com/lsbaws-part2/lsbaws_part2_browser_pyramid.png)

Вы также можете проверить сервер через командную строку, используя утилиту _curl__
```
$ curl -v http://localhost:8888/hello
...
```

Проверьте, что сервер и _curl_ напечатает в консоль.

Теперь на [Flask](http://flask.pocoo.org/ "Flask"). Давайте последуем тем же путем.
```py
from flask import Flask
from flask import Response
flask_app = Flask('flaskapp')


@flask_app.route('/hello')
def hello_world():
    return Response(
        'Hello world from Flask!\n',
        mimetype='text/plain'
    )

app = flask_app.wsgi_app
```
Сохранить вышеуказанный код как _flaskapp.py_ или загрузить его из [GitHub](https://github.com/rspivak/lsbaws/blob/master/part2/flaskapp.py) и запустите сервер так:
```
(lsbaws) $ python webserver2.py flaskapp:app
WSGIServer: Serving HTTP on port 8888 ...
```

Теперь введите [http://localhost:8888/hello](http://localhost:8888/hello) в ваш браузер и нажмите Enter:

![Flask](https://ruslanspivak.com/lsbaws-part2/lsbaws_part2_browser_flask.png)

Опять же, попробуйте _curl_ или Postman и убедитесь сами, что сервер возвращает сообщение, сгенерированное приложением Flask:
```
$ curl -v http://localhost:8888/hello
...
```

Может ли сервер также обрабатывать приложение [django](https://www.djangoproject.com/django)? Попробуйте! Это немного более затратно по времени, и я бы порекомендовал клонировать с репозитория [djangoapp.py](https://github.com/rspivak/lsbaws/blob/master/part2/djangoapp.py). Вот исходный код, который в основном создаёт приложнение и добавляет его в проект django _helloworld_ (предварительно созданный с использованием команды Django _django-admin.py startProject_) в текущий папку Python проекта, а затем импортирует приложение в WSGI.
```py
import sys
sys.path.insert(0, './helloworld')
from helloworld import wsgi


app = wsgi.application
```
Сохраните приведенный выше код как _djangoapp.py_ и запустите приложение Django с помощью вашего веб -сервера:
```
(lsbaws) $ python webserver2.py djangoapp:app
WSGIServer: Serving HTTP on port 8888 ...
```
Введите следующий адрес и нажмите Enter:

![Django](https://ruslanspivak.com/lsbaws-part2/lsbaws_part2_browser_django.png)

И, как вы уже делали пару раз раньше, вы также можете проверить его в командной строке и подтвердить, что именно приложение Django обрабатывает ваши запросы на этот раз:
```
$ curl -v http://localhost:8888/hello
...
```

Вы пробовали?Вы убедились, что сервер работает с этими тремя структурами?Если нет, то пожалуйста, сделайте это.Чтение важно, но эта серия посвящена ручному кодингу, и это означает, что вам нужно испачкать руки.Иди и попробуй.Я буду ждать тебя, не волнуйся.Нет, серьезно, вы должны попробовать это, и, что еще лучше, набирайте все самостоятельно и убедитесь, что это работает, как и ожидалось.

Хорошо, вы испытали силу WSGI: это позволяет вам намешивать код в соответстветствии с вашими хотелками веб -сервераами и веб -фреймворками. WSGI обеспечивает минимальный интерфейс между веб -серверами Python и веб -фреймворками Python. Это очень просто, и его легко реализовать как на сервере, так и на стороне фреймворка. В следующем фрагменте кода показан сервер и фреймворк -сторона интерфейса:
```py
def run_application(application):
    """Server code."""
    # This is where an application/framework stores
    # an HTTP status and HTTP response headers for the server
    # to transmit to the client
    headers_set = []
    # Environment dictionary with WSGI/CGI variables
    environ = {}

    def start_response(status, response_headers, exc_info=None):
        headers_set[:] = [status, response_headers]

    # Server invokes the ‘application' callable and gets back the
    # response body
    result = application(environ, start_response)
    # Server builds an HTTP response and transmits it to the client
    ...

def app(environ, start_response):
    """A barebones WSGI app."""
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [b'Hello world!']

run_application(app)
```
Вот как это работает:

1. Фреймворк предоставляет вызываемое «приложение» (спецификация WSGI не предписывает, как это должно быть реализовано)
2. Сервер вызывает вызываемое «приложение» для каждого запроса, который он получает от HTTP-клиента. Он передает словарь «environ», содержащий переменные WSGI/CGI, и вызываемый объект «start_response» в качестве аргументов вызываемому объекту «приложение»..
3. Фреймворк/приложение генерирует статус HTTP и заголовки ответа HTTP и передает их в вызываемый объект start_response, чтобы сервер мог их сохранить.Фреймворк/приложение также возвращает тело ответа.
4. Сервер объединяет статус, заголовки ответа и тело ответа в HTTP-ответ и передает его клиенту (этот шаг не является частью спецификации, но это следующий логический шаг в потоке, и я добавил его для ясности).

И вот визуальное представление интерфейса:

![WSGI Interface](https://ruslanspivak.com/lsbaws-part2/lsbaws_part2_wsgi_interface.png)

До сих пор вы видели веб -приложения Pyramid, Flask и Django, и вы видели код сервера, который реализует сторону сервера спецификации WSGI.Вы даже видели фрагмент кода приложения голого WSGI, который не использует какую -либо структуру.

Дело в том, что когда вы пишете веб -приложение, используя одну из тех фреймворков, которые вы используете, то вы пишите на более высоком уровне и не работаете с WSGI напрямую, но я знаю, что вам также интересно узнать о платформе  WSGI, поскольку вы читаете эту статью. Итак, давайте создадим минималистичное веб-приложение/веб-инфраструктуру WSGI без использования Pyramid, Flask или Django и запустим его на сервере:
```
def app(environ, start_response):
    """A barebones WSGI application.

    This is a starting point for your own Web framework :)
    """
    status = '200 OK'
    response_headers = [('Content-Type', 'text/plain')]
    start_response(status, response_headers)
    return [b'Hello world from a simple WSGI application!\n']
```
Опять же, сохраните приведенный выше код в файле _wsgiapp.py_ или загрузите его из [github](https://github.com/rspivak/lsbaws/blob/master/part2/wsgiapp.py) напрямую и запустите приложение под вашим веб -сервером как:
```
(lsbaws) $ python webserver2.py wsgiapp:app
WSGIServer: Serving HTTP on port 8888 ...
```

Введите следующий адрес и нажмите Enter.Это результат, который вы должны увидеть:

![Simple WSGI Application](https://ruslanspivak.com/lsbaws-part2/lsbaws_part2_browser_simple_wsgi_app.png)

Вы только что написали свою собственную минималистичную веб -структуру WSGI, узнав о том, как создать веб -сервер!Возмутительнo.

Теперь давайте вернемся к тому, что сервер передает клиенту.Вот ответ HTTP, который генерирует сервер, когда вы вызовите приложение Pyramid с помощью клиента HTTP:

![HTTP Response Part 1](https://ruslanspivak.com/lsbaws-part2/lsbaws_part2_http_response.png)

В ответ есть некоторые знакомые части, которые вы видели в [Часть 1] , но в нем также есть что-то новое. У него, например, четыре [HTTP headers](https://en.wikipedia.org/wiki/List_of_HTTP_header_fields "HTTP header fields") что вы раньше не видели: _Content-Type_, _Content-Length_, _Date_, and _Server_. Это те заголовки, которые обычно должен иметь ответ веб -сервера.Ни один из них не требуется строго, хотя. Целью заголовков является передача дополнительной информации о HTTP -запросе/ответе.

Теперь, когда вы знаете больше об интерфейсе WSGI, вот тот же HTTP-ответ с дополнительной информацией о том, какие части его создали:

![HTTP Response Part 2](https://ruslanspivak.com/lsbaws-part2/lsbaws_part2_http_response_explanation.png)

Я еще ничего не сказал о словаре **environ**, но в основном это словарь Python, который должен содержать определенные переменные WSGI и CGI, предписанные спецификацией WSGI.Сервер берет значения для словаря из HTTP -запроса после анализа запроса.Вот как выглядит содержимое словаря:

![Environ Python Dictionary](https://ruslanspivak.com/lsbaws-part2/lsbaws_part2_environ.png)

Веб -структура использует информацию из этого словаря, чтобы решить, какое представление использовать на основе указанного маршрута, метода запроса и т. Д., Где читать тело запроса и где писать ошибки, если таковые имеются.

BY теперь вы создали свой собственный веб -сервер WSGI, и вы сделали веб -приложения, написанные с различными веб -структурами.И вы также создали свое веб -приложение/веб -фреймворк c нуля. Это было чертовски увлекательное путешествие. Давайте повторим, что должен сделать ваш веб -сервер WSGI для обслуживания запросов, направленных на приложение WSGI:

*   Во -первых, сервер запускается и загружает _‘application’_  предоставляемой вашей веб -структурой/приложением
*   Затем сервер читает запрос
*   Затем сервер анализирует его
*   Затем он строит _‘environ’_ Словарь с использованием данных запроса
*   Затем он вызывает вызываемый объект _‘application’_ со словарем _‘environ’_ и вызываемый объект «start_response» в качестве параметров и возвращает тело ответа.
*   Затем сервер создает HTTP-ответ, используя данные, возвращаемые вызовом объекта _‘application’_, а также заголовки статуса и ответа, заданные вызываемым объектом «start_response».
*   И, наконец, сервер передает ответ HTTP обратно клиенту

![Server Summary](https://ruslanspivak.com/lsbaws-part2/lsbaws_part2_server_summary.png)

Это все, что нужно.Теперь у вас есть работающий сервер WSGI, который может обслуживать основные веб -приложения, написанные с помощью веб -фреймворков, соответствующих WSGI, такие как [Django](https://www.djangoproject.com/ "Django"), [Flask](http://flask.pocoo.org/ "Flask"), [Pyramid](http://trypyramid.com/ "Pyramid"), Или ваша собственная структура WSGI.Самое приятное, что сервер может использоваться с несколькими веб -фреймворками без каких -либо изменений в базе кода сервера.Совсем неплохо.

Прежде чем уйти, вот еще один вопрос, о котором вы можете подумать: «Как сделать сервер обрабатывающий более одного запроса за раз?» _
Оставайтесь с нами, и я покажу вам способ сделать это в [Part 3](README3.md). 
 