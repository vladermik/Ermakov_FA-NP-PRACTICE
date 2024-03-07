Пишем свой веб-сервер на Python: протокол HTTP
==============================================



#### Оглавление

*   [Введение](#intro)
*   [Задача HTTP-сервера](#server-goal)
*   [Структура HTTP-сервера](#server-structure)
*   [Пару слов о кодировке](#character-encoding)
*   [Стратегия разбора запроса](#parsing-approach)
*   [Разбор request line](#parsing-request-line)
*   [Разбор заголовков запроса](#parsing-headers)
*   [Обработка запроса](#handling-request)
*   [Отправка ответа](#sending-response)
*   [Чтение тела запроса](#reading-request-body)
*   [Повторное использование TCP-соединений](#http-keep-alive)
*   [Заключение](#conclusion)
*   [Ссылки по теме](#further-reading)

Введение
--------

На данный момент мы умеем [отправлять и принимать данные](../1_echo_server/README.md) по сети и [организовывать обработку запросов](../4_requests) на сервере. Настало время перейти на более высокий уровень - реализовать свой HTTP сервер.

Для начала определимся, что же такое HTTP. [Hypertext Transfer Protocol (HTTP)](https://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol) - _это протокол прикладного уровня, предназначенный для передачи гипертекстовых данных в распределенных информационных системах._ Ух, сложнааа... А на самом деле нет. Давайте разбираться!

Протокол - это не более, чем соглашение между двумя или более участниками некоторого взаимодействия. Когда речь идет о сетевом взаимодействии, протоколы принято условно [разделять на уровни](https://en.wikipedia.org/wiki/OSI_model). В самом низу находятся протоколы физического уровня, определяющие как данные передаются в физических средах, т.е. по проводам, оптоволокну, и т.п. Знакомые нам из [первой части](../1_echo_server/README.md) протоколы IP и TCP - это протоколы сетевого и транспортного уровня, соответственно. Они определяют более высокоуровневые детали взаимодействия, в частности, IP отвечает за адресацию компьютеров/узлов в сети, а TCP - за надежную передачу данных произвольной (т.е. в общем случае превышающей размер одного IP-пакета) длины между узлами. HTTP же располагается на самом высоком уровне - [прикладном](https://en.wikipedia.org/wiki/Application_layer). От нижележащих протоколов HTTP ожидает гарантий надежности доставки данных, а сам концентрируется на определении понятий запросов и ответов (сообщений) и их семантике. Фактически, HTTP является основным протоколом передачи данных в [вебе](https://en.wikipedia.org/wiki/World_Wide_Web), а сами данные являются [гипертекстом](https://en.wikipedia.org/wiki/Hypertext), зачастую представленным в формате HTML-страниц.



  

До версии [HTTP/2](https://en.wikipedia.org/wiki/HTTP/2), появившейся в 2015 году, HTTP был простым текстовым протоколом. Во второй версии протокол претерпел значительные доработки, стал эффективнее и приобрел новые возможности, но в то же время реализация клиентов и серверов усложнилась. На декабрь 2021 только [_46.8%_ сайтов Интернет используют HTTP/2](https://w3techs.com/technologies/details/ce-http2), но наблюдается устойчивый восходящий тренд.

В этой статье мы рассмотрим, как можно реализовать простейший HTTP-сервер на Python. Ради простоты, мы будем работать с версией протокола HTTP/1.1, а код сервера будет скорее служить образовательным целям, нежели являться полнофункциональным веб-сервером.

Задача HTTP-сервера
-------------------

HTTP-сервер - это (в большинстве случаев) развитие идеи уже хорошо нам известного TCP-сервера. Задача HTTP-сервера - принимать входящие HTTP-запросы от клиентов, обрабатывать их и отправлять HTTP-ответы.

Простейший HTTP-запрос выглядит следующим образом:

    GET / HTTP/1.1
    Host: example.com
    

То, что мы видим выше - это так называемое _сообщение_ [HTTP message](https://tools.ietf.org/html/rfc7230#section-3). Опуская вопрос кодировки данных, сообщение HTTP/1.1 - это обычный текст, который состоит из строк, разделенных символами _CRLF_, т.е. `\r\n`. Первая строка запроса называется [_request line_](https://tools.ietf.org/html/rfc7230#section-3.1.1). Она определяет _метод_ [method](https://tools.ietf.org/html/rfc7231#section-4), _цель_ [target](https://tools.ietf.org/html/rfc7230#section-5.3) и версию протокола. Далее идут [заголовки запроса](https://tools.ietf.org/html/rfc7230#section-3.2). В ранних версиях протокола секция заголовков могла отсутствовать полностью, но в HTTP/1.1 заголовок _Host_ является обязательным.

Назначение вышеописанных элементов мы рассмотрим чуть позже, а сейчас перейдем к примеру HTTP-ответа:

    HTTP/1.1 200 OK
    

HTTP-ответы также представлены _сообщениями_. Первая строка ответа называется [_status line_](https://tools.ietf.org/html/rfc7230#section-3.1.2). Она состоит из _версии_, трехзначного _кода статуса_ [status-code](https://tools.ietf.org/html/rfc7231#section-6) и опционального текста _причины_.

Как и в случае с TCP-сервером, для того, чтобы начать обрабатывать HTTP-запросы, наш сервер должен создать _слушающий (listening) сокет_. На каждое входящее соединение, сервер должен прочитывать текст HTTP-запроса, вызывать соответствующий обработчик, и, получив от него ответ, отсылать данные клиенту. TCP-соединение может быть как завершено непосредственно после отправки ответа, так и сохранено для повторного использования клиентом.

Структура HTTP-сервера
----------------------

Реализация полнофункционального HTTP/1.1-сервера требует учета всех требований протокола, определенных группой RFC ([RFC7230](https://tools.ietf.org/html/rfc7230) "Message Syntax and Routing", [RFC7231](https://tools.ietf.org/html/rfc7231) "Semantics and Content", [RFC7232](https://tools.ietf.org/html/rfc7232) "Conditional Requests", [RFC7233](https://tools.ietf.org/html/rfc7233) "Range Requests", [RFC7234](https://tools.ietf.org/html/rfc7234) "Caching", [RFC7235](https://tools.ietf.org/html/rfc7235) "Authentication"). Мы же скорее хотим сфокусироваться на самом подходе к реализации. **Исходный код в этой статье не готов для боевого использования, и не гарантируется, что его логика строго следует спецификации протокола.**

В качестве основы будущего HTTP-сервера мы будем использовать следующий класс:

    # python3
    
    import socket
    import sys
    
    class MyHTTPServer:
      def __init__(self, host, port, server_name):
        self._host = host
        self._port = port
        self._server_name = server_name
    
      def serve_forever(self):
        serv_sock = socket.socket(
          socket.AF_INET,
          socket.SOCK_STREAM,
          proto=0)
    
        try:
          serv_sock.bind((self._host, self._port))
          serv_sock.listen()
    
          while True:
            conn, _ = serv_sock.accept()
            try:
              self.serve_client(conn)
            except Exception as e:
              print('Client serving failed', e)
        finally:
          serv_sock.close()
    
      def serve_client(self, conn):
        try:
          req = self.parse_request(conn)
          resp = self.handle_request(req)
          self.send_response(conn, resp)
        except ConnectionResetError:
          conn = None
        except Exception as e:
          self.send_error(conn, e)
    
        if conn:
          conn.close()
    
      def parse_request(self, conn):
        pass  # TODO: implement me
    
      def handle_request(self, req):
        pass  # TODO: implement me
    
      def send_response(self, conn, resp):
        pass  # TODO: implement me
    
      def send_error(self, conn, err):
        pass  # TODO: implement me
    
    
    if __name__ == '__main__':
      host = sys.argv[1]
      port = int(sys.argv[2])
      name = sys.argv[3]
    
      serv = MyHTTPServer(host, port, name)
      try:
        serv.serve_forever()
      except KeyboardInterrupt:
        pass
    

Код сервера максимально упрощен, чтобы иметь возможность сфокусироваться именно на работе с протоколом HTTP. Обработка запросов происходит [_синхронно_](/ru/posts/writing-python-web-server-part-2/#single-client-single-process), т.е. возможно обслуживать не более одного клиента в один момент времени. Сервер в бесконечном цикле осуществляет прием входящих соединений, выполняя `serv_sock.accept()`. Каждое соединение `conn` является клиентским [сокетом](/ru/posts/writing-python-web-server-part-1/). Прием очередного соединения инициирует обработку HTTP-запроса `serve_client(conn)`. Обработка же заключается в чтении и _разборе aka [синтаксическом анализе](https://ru.wikipedia.org/wiki/%D0%A1%D0%B8%D0%BD%D1%82%D0%B0%D0%BA%D1%81%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B8%D0%B9_%D0%B0%D0%BD%D0%B0%D0%BB%D0%B8%D0%B7)_ HTTP-запроса `parse_request(conn)`, непосредственно обработке `handle_request(req)` и отправке ответа `send_response(conn, resp)`. В случае же ошибки на любом из этапов, обработка заканчивается отправкой сообщения об ошибке `send_error(conn, err)`.

Запустить сервер можно, сохранив код в файле `server.py` и выполнив команду:

    python3 server.py 127.0.0.1 53210 example.local
    

Для отправки тестовых HTTP-запросов удобно пользоваться консольной утилитой [_netcat_](https://en.wikipedia.org/wiki/Netcat):

    nc localhost 53210
    
    > GET / HTTP/1.1
    > Host: example.local
    >
    

Пару слов о кодировке
---------------------

В соответствии со спецификацией, одно сообщение HTTP может одновременно содержать данные, представленные в различных кодировках. В то же время, служебные данные, такие как request line, status line и заголовки должны быть преставлены некоторым надмножеством **однобайтовой** ASCII кодировки, определенном в стандарте [ISO/IEC 8859-1](https://en.wikipedia.org/wiki/ISO/IEC_8859-1). Почему существует такое требование становится очевидно при попытке реализации собственного HTTP-сервера. Как мы уже видели выше, HTTP-запрос - это обычный текст, а текст в компьютерном мире - это последовательность байт плюс дополнительное знание, в какой кодировке эти байты должны быть интерпретированы. **Без знания кодировки в общем случае невозможно (и зачастую небезопасно) каким-либо образом интерпретировать текстовые данные, представленные последовательностью байт.** Так как никакой предварительной фазы обмена информацией о кодировке в протоколе не предусмотрено, логичным решением является заранее договориться, что все данные по умолчанию передаются в одной и той же кодировке, и такой кодировкой была выбрана ASCII. В таком случае, у сервера всегда существует возможность произвести разбор запроса на составляющие, т.е. отделить request line от блока заголовков, а заголовки друг от друга.

Ограничение ASCII к счастью не распространяется на тело запроса. Имея возможность прочитать заголовки, из них возможно получить информацию о наличии, размере и кодировке тела запроса. Далее сервер должен прочитать заданное количество _"сырых"_ байт из сокета и лишь потом декодировать их в строку с использованием договоренной кодировки (или кодировки по умолчанию).

Если же существует очень большое желании использовать не-ASCII символы в значениях заголовков, то проткол предлагает кодировать данные в [MIME](https://en.wikipedia.org/wiki/MIME), хотя поддержка и использование этой возможности не является широко распространенной практикой.

Стратегия разбора запроса
-------------------------

Разбор запроса состоит из следующих шагов:

*   Читаем первую строку, т.е. request line, разбираем ее на _метод_, _цель_ и _версию_ и сохраняем их в некоторую структуру данных.
    
*   Читаем построчно заголовки, разбираем их на _имя_ и _значение_ и сохраняем в словаре (aka ассоциативном массиве) с именем заголовка в качестве ключа. Индикатором конца секции заголовков служит пустая строка.
    
*   На основе _метода_ и заголовков определяем, содержит ли запрос _тело_. Если да, поточно читаем байты из соединения до тех пор, пока прочитанное количество не равно ожидаемому размеру тела запроса. Техника чтения может отличаться в зависимости от типа запроса, подробнее см. секцию [Чтение тела запроса](#read-request-body).
    

Как было отмечено ранее, чтение строк должно осуществляться с использованием кодировки ISO/IEC 8859-1. Применение других кодировок возможно только к _значениям_ элементов сообщения (т.е. к значениям заголовков или телу запроса).

Разбор request line
-------------------

В качестве разминки выполним разбор request line, самой первой строки HTTP-запроса. Прежде всего, из соединения необходимо прочитать _строку_, т.е. последовательность байт, заканчивающуюся комбинацией `\r\n`. Простейший способ - это читать данные байт за байтом, сохраняя их в некотором буфере, пока не будет найдена необходимая комбинация:

    class MyHTTPServer:
      def parse_request(self, conn):
        buf = ''
        while '\r\n' not in buf:
          byte = conn.recv(1)  # возвращает тип bytes
          buf += str(byte, 'iso-8859-1')
    
        # ...
    

Однако, такой подход достаточно неэффективен, так как каждый вызов `conn.recv()` приводит к системному вызову, а значит имеет высокие накладные расходы. К счастью, благодаря широчайшим возможностям стандартной библиотеки Python, сокет [предоставляет возможность](https://docs.python.org/3/library/socket.html#socket.socket.makefile) создать вокруг него некоторую обертку, которая предоставляет [file object](https://docs.python.org/3/glossary.html#term-file-object) интерфейс:

    MAX_LINE = 64*1024
    
    class MyHTTPServer:
      def parse_request(self, conn):
        rfile = conn.makefile('rb')
        raw = rfile.readline(MAX_LINE + 1)  # эффективно читаем строку целиком
        if len(raw) > MAX_LINE:
          raise Exception('Request line is too long')
    
        req_line = str(raw, 'iso-8859-1')
        req_line = req_line.rstrip('\r\n')
        words = req_line.split()            # разделяем по пробелу
        if len(words) != 3:                 # и ожидаем ровно 3 части
          raise Exception('Malformed request line')
    
        method, target, ver = words
        if ver != 'HTTP/1.1':
          raise Exception('Unexpected HTTP version')
    
        return Request(method, target, ver, rfile)
    
    class Request:
      def __init__(self, method, target, version, rfile):
        self.method = method
        self.target = target
        self.version = version
        self.rfile = rfile
    

Так как мы фокусируемся только на версии HTTP/1.1, код разбора получился достаточно коротким и простым. Все, что мы сделали - это прочитали строку из соединения и разбили ее по пробелу на составляющие - _метод_, _цель_ и _версию_, сохранив их в структуре _Request_.

Разбор заголовков запроса
-------------------------

Перейдем к следующему шагу - разбору HTTP-заголовков. Запрос с заголовками выглядит следующим образом:

    GET /foo/bar HTTP/1.1
    Host: example.local
    Accept: text/html
    User-Agent: Mozilla/5.0
    
    # пустая строка выше - индикатор конца блока заголовков
    

Таким образом, необходимо читать строку за строкой, до тех пор, пока не будет встречена первая пустая строка. Выполним небольшой рефакторинг кода нашего сервера, выделив разбор request line и разбор заголовков в отдельные методы:

    MAX_HEADERS = 100
    
    class MyHTTPServer:
      def parse_request(self, conn):
        rfile = conn.makefile('rb')
        method, target, ver = self.parse_request_line(rfile)
        headers = self.parse_headers(rfile)
        return Request(method, target, ver, headers, rfile)
    
      def parse_headers(self, rfile):
        headers = []
        while True:
          line = rfile.readline(MAX_LINE + 1)
          if len(line) > MAX_LINE:
            raise Exception('Header line is too long')
    
          if line in (b'\r\n', b'\n', b''):
            # завершаем чтение заголовков
            break
    
          headers.append(line)
          if len(headers) > MAX_HEADERS:
            raise Exception('Too many headers')
        return headers
    
      def parse_request_line(self, rfile):
        pass  # ...
    

В результате, мы получили список отдельных заголовков `headers` вида:

    [b'Host: example.local\r\n', b'Accept: text/html\r\n', b'User-Agent: Mozilla/5.0\r\n']
    

В то же время, [мы планировали](#parsing-approach) сохранять заголовки HTTP-сообщений в ассоциативном массиве, где ключами бы являлись ключи заголовков (например, _Host_, _Accept_ или _User-Agent_), а значениями - соответствующие значения полей. Одним из вариантов было бы продолжить разбор, разбивая каждый элемент списка по символу `:` и сохраняя левую часть в качестве ключа, а правую - в качестве значения в некотором _dict_:

    def parse_headers(self, rfile):
      headers = []
    
      # ... read headers lines from rfile
    
      hdict = {}
      for h in headers:
        h = h.decode('iso-8859-1')
        k, v = h.split(':', 1)
        hdict[k] = v
    
      return hdict
    

Однако, существует достаточно большое количество частных случаев, которые подход выше не учитывает. Например, в одном сообщении может быть несколько заголовков с одинаковым именем, т.е. в общем случае по ключу в `hdict` должен находиться скорее список, а не одна строка; значения заголовков могут быть представлены в _MIME_\-кодировке; и пр.

К счастью, формат HTTP-сообщений, как и email-сообщений, следует спецификации [Internet Message Format](https://tools.ietf.org/html/rfc5322). Стандартная библиотека Python предоставляет модуль [email](https://docs.python.org/3.7/library/email.html), который в частности может быть использован для разбора HTTP-заголовков. Нам понадобится внести лишь минимальное изменение в метод `parse_headers()`, чтобы воспользоваться стандартным парсером:

    from email.parser import Parser
    
    class MyHTTPServer:
      def parse_headers(self, rfile):
        headers = []
    
        # ... read headers lines from rfile
    
        sheaders = b''.join(headers).decode('iso-8859-1')
        return Parser().parsestr(sheaders)
    

Возвращаемое значение метода `Parser.parsestr()` - это объект [`email.message.Message`](https://docs.python.org/3.7/library/email.compat32-message.html), который напоминает `OrderedDict`. Ключи в _Message_ - это отсортированные в порядке появления ключи заголовков.

Последнее, что мы сделаем в рамках задачи разбора заголовков - это проверим наличие и соответствие заголовка _Host_:

    class MyHTTPServer:
      def parse_request(self, conn):
        # ...
        headers = self.parse_headers(rfile)
        host = headers.get('Host')
        if not host:
          raise Exception('Bad request')
        if host not in (self._server_name,
                        f'{self._server_name}:{self._port}'):
          raise Exception('Not found')
        return Request(method, target, ver, headers, rfile)
    

Проверим изменение:

    # terminal 1
    python3 server.py 127.0.0.1 53210 example.local
    
    # terminal 2
    nc localhost 53210
    > GET / HTTP/1.1
    > Host: example.local
    
    # terminal 3
    nc localhost 53210
    > GET / HTTP/1.1
    > Host: iximiuz.com
    

Обработка запроса
-----------------

Настало время заняться непосредственно обработкой HTTP-запросов, т.е. бизнес-логикой нашего сервера. Одной из традиционных задач, выполняемых HTTP-сервером, является отдача статического контента, т.е. файлов и директорий из некоторой корневой директории. Мы же опустим эту функцию и сфокусируемся на кастомной логике приложения.

Представим, что мы хотим создать сервис, который позволяет регистрировать пользователей, получать список ID зарегистрированных пользователей, а также информацию о каждом пользователе по его ID. Опишем API нашего сервиса:

    # Создание нового пользователя
    POST /users?name=Vasya&age=42
    
    # Получение списка пользователей
    GET /users
    
    # Получение профиля пользователя
    GET /users/123
    

Дополнительно, в зависимости от заголовка запроса [_Accept_](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept), сервер будет возвращать данные либо в формате _HTML_, либо _JSON_.

Прежде, чем приступать непосредственно к обработке, давайте расширим возможности класса _Request_, чтобы впоследствии код обработки получился чуть более высокоуровневым. Добавим полезные методы `path` и `query`, которые будут разбивать _цель_ вида `/users?name=Vasya&age=42` на `/users` и `{'name': ['Vasya'], 'age': ['42']}`, соответственно:

    from functools import lru_cache
    from urllib.parse import parse_qs, urlparse
    
    class Request:
      def __init__(self, method, target, version, headers, rfile):
        self.method = method
        self.target = target
        self.version = version
        self.headers = headers
        self.rfile = rfile
    
      @property
      def path(self):
        return self.url.path
    
      @property
      @lru_cache(maxsize=None)
      def query(self):
        return parse_qs(self.url.query)
    
      @property
      @lru_cache(maxsize=None)
      def url(self):
        return urlparse(self.target)
    

Обработка запросов начинается в методе `handle_request()`. Сам метод занимается скорее диспетчеризацией запросов на основе _метода_ и _цели_, чем непосредственно обработкой:

    from urllib.parse import parse_qs
    
    class MyHTTPServer:
      def __init(self, *args):
        # ....
        self._users = {}
    
      def handle_request(self, req):
        if req.path == '/users' and req.method == 'POST':
          return self.handle_post_users(req)
    
        if req.path == '/users' and req.method == 'GET':
          return self.handle_get_users(req)
    
        if req.path.startswith('/users/'):
          user_id = req.path[len('/users/'):]
          if user_id.isdigit():
            return self.handle_get_user(req, user_id)
    
        raise Exception('Not found')
    
      def handle_post_users(self, req): pass
    
      def handle_get_users(self, req): pass
    
      def handle_get_user(self, req, user_id): pass
    

Давайте посмотрим на метод создания пользователя `handle_post_users()`:

    class MyHTTPServer:
      def handle_post_users(self, req):
        user_id = len(self._users) + 1
        self._users[user_id] = {'id': user_id,
                                'name': req.query['name'][0],
                                'age': req.query['age'][0]}
        return Response(204, 'Created')
    

Все очень просто - на основании данных из запроса создаем новый объект пользователя и сохраняем его на сервере. Ответом на такой запрос является лишь строка статуса [`HTTP/1.1 204 Created\r\n`](https://httpstatuses.com/204). Класс `Response` можно определить следующим образом:

    class Response:
      def __init__(self, status, reason, headers=None, body=None):
        self.status = status
        self.reason = reason
        self.headers = headers
        self.body = body
    

Следующий функция нашего приложения - это возвращение списка зарегистрированных пользователей `handle_get_users()`. В данном случае нам понадобится полноценный ответ, содержащий в себе перечисление всех пользователей на сервере. А в качестве дополнительной возможности, наш сервер будет поддерживать два формата данных - _text/html_ и _application/json_:

    class MyHTTPServer:
      def handle_get_users(self, req):
        accept = req.headers.get('Accept')
        if 'text/html' in accept:
          contentType = 'text/html; charset=utf-8'
          body = '<html><head></head><body>'
          body += f'<div>Пользователи ({len(self._users)})</div>'
          body += '<ul>'
          for u in self._users.values():
            body += f'<li>#{u["id"]} {u["name"]}, {u["age"]}</li>'
          body += '</ul>'
          body += '</body></html>'
    
        elif 'application/json' in accept:
          contentType = 'application/json; charset=utf-8'
          body = json.dumps(self._users)
    
        else:
          # https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/406
          return Response(406, 'Not Acceptable')
    
        body = body.encode('utf-8')
        headers = [('Content-Type', contentType),
                   ('Content-Length', len(body))]
        return Response(200, 'OK', headers, body)
    

Важно обратить внимание на способ представления `body`. Так как наш ответ содержит символы кириллицы, ASCII кодировка нам не подходит. Мы работаем с `body` как со строкой в кодировке UTF-8. Однако, прежде чем создать объект ответа, мы кодируем строку в последовательность байт, а заголовок [_Content-Length_](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Length), представляющий собой размер ответа, принимает значение длины уже в байтах. Заголовок _Content-Type_ при этом содержит секцию `; charset=utf-8`, по которой клиенты нашего сервера могут определить кодировку тела ответа.

Реализацию последнего метода нашего приложения `handle_get_user(user_id)` можно посмотреть в [полном исходном коде сервера](#full-source-code) в конце статьи.

Отправка ответа
---------------

Последний шаг, отделяющий нас от минимальной рабочей версии - это отправка HTTP-ответов. Код отправки достаточно прост. Прежде всего записываем в соединение status line вида `HTTP/1.1 <status_code> <reason>`. Затем, построчно записываем заголовки и не забываем пустую строку, обозначающую конец секции заголовков. Все вышеперечисленные данные должны быть представлены в кодировке ISO/IEC 8859-1. При наличии тела ответа, ожидаем, что оно уже представлено последовательностью байт и просто отправляем его в сокет:

    class MyHTTPServer:
      def send_response(self, conn, resp):
        wfile = conn.makefile('wb')
        status_line = f'HTTP/1.1 {resp.status} {resp.reason}\r\n'
        wfile.write(status_line.encode('iso-8859-1'))
    
        if resp.headers:
          for (key, value) in resp.headers:
            header_line = f'{key}: {value}\r\n'
            wfile.write(header_line.encode('iso-8859-1'))
    
        wfile.write(b'\r\n')
    
        if resp.body:
          wfile.write(resp.body)
    
        wfile.flush()
        wfile.close()
    

В случае возникновения ошибки на сервере, нам также необходимо отправить ответ. Для этого реализуем метод `send_error()`, фактически являющийся оберткой вокруг метода `send_response()`:

    class MyHTTPServer:
      def send_error(self, conn, err):
        try:
          status = err.status
          reason = err.reason
          body = (err.body or err.reason).encode('utf-8')
        except:
          status = 500
          reason = b'Internal Server Error'
          body = b'Internal Server Error'
        resp = Response(status, reason,
                       [('Content-Length', len(body))],
                       body)
        self.send_response(conn, resp)
    

Теперь мы можем ввести класс `HTTPError(Exception)` и заменить в коде сервера вхождения вида `raise Exception('Not found')` на `raise HTTPError(404, 'Not found')`.

    class HTTPError(Exception):
      def __init__(self, status, reason, body=None):
        super()
        self.status = status
        self.reason = reason
        self.body = body
    

Запустим наш сервер:

    # terminal 1
    
    python3 server.py 127.0.0.1 53210 example.local
    

И протестируем его, создав двух пользователей:

    # terminal 2
    
    nc localhost 53210
    > POST /users?name=Vasya&age=42 HTTP/1.1
    > Host: example.local
    >
    
    < HTTP/1.1 204 Created
    
    nc localhost 53210
    > POST /users?name=Vasya&age=42 HTTP/1.1
    > Host: example.local
    >
    
    < HTTP/1.1 204 Created
    

Теперь попробуем получить информацию о зарегистрированных пользователях - в формате HTML и в формате JSON:

    # terminal 2
    
    nc localhost 53210
    > GET /users HTTP/1.1
    > Host: example.local
    > Accept: text/html
    >
    
    < HTTP/1.1 200 OK
    < Content-Type: text/html; charset=utf-8
    < Content-Length: 129
    <
    < <html><head></head><body><div>Пользователи (2)</div><ul><li>#1 Vasya, 42</li><li>#2 Petya, 24</li></ul></body></html>
    
    nc localhost 53210
    > GET /users HTTP/1.1
    > Host: example.local
    > Accept: application/json
    >
    
    < HTTP/1.1 200 OK
    < Content-Type: application/json; charset=utf-8
    < Content-Length: 92
    <
    < {"1": {"id": 1, "name": "Vasya", "age": "42"}, "2": {"id": 2, "name": "Petya", "age": "24"}}
    

Также попробуем протестировать сообщения об ошибке:

    # terminal 2
    
    nc localhost 53210
    > GET /users HTTP/1.1
    >
    
    < HTTP/1.1 400 Bad request
    < Content-Length: 22
    <
    < Host header is missing
    
    nc localhost 53210
    > GET /foo HTTP/1.1
    > Host: example.local
    > Accept: application/json
    >
    
    < HTTP/1.1 404 Not found
    < Content-Length: 9
    <
    < Not found
    

Чтение тела запроса
-------------------

До настоящего момента, наш сервер не умел работал с телом запроса. Расширим класс _Request_, добавив тривиальную реализацию метода `body()`:

    class Request:
      def body(self):
        size = self.headers.get('Content-Length')
        if not size:
          return None
        return self.rfile.read(size)
    

Если абстрактно представить себе проблему передачи сообщений по сети, то задача чтения одного сообщения может быть непротиворечиво решена только если: сообщения всегда имеют фиксированную длину, сообщения имеют метаинформацию о размере, сообщения разделены некоторым набором символов. В случае протокола HTTP используется подход с передачей метаинформации в заголовоке _Content-Length_, определяющем длину тела сообщения.

Необходимо заметить, что не все типы запросов могут иметь тело. Например, запросы GET не должны иметь тела сообщения.

Протокол HTTP также предоставляет возможность передачи больших объемов данных, разбивая их на части (т.н. chunk-и). В таком случае добавляется специалльный заголовок `Transfer-Encoding: chunked`, а тело запроса (или ответа) представляется блоками байт, каждый из которых имеет префикс в виде длины блока. Подробнее тут [Chunked transfer encoding](https://en.wikipedia.org/wiki/Chunked_transfer_encoding).

Повторное использование TCP-соединений
--------------------------------------

Протокол HTTP поддерживает отправку нескольких последовательных (в версии HTTP2 поддерживается также мультиплексирование) HTTP-запросов в рамках одного TCP-соединения. Несмотря на то, что наш сервер мгновенно закрывает соединение после отправки ответа, поведением по умолчанию для протокола HTTP/1.1 является сохранение соединения открытым для повторного его использования клиентом. Это так называемый механизм [_HTTP keep-alive_](https://en.wikipedia.org/wiki/HTTP_persistent_connection). В случае же, если клиент или сервер по каким-либо причинам не хотят реиспользовать соединение, необходимо добавить заголовок `Connection: close`.

Заключение
----------

Реализованный нами HTTP-сервер объединяет в себе как непосредственно работу с протоколом, так и более высокоуровневую обработку HTTP-запросов, суть - бизнес-логику приложения. Очевидным развитием архитектуры веб-сервера является отделение редко меняющейся протокольной части от специфичной и волатильной бизнес-логики приложения. Более того, формализация программного интерфейса HTTP-сервера в виде некоторого стандарта позволила бы создавать переносимые между серверами приложения, избегая дублирования кода. Не удивительно, что Python-сообщество уже решило эту проблему, введя стандарт взаимодействия сервера и приложения [WSGI](https://en.wikipedia.org/wiki/Web_Server_Gateway_Interface). В [следующей статье](/ru/posts/writing-python-web-server-part-4/) мы рассмотрим, что из себя представляет эта спецификация и как на уровне кода можно научить приложение взаимодействовать с любым WSGI-совместимым HTTP-сервером.

Исходный код сервера

    # python3
    
    import json
    import socket
    import sys
    from email.parser import Parser
    from functools import lru_cache
    from urllib.parse import parse_qs, urlparse
    
    MAX_LINE = 64*1024
    MAX_HEADERS = 100
    
    class MyHTTPServer:
      def __init__(self, host, port, server_name):
        self._host = host
        self._port = port
        self._server_name = server_name
        self._users = {}
    
      def serve_forever(self):
        serv_sock = socket.socket(
          socket.AF_INET,
          socket.SOCK_STREAM,
          proto=0)
    
        try:
          serv_sock.bind((self._host, self._port))
          serv_sock.listen()
    
          while True:
            conn, _ = serv_sock.accept()
            try:
              self.serve_client(conn)
            except Exception as e:
              print('Client serving failed', e)
        finally:
          serv_sock.close()
    
      def serve_client(self, conn):
        try:
          req = self.parse_request(conn)
          resp = self.handle_request(req)
          self.send_response(conn, resp)
        except ConnectionResetError:
          conn = None
        except Exception as e:
          self.send_error(conn, e)
    
        if conn:
          req.rfile.close()
          conn.close()
    
      def parse_request(self, conn):
        rfile = conn.makefile('rb')
        method, target, ver = self.parse_request_line(rfile)
        headers = self.parse_headers(rfile)
        host = headers.get('Host')
        if not host:
          raise HTTPError(400, 'Bad request',
            'Host header is missing')
        if host not in (self._server_name,
                        f'{self._server_name}:{self._port}'):
          raise HTTPError(404, 'Not found')
        return Request(method, target, ver, headers, rfile)
    
      def parse_request_line(self, rfile):
        raw = rfile.readline(MAX_LINE + 1)
        if len(raw) > MAX_LINE:
          raise HTTPError(400, 'Bad request',
            'Request line is too long')
    
        req_line = str(raw, 'iso-8859-1')
        words = req_line.split()
        if len(words) != 3:
          raise HTTPError(400, 'Bad request',
            'Malformed request line')
    
        method, target, ver = words
        if ver != 'HTTP/1.1':
          raise HTTPError(505, 'HTTP Version Not Supported')
        return method, target, ver
    
      def parse_headers(self, rfile):
        headers = []
        while True:
          line = rfile.readline(MAX_LINE + 1)
          if len(line) > MAX_LINE:
            raise HTTPError(494, 'Request header too large')
    
          if line in (b'\r\n', b'\n', b''):
            break
    
          headers.append(line)
          if len(headers) > MAX_HEADERS:
            raise HTTPError(494, 'Too many headers')
    
        sheaders = b''.join(headers).decode('iso-8859-1')
        return Parser().parsestr(sheaders)
    
      def handle_request(self, req):
        if req.path == '/users' and req.method == 'POST':
          return self.handle_post_users(req)
    
        if req.path == '/users' and req.method == 'GET':
          return self.handle_get_users(req)
    
        if req.path.startswith('/users/'):
          user_id = req.path[len('/users/'):]
          if user_id.isdigit():
            return self.handle_get_user(req, user_id)
    
        raise HTTPError(404, 'Not found')
    
      def send_response(self, conn, resp):
        wfile = conn.makefile('wb')
        status_line = f'HTTP/1.1 {resp.status} {resp.reason}\r\n'
        wfile.write(status_line.encode('iso-8859-1'))
    
        if resp.headers:
          for (key, value) in resp.headers:
            header_line = f'{key}: {value}\r\n'
            wfile.write(header_line.encode('iso-8859-1'))
    
        wfile.write(b'\r\n')
    
        if resp.body:
          wfile.write(resp.body)
    
        wfile.flush()
        wfile.close()
    
      def send_error(self, conn, err):
        try:
          status = err.status
          reason = err.reason
          body = (err.body or err.reason).encode('utf-8')
        except:
          status = 500
          reason = b'Internal Server Error'
          body = b'Internal Server Error'
        resp = Response(status, reason,
                       [('Content-Length', len(body))],
                       body)
        self.send_response(conn, resp)
    
      def handle_post_users(self, req):
        user_id = len(self._users) + 1
        self._users[user_id] = {'id': user_id,
                                'name': req.query['name'][0],
                                'age': req.query['age'][0]}
        return Response(204, 'Created')
    
      def handle_get_users(self, req):
        accept = req.headers.get('Accept')
        if 'text/html' in accept:
          contentType = 'text/html; charset=utf-8'
          body = '<html><head></head><body>'
          body += f'<div>Пользователи ({len(self._users)})</div>'
          body += '<ul>'
          for u in self._users.values():
            body += f'<li>#{u["id"]} {u["name"]}, {u["age"]}</li>'
          body += '</ul>'
          body += '</body></html>'
    
        elif 'application/json' in accept:
          contentType = 'application/json; charset=utf-8'
          body = json.dumps(self._users)
    
        else:
          # https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/406
          return Response(406, 'Not Acceptable')
    
        body = body.encode('utf-8')
        headers = [('Content-Type', contentType),
                   ('Content-Length', len(body))]
        return Response(200, 'OK', headers, body)
    
      def handle_get_user(self, req, user_id):
        user = self._users.get(int(user_id))
        if not user:
          raise HTTPError(404, 'Not found')
    
        accept = req.headers.get('Accept')
        if 'text/html' in accept:
          contentType = 'text/html; charset=utf-8'
          body = '<html><head></head><body>'
          body += f'#{user["id"]} {user["name"]}, {user["age"]}'
          body += '</body></html>'
    
        elif 'application/json' in accept:
          contentType = 'application/json; charset=utf-8'
          body = json.dumps(user)
    
        else:
          # https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/406
          return Response(406, 'Not Acceptable')
    
        body = body.encode('utf-8')
        headers = [('Content-Type', contentType),
                   ('Content-Length', len(body))]
        return Response(200, 'OK', headers, body)
    
    
    class Request:
      def __init__(self, method, target, version, headers, rfile):
        self.method = method
        self.target = target
        self.version = version
        self.headers = headers
        self.rfile = rfile
    
      @property
      def path(self):
        return self.url.path
    
      @property
      @lru_cache(maxsize=None)
      def query(self):
        return parse_qs(self.url.query)
    
      @property
      @lru_cache(maxsize=None)
      def url(self):
        return urlparse(self.target)
    
      def body(self):
        size = self.headers.get('Content-Length')
        if not size:
          return None
        return self.rfile.read(size)
    
    class Response:
      def __init__(self, status, reason, headers=None, body=None):
        self.status = status
        self.reason = reason
        self.headers = headers
        self.body = body
    
    class HTTPError(Exception):
      def __init__(self, status, reason, body=None):
        super()
        self.status = status
        self.reason = reason
        self.body = body
    
    
    if __name__ == '__main__':
      host = sys.argv[1]
      port = int(sys.argv[2])
      name = sys.argv[3]
    
      serv = MyHTTPServer(host, port, name)
      try:
        serv.serve_forever()
      except KeyboardInterrupt:
        pass

Ссылки по теме
--------------

*   [http.server модуль Python Standard Library](https://docs.python.org/3/library/http.server.html)
*   [Исходный код http.server на GitHub](https://github.com/python/cpython/blob/b16b4e45923f4e4dfd8e970ae4e6a934faf73b79/Lib/http/server.py)
*   [RFC7230 Message Syntax and Routing](https://tools.ietf.org/html/rfc7230)
*   [RFC7231 Semantics and Content](https://tools.ietf.org/html/rfc7231)
*   [RFC7232 Conditional Requests](https://tools.ietf.org/html/rfc7232)
*   [RFC7233 Range Requests](https://tools.ietf.org/html/rfc7233)
*   [RFC7234 Caching](https://tools.ietf.org/html/rfc7234)
*   [RFC7235 Authentication](https://tools.ietf.org/html/rfc7235)


