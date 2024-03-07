Давайте создадим веб -сервер.Часть 3.
============================================================================================================================


> _“Мы познаем больше, когда нужно изобретать » - Piagege

В [Part 2](6_Web_server/README2.md) Вы создали минималистичный сервер WSGI, который мог бы обрабатывать основные HTTP GET -запросы.И я задал вам вопрос: «Как вы можете заставить ваш сервер обрабатывать более одного запроса за раз?»В этой статье вы найдете ответ.Итак, пристегитесь и переключитесь на высокую передачу.Вы отправляетесь в скоростное путешествие.Подготовьте свой Linux, Mac OS X (или любая система \*nix) и Python. Весь исходный код из статьи доступен на[GitHub](https://github.com/rspivak/lsbaws/blob/master/part3/).

Сначала давайте вспомним, как выглядит очень простой веб -сервер и что должен сделать сервер для обслуживания запросов клиента.Сервер, который вы создали в [Часть 1]  и [часть 2] это итеративный сервер, который обрабатывает один запрос клиента за раз.Он не может принять новое соединение до тех пор, пока не завершит обработку текущего запроса клиента.Некоторые клиенты могут быть недовольны этим, потому что им придется ждать в очереди, а для занятых серверов линия может быть слишком длинной.

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_it1.png)

Вот код итеративного сервера[webserver3a.py](https://github.com/rspivak/lsbaws/blob/master/part3/webserver3a.py):
```py
#####################################################################
# Iterative server - webserver3a.py                                 #
#                                                                   #
# Tested with Python 2.7.9 & Python 3.4 on Ubuntu 14.04 & Mac OS X  #
#####################################################################
import socket

SERVER_ADDRESS = (HOST, PORT) = '', 8888
REQUEST_QUEUE_SIZE = 5


def handle_request(client_connection):
    request = client_connection.recv(1024)
    print(request.decode())
    http_response = b"""\
HTTP/1.1 200 OK

Hello, World!
"""
    client_connection.sendall(http_response)


def serve_forever():
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket.bind(SERVER_ADDRESS)
    listen_socket.listen(REQUEST_QUEUE_SIZE)
    print('Serving HTTP on port {port} ...'.format(port=PORT))

    while True:
        client_connection, client_address = listen_socket.accept()
        handle_request(client_connection)
        client_connection.close()

if __name__ == '__main__':
    serve_forever()
```    

Чтобы наблюдать за своим сервером, обрабатывая только один запрос клиента за раз, немного измените сервер и добавьте 60 -секундную задержку после отправки ответа клиенту.Изменение - это всего лишь одна строка, чтобы сообщить серверному процессу спать в течение 60 секунд.

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_it2.png)

А вот код спящего сервера [webserver3b.py](https://github.com/rspivak/lsbaws/blob/master/part3/webserver3b.py):
```py
#########################################################################
# Iterative server - webserver3b.py                                     #
#                                                                       #
# Tested with Python 2.7.9 & Python 3.4 on Ubuntu 14.04 & Mac OS X      #
#                                                                       #
# - Server sleeps for 60 seconds after sending a response to a client   #
#########################################################################
import socket
import time

SERVER_ADDRESS = (HOST, PORT) = '', 8888
REQUEST_QUEUE_SIZE = 5


def handle_request(client_connection):
    request = client_connection.recv(1024)
    print(request.decode())
    http_response = b"""\
HTTP/1.1 200 OK

Hello, World!
"""
    client_connection.sendall(http_response)
    time.sleep(60)  # sleep and block the process for 60 seconds


def serve_forever():
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket.bind(SERVER_ADDRESS)
    listen_socket.listen(REQUEST_QUEUE_SIZE)
    print('Serving HTTP on port {port} ...'.format(port=PORT))

    while True:
        client_connection, client_address = listen_socket.accept()
        handle_request(client_connection)
        client_connection.close()

if __name__ == '__main__':
    serve_forever()

```

Запустите сервер с:

    $ python webserver3b.py

Теперь откройте новое окно терминала и запустите команду _curl_. Вы должны мгновенно увидеть _«Hello, World!»_ Строка напечатается на экране:
```
$ curl http://localhost:8888/hello
Hello, World!
```
И без промедления откройте второе окно терминала и вновь запустите  команду _curl_:

    $ curl http://localhost:8888/hello

Если вы сделали это в течение 60 секунд, то второй _curl_ не должен сразу что-то вывести на экран, а просто должен замереть. Сервер не будет отвечать на новые запросы на своем стандартном выводе. Вот как это выглядит на моем Mac (окно в правом нижнем углу, выделенном в желтом цвете, показывает вторую  команду _curl_, ожидающую, когда соединение будет принято сервером):

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_it3.png)

После того, как вы подождали достаточно долго (более 60 секунд), вы должны увидеть первое завершение _curl_ и второе _curl_ выводящее _ «Hello, World!» _ На экране, затем оно повесит 60 секунд, а затем завершится:

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_it4.png)

Смысл такого способа обработки в том, что сервер заканчивает обслуживание первого запроса клиента _curl_, а затем начинает обрабатывать второй запрос только после простоя в течение 60 секунд.Все это происходит последовательно или итеративно, за один шаг или в нашем случае один запрос клиента, за один раз.

Давайте немного поговорим о связи между клиентами и серверами.Чтобы две программы могли общаться друг с другом по сети, они должны использовать сокет (как розетку и вилку). И вы видели это как в [Part 1]и [Part 2]. Но что такое сокет?

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_it_socket.png)

A _socket_ является абстракцией конечной точки связи и позволяет вашей программе общаться с другой программой, используя файловые дескрипторы.В этой статье я буду говорить конкретно о сокетах TCP/IP на Linux/Mac OS X. Важным понятием для понимания является _socket pair_ TCP.

> Пара сокетов  _socket pair_ для TCP-соединения представляет собой кортеж из четырех точек, который идентифицирует две конечные точки TCP-соединения: локальный IP-адрес, локальный порт, внешний IP-адрес и внешний порт. Пара сокетов уникально идентифицирует каждое соединение TCP в сети.Два значения, которые идентифицируют каждую конечную точку, IP -адрес и номер порта, часто называют _socket_.[1](#fn-1)

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_it_socketpair.png)

Итак, кортеж {10.10.10.2:49152, 12.12.12.3:8888} - это пара, которая уникально идентифицирует две конечные точки соединения TCP на клиенте, а кортеж {12.12.12.3:8888, 10.10.10.2:49152}Пара сокетов, которая уникально идентифицирует одни и те же две конечные точки соединения TCP на сервере.Два значения, которые идентифицируют конечную точку сервера соединения TCP, IP -адрес 12.12.12.3 и порт 8888, в данном случае называются сокетом (то же самое относится и к конечной точке клиента).

Стандартная последовательность, через которую обычно проходит сервер, чтобы создать сокет и начать принимать клиентские подключения, является следующим:

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_it_server_socket_sequence.png)

1.  Сервер создает сокет TCP/IP.Это делается со следующим утверждением в Python:
    
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
2.  Сервер может установить некоторые параметры сокета (это необязательно, но вы можете видеть, что приведенный выше код сервера делает именно это для повторного использования одного и того же адреса снова и снова, если вы решите убить и повторно запустить сервер опять).
    
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
3.  Затем сервер связывает адрес.Функция _bind_ присваивает локальный адрес протокола в сокет.С TCP вызов _BIND_ позволяет указать номер порта, IP -адрес, как вместе, так и вообще не указывать.[1](#fn-1)
    
        listen_socket.bind(SERVER_ADDRESS)
    
4.  Затем сервер активирует прослушивание сокета
    
        listen_socket.listen(REQUEST_QUEUE_SIZE)
    

Метод _Listen_ вызывается только на сервере _servers_ .Он говорит ядру, что он должен принять входящие запросы на соединение для этого сокета.

После того, как это сделано, сервер начинает принимать клиентские подключения по одному подключению за раз в цикле.При наличии соединения, вызов _Accept_ возвращает подключенную клиентскую сокет-розетку. Затем сервер считывает данные запроса из подключенного клиентского сокета-вилки, печатает данные на своем стандартном выходе и отправляет сообщение обратно клиенту.Затем сервер закрывает клиентское соединение, и он снова готов принять новое клиентское соединение.

Вот что клиент должен сделать, чтобы общаться с сервером по TCP/IP:

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_it_client_socket_sequence.png)

Вот пример кода для клиента, чтобы подключиться к вашему серверу, отправить запрос и распечатать ответ:
```py
  import socket

 # create a socket and connect to a server
 sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
 sock.connect(('localhost', 8888))

 # send and receive some data
 sock.sendall(b'test')
 data = sock.recv(1024)
 print(data.decode())
```

После создания сокета клиент должен подключиться к серверу.Это сделано с помощью вызова _connect_:

    sock.connect(('localhost', 8888))

Клиент должен только предоставить удаленный IP -адрес или имя хоста и номер удаленного порта сервера для подключения.

Вы, вероятно, заметили, что клиент не вызывает _bind_ и _accept_. Клиенту не нужно звонить _bind_, потому что клиент не заботится о локальном IP -адресе и локальном номере порта. Стек TCP/IP в ядре автоматически назначает локальный IP -адрес и локальный порт, когда клиент вызывает _connect_. Локальный порт называется _ephemeral port_, то есть недолговечный порт.
![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_it_ephemeral_port.png)

Порт на сервере, который идентифицирует общепринятую для данного порта службу, к которой клиент подключается, называется _well-skell_ Port (например, 80 для HTTP и 22 для SSH).Запустите свой Python Shell и сделайте клиентское соединение с сервером, который вы запускаете на Localhost, и посмотрите, какой эфемерный порт присваивает ядро к созданному вами сокету (запустите сервер [webserver3a.py](https://github.com/rspivak/lsbaws/blob/master/part3/webserver3a.py) or [webserver3b.py](https://github.com/rspivak/lsbaws/blob/master/part3/webserver3b.py) Прежде чем попробовать следующий пример):
```py
>>> import socket
>>> sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
>>> sock.connect(('localhost', 8888))
>>> host, port = sock.getsockname()[:2]
>>> host, port
('127.0.0.1', 60589)
```

В приведенном выше случае ядро ​​назначило сокету эфемерный порт 60589

Есть некоторые другие важные понятия, которые мне нужно быстро осветить, прежде чем перейти дальше - это концепции _process_ и _file descriptor_.

Что такое процесс? _Process_ - это всего лишь экземпляр выполняемой программы.Например, когда код сервера выполняется, он загружается в память, а экземпляр этой выполняющейся программы называется процессом.Ядро записывает кучу информации о процессе - его идентификатор процесса будет одним из примеров - чтобы отслеживать его.Когда вы запускаете свой итеративный сервер [webserver3a.py](https://github.com/rspivak/lsbaws/blob/master/part3/webserver3a.py) или [webserver3b.py](https://github.com/rspivak/lsbaws/blob/master/part3/webserver3b.py) Вы запускаете только один процесс.

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_it_server_process.png)

Запустите сервер [webserver3b.py](https://github.com/rspivak/lsbaws/blob/master/part3/webserver3b.py) в окне терминала:

    $ python webserver3b.py

И в другом окне терминала запустите команду _PS_, чтобы получить информацию об этом процессе:

    $ ps | grep webserver3b | grep -v grep
    7182 ttys003    0:00.04 python webserver3b.py

Команда _PS_ показывает, что вы действительно запустили только один процесс Python _Webserver3b_. Когда процесс создается, ядро присваивает ему идентификатор процесса, PID. В UNIX у каждого пользовательского процесса также есть родитель, который, в свою очередь, имеет свой собственный идентификатор процесса, называемый родительским идентификатором процесса, или PPID для краткости.Я предполагаю, что вы запускаете оболочку Bash по умолчанию, и когда вы запускаете сервер, новый процесс создается с помощью PID, а его родительский PID устанавливается на PID оболочки Bash.

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_it_ppid_pid.png)

Попробуйте это и убедитесь сами, как все это работает.Снова запустите свой Python Shell, который создаст новый процесс, а затем получите пид процесса оболочки Python и PID PID (PID вашей оболочки Bash), используя [os.getpid()](https://docs.python.org/2.7/library/os.html#os.getpid) и [os.getppid()](https://docs.python.org/2.7/library/os.html#os.getppid) системные вызовы. Затем в другом окне терминала запустите команду _PS_ и GREP для PPID (родительский идентификатор процесса, который в моем случае равен 3148).На скриншоте ниже вы можете увидеть пример отношения между родителями и детьми между процессом оболочки моего ребенка Python и процессом Parent Bash Shell на моем Mac OS X:

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_it_pid_ppid_screenshot.png)

Еще одна важная концепция, которую нужно знать, - это концепция _file descriptor_.Так что же такое дескриптор файла?_File Descriptor_-это неотрицательное целое число, которое ядро назначает процессу, когда он открывает существующий файл, создает новый файл или когда он создает новый сокет. Вы, наверное, слышали, что в Unix все является файлом. Ядро относится к открытым файлам процесса с помощью дескриптора файла. Когда вам нужно прочитать или написать файл, вы идентифицируете его с дескриптором файла.Python дает вам объекты высокого уровня для борьбы с файлами (и соктетами), и вам не нужно использовать дескрипторы файлов напрямую, чтобы идентифицировать файл, но под капотом, именно так файлы и гнезда идентифицируются в Unix: по их целочисленному дескриптору файла.

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_it_process_descriptors.png)

По умолчанию оболочка UNIX присваивает файловый дескриптор 0 - стандартному вводу процесса, файловый дескриптор 1 — стандартному выводу процесса, а файловый дескриптор 2 — стандартной ошибке.

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_it_default_descriptors.png)

Как я упоминал ранее, даже несмотря на то, что Python предоставляет вам для работы файл или подобный файлу объект высокого уровня, вы всегда можете использовать метод fileno() для объекта, чтобы получить файловый дескриптор, связанный с файлом. Вернемся к своей оболочке Python, чтобы увидеть, как вы можете это сделать:
```py
>>> import sys
>>> sys.stdin
<open file '<stdin>', mode 'r' at 0x102beb0c0>
>>> sys.stdin.fileno()
0
>>> sys.stdout.fileno()
1
>>> sys.stderr.fileno()
2
```

И, работая с файлами и розетками в Python, вы обычно используете объект/сокет высокого уровня, но могут быть времена, когда вам нужно напрямую использовать дескриптор файла.Вот пример того, как вы можете написать строку на стандартный вывод, используя [write](https://docs.python.org/2.7/library/os.html#os.write) Системный вызов, который принимает дескриптор файла (как целое число) как параметр:
```
>>> import sys
>>> import os
>>> res = os.write(sys.stdout.fileno(), 'hello\n')
hello
```

И вот интересная часть, которая больше не должна быть удивлением для вас, потому что вы уже знаете, что все является файлом в UNIX - в вашем сокете также есть дескриптор файла, связанный с ним. Опять же, когда вы создаете гнездо в Python, вы возвращаете объект, а не неотрицательное целое число, но вы всегда можете получить прямой доступ к дескриптору целочисленного файла сокета с помощью метода _fileno()_, который я упоминал ранее.
```py
>>> import socket
>>> sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
>>> sock.fileno()
3
```

Еще одна вещь, которую я хотел упомянуть: вы заметили, что во втором примере итеративного сервера [webserver3b.py](https://github.com/rspivak/lsbaws/blob/master/part3/webserver3b.py), когда Серверный процесс спал в течение 60 секунд, вы все равно могли бы подключиться к серверу со второй командой _curl_? Конечно, Curl сразу ничего не выдал и просто висел там, но почему сервер в тот момент не принимал соединение, и клиент не был сразу отклонен, а вместо этого смог подключиться к серверу ? Ответом на этот вопрос является метод прослушивания объекта сокета и его аргумент BACKLOG, который я назвал в коде REQUEST_QUEUE_SIZE. Аргумент BACKLOG определяет размер очереди в ядре для входящих запросов на соединение. Когда сервер [webserver3b.py](https://github.com/rspivak/lsbaws/blob/master/part3/webserver3b.py) Спал, вторая команда _curl_, которую вы запустили, смогла подключиться к серверу, потому что у ядра было достаточно места, доступного во входящей очереди запроса подключения для сокета сервера.

Увеличение аргумента BACKLOG не превращает ваш сервер волшебным образом в сервер, который может обрабатывать несколько клиентских запросов одновременно, важно иметь достаточно большой параметр backlog для занятых серверов, чтобы вызову принятия не приходилось ждать нового соединения, которое должно быть установлено, но может сразу же схватить новое соединение с очереди и без промедления начать обработку запроса клиента.

Ух-ух! Вы прошли большой путь. Давайте кратко подведем итог тому, что вы узнали (или освежили, если для вас это все основы) на данный момент.

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_checkpoint.png)

> *   Итеративный сервер
> * Последовательность создания сокетов сервера (сокет, привязка, прослушивание, принятие)
> * Последовательность создания подключения клиента (сокет, подключение)
> * Пара сокетов
> * Сокет
> * Эфемерный порт и известный порт
> * Процесс
> * Идентификатор процесса (PID), родительский идентификатор процесса (PPID) и отношения родительского ребенка.
> * Файловые дескрипторы
> * Значение аргумента BACKLOG метода listen

  
Теперь я готов ответить на вопрос из [Часть 2]: «Как заставить свой сервер обрабатывать более одного запроса за раз?» Или, «Как создать параллельный сервер?»

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_conc2_service_clients.png)

Самый простой способ написать параллельный сервер в Unix - использовать [fork()](https://docs.python.org/2.7/library/os.html#os.fork) системный вызов.

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_fork.png)

Вот код вашего нового   параллельного сервера [webserver3c.py](https://github.com/rspivak/lsbaws/blob/master/part3/webserver3c.py), которые могут обрабатывать несколько запросов клиентов одновременно (как В нашем примере итеративного сервера [webserver3b.py](https://github.com/rspivak/lsbaws/blob/master/part3/webserver3b.py) каждый потомок процесса спит в течение 60 секунд):

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_it2.png)
```py
###########################################################################
# Concurrent server - webserver3c.py                                      #
#                                                                         #
# Tested with Python 2.7.9 & Python 3.4 on Ubuntu 14.04 & Mac OS X        #
#                                                                         #
# - Child process sleeps for 60 seconds after handling a client's request #
# - Parent and child processes close duplicate descriptors                #
#                                                                         #
###########################################################################
import os
import socket
import time

SERVER_ADDRESS = (HOST, PORT) = '', 8888
REQUEST_QUEUE_SIZE = 5


def handle_request(client_connection):
    request = client_connection.recv(1024)
    print(
        'Child PID: {pid}. Parent PID {ppid}'.format(
            pid=os.getpid(),
            ppid=os.getppid(),
        )
    )
    print(request.decode())
    http_response = b"""\
HTTP/1.1 200 OK

Hello, World!
"""
    client_connection.sendall(http_response)
    time.sleep(60)


def serve_forever():
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket.bind(SERVER_ADDRESS)
    listen_socket.listen(REQUEST_QUEUE_SIZE)
    print('Serving HTTP on port {port} ...'.format(port=PORT))
    print('Parent PID (PPID): {pid}\n'.format(pid=os.getpid()))

    while True:
        client_connection, client_address = listen_socket.accept()
        pid = os.fork()
        if pid == 0:  # child
            listen_socket.close()  # close child copy
            handle_request(client_connection)
            client_connection.close()
            os._exit(0)  # child exits here
        else:  # parent
            client_connection.close()  # close parent copy and loop over

if __name__ == '__main__':
    serve_forever()
```    

Прежде чем погрузиться и обсудить, как работает _fork_, попробуйте и посмотрите сами, что сервер действительно может обрабатывать несколько запросов клиента одновременно, в отличие от его итерационных аналогов [webserver3a.py](https://github.com/rspivak/lsbaws/blob/master/part3/webserver3a.py) и [webserver3b.py](https://github.com/rspivak/lsbaws/blob/master/part3/webserver3b.py).З апустите сервер в командной строке с:

    $ python webserver3c.py

И попробуйте те же две команды _curl_, которые вы пробовали ранее с итеративным сервером, и убедитесь сами, что теперь, даже если дочерний процесс сервера спит в течение 60 секунд после обслуживания запроса клиента, это не влияет на других клиентов, потому что они обслуживается разными и полностью независимыми процессами. Вы должны увидеть свои команды _curl_ Вы можете продолжать запускать столько команд _curl_, сколько захотите (ну, почти столько, сколько вы хотите :), и все они выдадут ответ сервера _ «Привет, мир» _ сразу и без какой -либо заметной задержки. Попробуй это.

Самый важный момент, чтобы понять о [fork ()](https://docs.python.org/2.7/library/os.html#os.fork), - это то, что вы вызываете _fork_ один раз, но он возвращается дважды: один раз в родительском процесс и один раз в дочернем процессе.К огда вы разбираетесь в новом процессе, идентификатор процесса, возвращаемый в дочерний процесс, равен 0. Когда _fork_ возвращает в родительском процессе, он возвращает PID потомка.

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_conc2_how_fork_works.png)

Я до сих пор помню, насколько я был очарован _fork_, когда я впервые прочитал об этом и попробовал это. Это выглядело как волшебство для меня. Здесь я читал последовательный код, а затем «Бум!»: Код клонировал себя, и теперь было два экземпляра того же кода, работающего одновременно. Я думал, что это было не что иное, как волшебство, серьезно.

Когда родительский процесс создает новый дочерний процесс, дочерний процесс получает копию файловых дескрипторов родителя:
![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_conc2_shared_descriptors.png)

Вы, вероятно, заметили, что родительский процесс в приведенном выше коде закрыл клиентское соединение:
```
else:  # parent
    client_connection.close()  # close parent copy and loop over
```

Итак, почему дочерний процесс по -прежнему может читать данные из клиентского сокета, если его родитель закрыт - сидит на той же самой розетке? Ответ на картинке выше. Ядро использует подсчеты ссылки на дескриптор, чтобы решить, закрыть ли розетку или нет.Он закрывает гнездо только тогда, когда его количество ссылок на дескриптор становится 0. Когда ваш сервер создает дочерний процесс, ребенок получает копию дескрипторов файлов родителей, а ядро увеличивает количество ссылок для этих дескрипторов.В случае одного родителя и одного ребенка количество ссылок дескрипторов будет 2 для сокета клиента, и когда родительский процесс в приведенном выше коде закрывает сокет подключения клиента, он просто уменьшает его ссылки, который становится 1, не достаточно мал, чтобыпривести к закрытию ядра.Дочерний процесс также закрывает дубликатную копию родителя _listen \ _socket_, поскольку ребенок не заботится о принятии новых клиентских соединений, он заботится только о обработке запросов из установленного клиентского соединения:

    listen_socket.close()  # close child copy

Я расскажу о том, что произойдет, если вы не закроете дублирующие дескрипторы позже в статье.

Как вы можете видеть из исходного кода вашего параллельного сервера, единственная роль родительского процесса сервера теперь — принять новое клиентское соединение, создать новый дочерний процесс для обработки этого клиентского запроса и вернуться в цикл для принятия другого клиентского соединения, и ничего более.. Родительский процесс сервера не обрабатывает запросы клиентов — это делают его дочерние процессы.

Немного в сторону. Что это значит, когда мы говорим, что два события одновременны?

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_conc2_concurrent_events.png)

Когда мы говорим, что два события являются одновременными, мы обычно имеем в виду, что они случаются одновременно.Как сокращение, это определение в порядке, но вы должны помнить строгое определение:

> Два события - _concurrent_, если вы не можете сказать, просмотрев программу, которая произойдет первым.[2](#fn-2)

Опять же, пришло время вспомнить основные идеи и концепции, которые вы рассмотрели до этого

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_checkpoint.png)

> *   Самый простой способ написать параллельный сервер в Unix - это использовать [fork ()](https://docs.python.org/2.7/library/os.html#os.fork) 
> * Когда процесс разветвляет новый процесс, он становится родительским процессом для этого вновь разветвленного дочернего процесса.
> * Родительский и дочерний процессы используют одни и те же файловые дескрипторы после вызова  _fork_.
> * Ядро использует подсчет ссылок дескриптора, чтобы решить, закрыть ли файл/сокет или нет
> * Роль родительского процесса сервера: все, что он сейчас делает, это принимает новое соединение от клиента, создает дочерний процесс для обработки запроса клиента и выполняет цикл для принятия нового клиентского соединения.

  
LДавайте посмотрим, что произойдет, если вы не закроете повторяющиеся дескрипторы сокетов в родительском и дочернем процессах. Вот измененная версия одновременного сервера, где сервер не закрывает дублирующиеся дескрипторы, [webserver3d.py](https://github.com/rspivak/lsbaws/blob/master/part3/webserver3d.py):
```py
###########################################################################
# Concurrent server - webserver3d.py                                      #
#                                                                         #
# Tested with Python 2.7.9 & Python 3.4 on Ubuntu 14.04 & Mac OS X        #
###########################################################################
import os
import socket

SERVER_ADDRESS = (HOST, PORT) = '', 8888
REQUEST_QUEUE_SIZE = 5


def handle_request(client_connection):
    request = client_connection.recv(1024)
    http_response = b"""\
HTTP/1.1 200 OK

Hello, World!
"""
    client_connection.sendall(http_response)


def serve_forever():
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket.bind(SERVER_ADDRESS)
    listen_socket.listen(REQUEST_QUEUE_SIZE)
    print('Serving HTTP on port {port} ...'.format(port=PORT))

    clients = []
    while True:
        client_connection, client_address = listen_socket.accept()
        # store the reference otherwise it's garbage collected
        # on the next loop run
        clients.append(client_connection)
        pid = os.fork()
        if pid == 0:  # child
            listen_socket.close()  # close child copy
            handle_request(client_connection)
            client_connection.close()
            os._exit(0)  # child exits here
        else:  # parent
            # client_connection.close()
            print(len(clients))

if __name__ == '__main__':
    serve_forever()
```

Запустить сервер с:

    $ python webserver3d.py

Используйте Curl для подключения к серверу:

    $ curl http://localhost:8888/hello
    Hello, World!

Хорошо, Curl напечатал ответ от параллельного сервера, но не завершил работу и продолжает висеть. .Что здесь происходит?Сервер больше не спит в течение 60 секунд: его дочерний процесс активно обрабатывает запрос клиента, закрывает клиентское соединение и выходит, но клиент _curl_ по -прежнему не завершается.

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_conc3_child_is_active.png)

Так почему же _curl_ не завершается?Причина - дубликаты файловых дескрипторов. Причина — дубликаты файловых дескрипторов. Когда дочерний процесс закрыл клиентское соединение, ядро ​​уменьшило счетчик ссылок этого клиентского сокета, и этот счетчик стал равен 1 Дочерний процесс сервера завершился, но клиентский сокет не был закрыт ядром, поскольку счетчик ссылок для этого дескриптора сокета не был равен 0., и в результате пакет завершения (называемый FIN на языке TCP/IP) не был отправлен клиенту, и клиент, так сказать, остался на линии. Есть еще одна проблема.Если ваш длительный сервер не закрывает дубликаты дескрипторов файлов, в конечном итоге закончатся доступные дескрипторы файлов:

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_conc3_out_of_descriptors.png)

Остановите свой сервер [webserver3d.py](https://github.com/rspivak/lsbaws/blob/master/part3/webserver3d.py) командой _control-c_ и проверьте ресурсы по умолчанию, доступные для вашего серверного процесса, настроенного вашей оболочкой, с помощью встроенной команды оболочки _Ulimit_:
```sh
$ ulimit -a
core file size          (blocks, -c) 0
data seg size           (kbytes, -d) unlimited
scheduling priority             (-e) 0
file size               (blocks, -f) unlimited
pending signals                 (-i) 3842
max locked memory       (kbytes, -l) 64
max memory size         (kbytes, -m) unlimited
open files                      (-n) 1024
pipe size            (512 bytes, -p) 8
POSIX message queues     (bytes, -q) 819200
real-time priority              (-r) 0
stack size              (kbytes, -s) 8192
cpu time               (seconds, -t) unlimited
max user processes              (-u) 3842
virtual memory          (kbytes, -v) unlimited
file locks                      (-x) unlimited
```


Как вы можете видеть выше, максимальное количество дескрипторов открытых файлов (_open files_), доступное для процесса сервера в моем поле Ubuntu, составляет 1024.

Теперь давайте посмотрим, как ваш сервер может закончить доступные файловые дескрипторы, если он не закрывает дублируемые дескрипторы.В существующем или новом окне терминала установите максимальное количество дескрипторов открытых файлов для вашего сервера 256:

    $ ulimit -n 256

Запустите сервер [webserver3d.py](https://github.com/rspivak/lsbaws/blob/master/part3/webserver3d.py) в том же терминале, где вы только что запустили команду _$ ulimit -n 256_:

    $ python webserver3d.py

и используйте следующий клиент [client3.py](https://github.com/rspivak/lsbaws/blob/master/part3/client3.py), чтобы протестировать сервер.
```
#####################################################################
# Test client - client3.py                                          #
#                                                                   #
# Tested with Python 2.7.9 & Python 3.4 on Ubuntu 14.04 & Mac OS X  #
#####################################################################
import argparse
import errno
import os
import socket


SERVER_ADDRESS = 'localhost', 8888
REQUEST = b"""\
GET /hello HTTP/1.1
Host: localhost:8888

"""


def main(max_clients, max_conns):
    socks = []
    for client_num in range(max_clients):
        pid = os.fork()
        if pid == 0:
            for connection_num in range(max_conns):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(SERVER_ADDRESS)
                sock.sendall(REQUEST)
                socks.append(sock)
                print(connection_num)
                os._exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Test client for LSBAWS.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--max-conns',
        type=int,
        default=1024,
        help='Maximum number of connections per client.'
    )
    parser.add_argument(
        '--max-clients',
        type=int,
        default=1,
        help='Maximum number of clients.'
    )
    args = parser.parse_args()
    main(args.max_clients, args.max_conns)
```
В новом окне терминала запустите Client3.py и скажите ему,  создать 300 одновременных подключений к серверу:

    $ python client3.py --max-clients=300

Достаточно скоро ваш сервер выдаст ошибку. Вот скриншот исключения на моей пк:

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_conc3_too_many_fds_exc.png)

Урок ясен - ваш сервер должен закрыть дублирующие дескрипторы. Но даже если вы закрываете дублирующие дескрипторы, вы еще не решили проблему, потому что есть другая проблема с вашим сервером, и эта проблема - зомби!

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_conc3_zombies.png)

Да, ваш код сервера на самом деле понасоздавал зомби. Посмотрим, как.Запустите свой сервер снова:

    $ python webserver3d.py

Запустите команду _curl_ в другом окне терминала:

    $ curl http://localhost:8888/hello

И теперь запустите команду _PS_, чтобы показать запущенные процессы Python.Это пример вывода _ps_ в моем   Ubuntu:
```
$ ps auxw | grep -i python | grep -v grep
vagrant   9099  0.0  1.2  31804  6256 pts/0    S+   16:33   0:00 python webserver3d.py
vagrant   9102  0.0  0.0      0     0 pts/0    Z+   16:33   0:00 \[python\] <defunct>
```

Вы видите вторую строку выше, где говорится, что статус процесса с PID 9102 — Z+, а имя процесса — __defunct__? Это наш зомби .Проблема с зомби в том, что вы не можете убить их.

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_conc3_kill_zombie.png)

Даже если вы попытаетесь убить зомби с помощью _$ kill -9_, они выживут. Попробуйте и убедитесь сами.

Что такое зомби в любом случае и почему наш сервер создает их?  _Zombie_ - Зомби — это процесс, который завершился, но его родитель не дождался его и еще не получил статус завершения. Когда дочерний процесс завершается раньше своего родительского, ядро ​​превращает дочерний процесс в зомби и сохраняет некоторую информацию о процессе, чтобы родительский процесс мог получить ее позже. Результат информации обычно представляет собой идентификатор процесса, статус завершения процесса и использование ресурса с помощью процесса.Итак, зомби служат цели, но если ваш сервер не позаботится об этих зомби, ваша система превратится в мусорку. Давайте посмотрим, как это происходит. Сначала остановите работающий сервер и в новом окне терминала используйте команду ulimit, чтобы установить максимальное количество пользовательских процессов на 400 (обязательно установите _open files_ на более высокую цифру, скажем, 500):

$ ulimit -u 400
$ ulimit -n 500

Запустите сервер [webserver3d.py](https://github.com/rspivak/lsbaws/blob/master/part3/webserver3d.py) в том же терминале, где вы только что запустили команду _$ ulimit -u 400_:

    $ python webserver3d.py

В новом окне терминала запустите [client3.py](https://github.com/rspivak/lsbaws/blob/master/part3/client3.py) и скажите ему создать 500 одновременных соединений с сервером:

    $ python client3.py --max-clients=500

И, опять же, достаточно скоро ваш сервер сломается с исключением **Oserror: ресурс временно недоступен** , когда он попытается создать новый дочерний процесс, но он не сможет, потому что он достиг предела для максимального количества потомков, которые  разрешено создавать. Вот скриншот исключения на моей пк:

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_conc3_resource_unavailable.png)

Как вы можете видеть, зомби создают проблемы для вашего   сервера, если он не позаботится о них. Вскоре я расскажу, как сервер должен решать эту проблему с зомби.

Давайте вернемся к основным моментам, которые вы рассмотрели до этого:

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_checkpoint.png)

> *   Если вы не закроете повторяющиеся дескрипторы, клиенты не завершат работу, поскольку клиентские соединения не будут закрыты.
> * Если вы не закрываете дублируемые дескрипторы, на вашем   сервере в конечном итоге закончится доступные дескрипторы файлов (_max open files_).
> * Когда вы создаете дочерний процесс, и он завершается, а родительский процесс не ждет его и не получает статус завершения, он становится зомби _zombie_.
> * Зомби должны что -то съесть, и, в нашем случае, это память. На вашем сервере в конечном итоге закончится доступные процессы (_max пользовательские процессы_), если он не позаботится о зомби.
> * Зомби нельзя убить, его нужно дождаться.

  
Итак, что вам нужно сделать, чтобы позаботиться о зомби? Вам необходимо изменить код сервера на _wait_ для зомби, чтобы получить статус завершения. Вы можете сделать это, изменив код своего сервера, чтобы вызвать [WAIT](https://docs.python.org/2.7/library/os.html#os.wait) .К сожалению, это далеко не идеально, потому что, если вы называете _wait_, и не существует прекращенного дочернего процесса, вызов _wait_ заблокирует ваш сервер, что эффективно предотвратит управление новым клиентским подключением.Есть ли другие варианты?Да, есть, и одним из них является комбинация _Signal Handler_ с системным вызовом _wait_.

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_conc4_signaling.png)

Вот как это работает.Когда дочерний процесс завершает работу, ядро ​​отправляет сигнал SIGCHLD. Родительский процесс может настроить обработчик сигнала для асинхронного уведомления об этом событии SIGCHLD., а затем он может дождаться, пока дочерний процесс получит статус завершения, тем самым не позволяя процессу-зомби остаться без внимания.

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part_conc4_sigchld_async.png)

Кстати, асинхронное событие означает, что родительский процесс не знает заранее, что событие произойдет.

Измените код вашего сервера, чтобы настроить обработчик событий _sigchld_ и _wait_ для завершенного потомка в обработчике событий.Код доступен в [webserver3e.py](https://github.com/rspivak/lsbaws/blob/master/part3/webserver3e.py) файле:
```
###########################################################################
# Concurrent server - webserver3e.py                                      #
#                                                                         #
# Tested with Python 2.7.9 & Python 3.4 on Ubuntu 14.04 & Mac OS X        #
###########################################################################
import os
import signal
import socket
import time

SERVER_ADDRESS = (HOST, PORT) = '', 8888
REQUEST_QUEUE_SIZE = 5


def grim_reaper(signum, frame):
    pid, status = os.wait()
    print(
        'Child {pid} terminated with status {status}'
        '\n'.format(pid=pid, status=status)
    )


def handle_request(client_connection):
    request = client_connection.recv(1024)
    print(request.decode())
    http_response = b"""\
HTTP/1.1 200 OK

Hello, World!
"""
    client_connection.sendall(http_response)
    # sleep to allow the parent to loop over to 'accept' and block there
    time.sleep(3)


def serve_forever():
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket.bind(SERVER_ADDRESS)
    listen_socket.listen(REQUEST_QUEUE_SIZE)
    print('Serving HTTP on port {port} ...'.format(port=PORT))

    signal.signal(signal.SIGCHLD, grim_reaper)

    while True:
        client_connection, client_address = listen_socket.accept()
        pid = os.fork()
        if pid == 0:  # child
            listen_socket.close()  # close child copy
            handle_request(client_connection)
            client_connection.close()
            os._exit(0)
        else:  # parent
            client_connection.close()

if __name__ == '__main__':
    serve_forever()
```
Запустите сервер:

    $ python webserver3e.py

Используйте curl, чтобы отправить запрос на измененный параллельный сервер:

    $ curl http://localhost:8888/hello

Посмотрите на сервер:

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_conc4_eintr.png)

Что сейчас произошло?Вызов _Accept_ не удался с ошибкой _EINTR_.

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_conc4_eintr_error.png)

Родительский процесс был заблокирован в вызове _accept_ при выходе дочернего процесса, что вызвало событие _sigchld_, которое, в свою очередь, активировало обработчик сигнала, и когда обработчик сигнала завершил системный вызов _accept_

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_conc4_eintr_accept.png)

Не волнуйтесь, хотя это довольно простая проблема.Все, что вам нужно сделать, это повторно запустить системный вызов _accept_.Вот измененная версия сервера [webserver3f.py](https://github.com/rspivak/lsbaws/blob/master/part3/webserver3f.py), которая обрабатывает эту проблему:
```
###########################################################################
# Concurrent server - webserver3f.py                                      #
#                                                                         #
# Tested with Python 2.7.9 & Python 3.4 on Ubuntu 14.04 & Mac OS X        #
###########################################################################
import errno
import os
import signal
import socket

SERVER_ADDRESS = (HOST, PORT) = '', 8888
REQUEST_QUEUE_SIZE = 1024


def grim_reaper(signum, frame):
    pid, status = os.wait()


def handle_request(client_connection):
    request = client_connection.recv(1024)
    print(request.decode())
    http_response = b"""\
HTTP/1.1 200 OK

Hello, World!
"""
    client_connection.sendall(http_response)


def serve_forever():
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket.bind(SERVER_ADDRESS)
    listen_socket.listen(REQUEST_QUEUE_SIZE)
    print('Serving HTTP on port {port} ...'.format(port=PORT))

    signal.signal(signal.SIGCHLD, grim_reaper)

    while True:
        try:
            client_connection, client_address = listen_socket.accept()
        except IOError as e:
            code, msg = e.args
            # restart 'accept' if it was interrupted
            if code == errno.EINTR:
                continue
            else:
                raise

        pid = os.fork()
        if pid == 0:  # child
            listen_socket.close()  # close child copy
            handle_request(client_connection)
            client_connection.close()
            os._exit(0)
        else:  # parent
            client_connection.close()  # close parent copy and loop over


if __name__ == '__main__':
    serve_forever()
```

Запустите обновленный сервер webserver3f.py:

    $ python webserver3f.py

Используйте Curl, чтобы отправить запрос на измененный параллельный сервер:

    $ curl http://localhost:8888/hello



Видите? Больше никаких исключений EINTR. Теперь убедитесь, что зомби больше нет и что ваш обработчик событий SIGCHLD с вызовом ожидания позаботился о завершенных дочерних элементах.Для этого просто запустите команду _PS_ и убедитесь, что больше нет процессов Python со статусом **Z+** (нет больше **Defunct** процессов). Отлично! Теперь чувствуем себя в безопасности без бегающих зомби.

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_checkpoint.png)

> *   Если форкнуть _fork_ потомка и не дождаться его, он становится _zombie_.
> * Используйте обработчик событий SIGCHLD, чтобы асинхронно ждать, пока завершенный дочерний элемент получит статус завершения.
> * При использовании обработчика событий вам нужно помнить, что системные вызовы могут быть прерваны, и вы должны быть готовы к этому сценарию

  
Пока все хорошо. Нет проблем, верно? Ну, почти.Попробуйте свой [webserver3f.py](https://github.com/rspivak/lsbaws/blob/master/part3/webserver3f.py) еще раз, но вместо того, чтобы сделать один запрос с _curl_ для [client3.py](https:///github.com/rspivak/lsbaws/blob/master/part3/client3.py) созданиете 128 одновременных соединений:

    $ python client3.py --max-clients 128

Теперь запустите команду _ps_

    $ ps auxw | grep -i python | grep -v grep

И посмотри, О, нет, зомби снова вернулись!
![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_conc5_zombies_again.png)

Что пошло не так на этот раз?Когда вы запустили 128 одновременных клиентов и установили 128 подключений, дочерние обработчики на сервере обрабатывали запросы и заканчивались почти в то же время, что привело к тому, что сигналы _sigchld_ отправлялись в родительский процесс. Проблема в том, что сигналы не поставлены в очередь, и ваш серверный процесс пропустил несколько сигналов, в результате чего несколько зомби остались без присмотра::

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_conc5_signals_not_queued.png)

Решение проблемы состоит в том, чтобы настроить обработчик событий _sigchld_, но вместо _wait_ используйте [waitpid](https://docs.python.org/2.7/library/os.html#os.waitpid)  с опцией WNOHANG в цикле, чтобы убедиться, что обо всех завершенных дочерних процессах позаботятся.. Вот измененный код сервера, [webserver3g.py](https://github.com/rspivak/lsbaws/blob/master/part3/webserver3g.py):
```
###########################################################################
# Concurrent server - webserver3g.py                                      #
#                                                                         #
# Tested with Python 2.7.9 & Python 3.4 on Ubuntu 14.04 & Mac OS X        #
###########################################################################
import errno
import os
import signal
import socket

SERVER_ADDRESS = (HOST, PORT) = '', 8888
REQUEST_QUEUE_SIZE = 1024


def grim_reaper(signum, frame):
    while True:
        try:
            pid, status = os.waitpid(
                -1,          # Wait for any child process
                 os.WNOHANG  # Do not block and return EWOULDBLOCK error
            )
        except OSError:
            return

        if pid == 0:  # no more zombies
            return


def handle_request(client_connection):
    request = client_connection.recv(1024)
    print(request.decode())
    http_response = b"""\
HTTP/1.1 200 OK

Hello, World!
"""
    client_connection.sendall(http_response)


def serve_forever():
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket.bind(SERVER_ADDRESS)
    listen_socket.listen(REQUEST_QUEUE_SIZE)
    print('Serving HTTP on port {port} ...'.format(port=PORT))

    signal.signal(signal.SIGCHLD, grim_reaper)

    while True:
        try:
            client_connection, client_address = listen_socket.accept()
        except IOError as e:
            code, msg = e.args
            # restart 'accept' if it was interrupted
            if code == errno.EINTR:
                continue
            else:
                raise

        pid = os.fork()
        if pid == 0:  # child
            listen_socket.close()  # close child copy
            handle_request(client_connection)
            client_connection.close()
            os._exit(0)
        else:  # parent
            client_connection.close()  # close parent copy and loop over

if __name__ == '__main__':
    serve_forever()
```
Запустить сервер:

    $ python webserver3g.py

Используйте тестовый клиент [client3.py](https://github.com/rspivak/lsbaws/blob/master/part3/client3.py):

    $ python client3.py --max-clients 128

И теперь убедитесь, что зомби больше нет.Ура!Жизнь хороша без зомби:)

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_conc5_no_zombies.png)

Поздравляю!Это было довольно долгое путешествие, но я надеюсь, что вам понравилось.Теперь у вас есть собственный простой параллельный сервер, и код может служить основой для вашей дальнейшей наработки в направлении веб -сервера производственного цикла.

Я оставлю вам в качестве упражнения обновить сервер WSGI из части 2 и сделать его параллельным. Вы можете найти модифицированную версию [здесь](https://github.com/rspivak/lsbaws/blob/master/part3/webserver3h.py).Но посмотрите на мой код только после того, как вы реализовали свою собственную версию. У вас есть вся необходимая информация для этого. Так что иди и просто сделай это :)

Что дальше?Как сказал Джош Биллингс,

> _“Будь как почтовая марка — прилепись к одной вещи, пока не доберешься до финиша.”_

Начните с основ. Задайте вопрос тому, что вы уже знаете. И всегда копайте глубже.

![](https://ruslanspivak.com/lsbaws-part3/lsbaws_part3_dig_deeper.png)

> _“Если вы изучите только методы, вы будете привязаны к методам. Но если вы изучите принципы, вы сможете разработать свои собственные методы..” —Ralph Waldo Emerson_

