# -*- coding: utf-8 -*-
# Copyright 2013 James McCauley
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Simple datapath control framework for POX datapaths
----------------------------------------------------
Estrutura de controle de datapath simples para datapaths POX
"""

from pox.core import core
from pox.lib.ioworker.workers import *
from pox.lib.ioworker import *
from pox.lib.revent import *


# IOLoop for our IO workers
_ioloop = None

# Log
log = None


class CommandEvent (Event):
  #"Classe para comando do evento"
  """
  Event fired whenever a command is received
  ------------------------------------------
  Evento disparado sempre que um comando é recebido
  """
  
  def __init__ (self, worker, cmd):
    #"Inicialização"
    super(CommandEvent,self).__init__()
    self.worker = worker
    self.cmd = cmd
 
 
  @property
  def first (self):
    #"Define o primeiro"
    return self.cmd.strip().split()[0]

  @property["Define os argumentos"]
  def args (self):
    return self.cmd.strip().split()[1:]

   
  def __str__ (self):
    #"Retorna string"
    return "<%s: %s>" % (self.worker, self.cmd)


class ServerWorker (TCPServerWorker, RecocoIOWorker):
  #"Trabalhador-Servidor"
  """
  Worker to accept connections
  ----------------------------
  Trabalhador para aceitar conexão
  """
  pass
  #TODO: Really should just add this to the ioworker package.


class Worker (RecocoIOWorker):
  #"Classe trabalhador"
  """
  Worker to receive POX dpctl commands 
  ------------------------------------
  Trabalhador receber comandos POX dpctl
  """
  
  def __init__ (self, *args, **kw):
    #"Inicialização"
    super(Worker, self).__init__(*args, **kw)
    self._connecting = True
    self._buf = b''

   
  def _process (self, data):
    #"Processando"
    self._buf += data
    while '\n' in self._buf:
      fore,self._buf = self._buf.split('\n', 1)
      core.ctld.raiseEventNoErrors(CommandEvent, self, fore)

  
  def _handle_rx (self):
    #"lançamento RX"
    self._buf += self.read()
    self._process(self.read())

  
  def _exec (self, msg):
    #"Execução"
    msg.split()


class Server (EventMixin):
  #"Classe Servidor"
  """
  Listens on a TCP socket for control
  ------------------------------------
  Escuta em um soquete TCP para controle
  """
  _eventMixin_events = set([CommandEvent])

  
  def __init__ (self, port = 7791):
    #"Inicialização"
    w = ServerWorker(child_worker_type=Worker, port = port)
    self.server_worker = w
    _ioloop.register_worker(w)


def create_server (port = 7791):
  #"Criando o servidor"
  # Set up logging - Configurar o registo
  global log
  if not log:
    log = core.getLogger()

  # Set up IO loop - Configurar o loop IO
  global _ioloop
  if not _ioloop:
    _ioloop = RecocoIOLoop()
    #_ioloop.more_debugging = True
    _ioloop.start()

  c = Server(port = int(port))
  return c


def server (port = 7791):
  #"Define servidor"
  #"Faz c receber a função create_server com a porta"
  c = create_server(int(port))
    core.register("ctld", c)


def launch (cmd, address = None, port = 7791):
  #"Define lanaçamento; recebe cmd, endereco como vazio e porta"
  #"Se não tem endereço, faz address receber 127.0.0.1"
  #"importa socket"
  #"try: tenta criar conexão; se der erro, informa: Não foi possível conectar"
  #"try: tenta setar timeout e enviar cmd; se der erro, informa com um warn: Não responde"
  #"depois com uma exceção: Ao comunicar"
  core.quit()
  if not address:
    address = "127.0.0.1"
  import socket
  core.getLogger('core').setLevel(100)
  log = core.getLogger('ctl')
  try:
    s = socket.create_connection((address,port), timeout=2)
  except:
    log.error("Couldn't connect")
    return
  try:
    s.settimeout(2)
    s.send(cmd + "\n")
    d = s.recv(4096).strip()
    core.getLogger("ctl").info(d)
  except socket.timeout:
    log.warn("No response")
  except:
    log.exception("While communicating")
