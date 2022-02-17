from time import time
from time import sleep
from cv2 import cv2
from os import listdir
import sys
import numpy as np
import mss
import pyautogui
import yaml

abrir_config = open("config.yaml", "r")
carregar_config = yaml.safe_load(abrir_config)
pyautogui.PAUSE = carregar_config["tempo_clique"]


def remover_prefixo(string, prefixo):
    if prefixo and string.startswith(prefixo):
        return string[len(prefixo):]
    return string


def remover_sufixo(string, sufixo):
    if sufixo and string.endswith(sufixo):
        return string[:-len(sufixo)]
    return string


def carregar_imagens(dir_path='./alvos/'):
    arquivos = listdir(dir_path)
    alvos = {}
    for arquivo in arquivos:
        path = remover_prefixo(dir_path, './') + arquivo
        alvos[remover_sufixo(arquivo, '.png')] = cv2.imread(path)
    return alvos

global off_x
off_x = 0

if carregar_config['qtd_monitores'] > 1:
  with mss.mss() as sct:
      off_x = 0
      if len(sct.monitors) > 1:
        monitor = sct.monitors[1]
        off_x = -monitor['width']

def print_screen():
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        sct_img = np.array(sct.grab(monitor))

    return sct_img[:, :, :3]


def posicoes(imagem, confianca=0.7, screenshot=None):
    if screenshot is None:
        screenshot = print_screen()

    resultado = cv2.matchTemplate(screenshot, imagem, cv2.TM_CCOEFF_NORMED)
    l = imagem.shape[1]
    a = imagem.shape[0]

    yloc, xloc = np.where(resultado >= confianca)

    retangulos = []

    for (x, y) in zip(xloc, yloc):
        retangulos.append([int(x), int(y), int(l), int(a)])
        retangulos.append([int(x), int(y), int(l), int(a)])

    retangulos, larguras = cv2.groupRectangles(retangulos, 1, 0.2)

    return retangulos


def mover(x, y, duracao=1):
    pyautogui.moveTo(x + off_x, y, duracao)

def scroll():
    commoms = posicoes(imagens['ammo'], confianca = 0.8)
    if (len(commoms) == 0):
        return

    x,y,w,h = commoms[len(commoms)-1]
    mover(x, y, 0.3)

    pyautogui.dragRel(0, -carregar_config['click_and_drag_amount'], duration=1, button='left')

def achou(imagem, confianca=0.7):
    return len(posicoes(imagens[imagem], confianca=confianca)) > 0

def clicar(img, timeout=3, confianca=0.7, velocidade=1):
    inicio = time()
    expirou = False
    while(not expirou):
        encontrou = posicoes(img, confianca=confianca)

        if(len(encontrou) == 0):
            expirou = time() - inicio > timeout
            continue

        x, y, l, a = encontrou[0]

        clicar_x = x+l/2
        clicar_y = y+a/2

        mover(clicar_x, clicar_y, velocidade)
        pyautogui.click()

        return True

    return False


def login():
    print("Tentando logar....")

    if (achou('conectar_metamask')):
      clicar(imagens['conectar_metamask'], timeout=0.1)
      sleep(10)

    if (achou('assinar')):
      clicar(imagens['assinar'], timeout=0.1)
      sleep(8)

    if (achou('play')):
      clicar(imagens['play'], timeout=0.1)
      sleep(4)

    return


def jogar():
    timeout = 5
    inicio = time()
    expirou = False
    while(not expirou):
        encontrou = posicoes(imagens["fight"], confianca=0.98)

        if(len(encontrou) == 0):
            expirou = time() - inicio > timeout
            continue
        else:
            clicar(imagens["fight"], timeout=0.5, confianca=0.98, velocidade=0.3)
            pyautogui.click()

            if achou('full', confianca=0.95):
              clicar(imagens["startboss"])
              expirou = True

    return

global bossAtual
bossAtual = 0

def bossatual():
  global bossAtual

  for bossnum in range(10):
    if achou('boss' + str(bossnum + 1), confianca=0.9):
      if bossAtual != bossnum + 1:
        print('Detectado Boss: ' + str(bossnum + 1))
        bossAtual = bossnum + 1

  return

def jogando():
    if achou('confirm'):
      clicar(imagens['confirm'])

    if achou('confirmtime', confianca=0.6):
      clicar(imagens['confirmtime'], confianca=0.6)

    if achou('confirmsurrender'):
      clicar(imagens['confirmsurrender'])

    bossatual()

    if achou('boss11', confianca=0.95):
      print('Chegou no boss 11, clicando surrender')
      clicar(imagens['surrenderbtn'])

    if achou('empty', confianca=0.9):
      print('Todas as naves quebraram, retornando ao inicio')
      clicar(imagens['retorno'])
      return True

    return False


def main():
    global imagens
    global bossAtual
    imagens = carregar_imagens()

    print('--- Bot iniciando!')
    print('--- Se puder doar algum token pra ajudar humilde!')
    print('--- 0xaB2E35923e09D270808f412b6869319c85686570')

    sleep(carregar_config["tempo_comecar_programa"])

    ultimo = {
        "login": 0,
        "atualizar": 0,
        "scrolls": 0
    }

    while True:
        agora = time()

        if agora - ultimo["login"] > 60:
            ultimo["login"] = agora
            login()

        if achou('error'):
          clicar(imagens["error"])
        
        if achou('full', confianca=0.95):
          print('Todas as naves já estavam selecionadas')
          clicar(imagens["startboss"])
        else:
          if achou('fight', confianca=0.98):
            print('Encontrou naves disponíveis...')
            jogar()
          else:
            if bossAtual == 10 and achou('noships', confianca=0.95) is False:
              clicar(imagens["startboss"])
            else:
              scroll()
              ultimo["scrolls"] += 1
              
              if (ultimo["scrolls"] >= carregar_config['qtd_scrolls']):
                ultimo["scrolls"] = 0
                clicar(imagens["startboss"])

        jogando()

        sys.stdout.flush()


if __name__ == '__main__':

    main()
