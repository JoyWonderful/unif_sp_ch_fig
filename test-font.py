import pyfiglet
from pyperclip import copy
from os import get_terminal_size
font = pyfiglet.Figlet(font="chinese_solid_box_big", width=get_terminal_size().columns)

print(font.renderText("ok"))
while True:
    text = input("> ")
    font.width = float("inf")
    copy(font.renderText(text))
    font.width = get_terminal_size().columns
    print(font.renderText(text))