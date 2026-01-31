"""
Generate FIGfonts from unifont glyghs.

Unifont glyghs is licensed under dual-licensed under the OFL1.1 and GPL2.0,
see assets/unifont/COPYING.txt.
The source code is licensed under GPL2.0. See the notice below and LICENSE.txt.
The generated fonts are licensed under OFL1.1. See fig-fonts/LICENSE.txt.

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
import json
from os import path
from dataclasses import dataclass, field

UNIFONT_VERSION = "17.0.03"
CURRENT_DIR = path.dirname(path.abspath(__file__)) + "/" # ./
INPUT_FILE = CURRENT_DIR + "assets/unifont/unifont.hex"
INPUT_SP_CHINESE_CH_FILE = CURRENT_DIR + "assets/level-1.txt" # 一级字, 3500 个
OUTPUT_JSON = CURRENT_DIR + "assets/unifont/unifont.json"
FLF_SCOPE_ARR = [
    #[0x0020, 0x007E], # Part of "Controls and basic latin". The necessary FIGfont
    #[0x4E00, 0x9FFF], # 基本汉字，太多了，不用，使用 INPUT_SP_CHINESE_CH_FILE 生成
    [0x3000, 0x3002], [0x3007, 0x300B], [0x3010, 0x3011], # 部分中文符号和标点
    [0xFF0C, 0xFF0C], # ，  逗号
    [0xFF01, 0xFF01], # ！  感叹号
    [0xFF1F, 0xFF1F], # ？  问号
    [0xFF1A, 0xFF1B], # ：；  冒号 分号
    [0x2014, 0x2014], # —  破折号
    [0x2026, 0x2026] # …  省略号
]

dic = {} # This dict is to store the hex file
HEX2BIN = {"0":"0000", "1":"0001", "2":"0010", "3":"0011",
    "4":"0100", "5":"0101", "6":"0110", "7":"0111",
    "8":"1000", "9":"1001", "A":"1010", "B":"1011",
    "C":"1100", "D":"1101", "E":"1110", "F":"1111"}


## Get Simplified Chinese characters required to generate
for ch in open(INPUT_SP_CHINESE_CH_FILE, "r", encoding="utf-8"):
    ch_code = ord(ch.replace("\n", ""))
    FLF_SCOPE_ARR += [[ch_code, ch_code]]
# FLF_SCOPE_ARR won't be changed anymore. So I regard it as an constant variable


## Write .hex to dict
for line in open(INPUT_FILE, "r"):
    tmparr:list = line.replace("\n", "").split(":")
    dic.update({int("0x"+tmparr[0],base=16): tmparr[1]})


## Write JSON
def generate_json(output_json = OUTPUT_JSON):
    """
    Generate JSON file of unifont glyphs.

    :param output_json: The output JSON file
    """
    with open(output_json, "w", encoding="utf-8") as f:
        f.write(json.dumps(dic, indent=0))


def generate_bin_dic(flf_scope_arr:list=FLF_SCOPE_ARR) -> dict:
    """
    Generate the 0-1 strings for unifont glyphs in `flf_scope_arr`
    
    :param flf_scope_arr: A list of unicode scopes.\n\n\
        The list should contain several lists of scope.\n\n\
        e.g. `[[0x4E00,0x9FFF],[0x0020,0x0020]]`.
    :type flf_scope_arr: list
    :return: A dict like `{unicode: [lists of 0-1 string]}`.\n\n\
        Every string in the list corresponds a line.\n\n\
        e.g. `{1:["01010101","01010101","01010101",...],...}`
    :rtype: dict
    """
    ret_dic = {}
    for scope in flf_scope_arr+[[0x0020,0x007E]]:
        for i in range(scope[0], scope[1]+1):
            bin_str = ""
            hex_ch:str = dic[i]
            line_break_cnt = 4 # when to break(based on hex digits) # hex_ch=64, width:2ch (e.g: 乐)
            if(len(hex_ch) == 32): line_break_cnt = 2 # width:1ch (e.g: A)
            cnt = 0 # how many hex digits have read for each line?
            # begin convert hex to bin string
            for ch in hex_ch:
                cnt += 1
                bin_str += HEX2BIN[ch]
                if(cnt % line_break_cnt == 0 and cnt != len(hex_ch)): # line break
                    # not:last line(if don't use `and cnt != len(hex_ch)`, the FIGcharacter's end will be like: `{data}@\n@@\n` ,but expected `{data}@@\n`)
                    bin_str += "\n"
            # end convert
            ret_dic.update({i: bin_str.split("\n")})
    ret_dic.update( # The "missing character".
        {0:["00000000", # FFFD:0000007E665A5A7A76767E76767E0000
            "00000000",
            "00000000",
            "01111110",
            "01100110",
            "01011010",
            "01011010",
            "01111010",
            "01110110",
            "01110110",
            "01111110",
            "01110110",
            "01110110",
            "01111110",
            "00000000",
            "00000000"]})
    return ret_dic



def is_ne_ch(code_num:int) -> bool: # is necessary character?
    if(code_num >= 0x0020 and code_num <= 0x007E): return True
    if(code_num in [0x00C4,0x00D6,0x00DC,0x00E4,0x00F6,0x00FC,0x00DF]): return True
    return False


# FIGchars generate

@dataclass
class Figfont:
    """
    The Figfont class, used to generate FIGfont file.\n\n\
    Except the attribute starts with `font_`, all the attributes should be place in header\
    are as follows:\n\n\
    - Height
    - Baseline
    - Max_Length
    - Old_Layout
    - Comment_Lines
    - Print_Direction
    - Full_Layout
    - Codetag_Count
    """
    height:int
    baseline:int
    max_length:int
    font_dic:dict = field(default_factory=dict)
    font_header:str = ""
    font_comment:str = """File is generated by unif-sp-ch-fig.
Convert unifont <https://unifoundry.com/unifont/> (especially for Chinese characters) to FIGfont file.
License of this FIGfont and unifont is SIL OPEN FONT LICENSE Version 1.1(OFL 1.1), see LICENSE.txt."""
    old_layout:int = -1 # none
    comment_lines:int = 3
    print_direction:int = 0 # left-to-right
    full_layout:int = 0 # none
    codetag_count:int = 0

class Generator_figfont:
    """
    The class to include all the FIGfont generator.\n\n\
    Each function in this class starts with `ch_` corresponds a font generator.\n\n\
    Note the "generator" here don't means `generator` in python.

    :param bin_dic: The 0-1 string of FIGcharacters. Generated by `generate_bin_dic()`
    :type bin_dic: dict
    """
    def _attribute_str(self, fig:Figfont) -> str:
        return " ".join(
            list(map(
                lambda attribute: str(fig.__dict__[attribute]), # object.__dict__ will return a dict of all of the attributes in the class
                self.font_header_attribute_arrange)
            )
        )
    
    def __init__(self, bin_dic:dict):
        self.bin_dic = bin_dic
        self.font_header_attribute_arrange = ["height", "baseline", "max_length", "old_layout", "comment_lines", "print_direction", "full_layout", "codetag_count"]
        iter_bin_dic = iter(bin_dic)
        self.codetag_cnt = 0
        while True:
            try:
                i = next(iter_bin_dic)
                if(is_ne_ch(i)): continue
                self.codetag_cnt += 1
            except StopIteration:
                break
    
    def ch_filling(self, ch_fill="\u2588\u2588", ch_blank="  ") -> Figfont: # ch_fill = "██" 
        """
        The normal font. Will only replace the 0-1 with other to generate.\n\n\
        In order to make sure the font isn't strange, the length of `ch_fill` & `ch_blank` must be 2.
        
        :param ch_fill: Which character to replace "1" in the 0-1 string.
        :type ch_fill: str
        :param ch_blank: Which character to replace "0" in the 0-1 string.
        :type ch_blank: str
        :return: A `Figfont` object. See Figfont.
        :rtype: Figfont
        """
        ret_fig = Figfont(height=16, baseline=14, max_length=32+2)
        iter_bin_dic = iter(self.bin_dic)
        while True:
            try:
                i = next(iter_bin_dic)
                ret_fig.font_dic.update(
                    {i: list(map(
                        lambda line:line.replace("1",ch_fill).replace("0",ch_blank),
                        self.bin_dic[i]
                    ))}
                )
            except StopIteration:
                break
        ret_fig.codetag_count = self.codetag_cnt
        ret_fig.font_header = f"flf2a$ {self._attribute_str(ret_fig)}\n{ret_fig.font_comment}\n"
        return ret_fig
    
    def ch_half_block(self, corres:dict[str,dict[str, str]]={}) -> Figfont:
        """
        Just like `ch_filling`, but combine 2 lines to 1 line.\n\n\
        The most common used.
        
        :param corres: Optional. Like `{"0":{"0":" ","1":"▄"},"1":{"0":"▀","1":"█"}}`\n\n\
            The first 0,1 corresponds the first line is filled or not.\n\n\
            The second 0,1 corresponds the second line.
        :type corres: dict
        :return: A `Figfont` object. See Figfont.
        :rtype: Figfont
        """
        # upper = "▀"; lower = "▄"; full = "█"
        UPPER_BLOCK = "\u2580"
        LOWER_BLOCK = "\u2584"
        FULL_BLOCK = "\u2588"
        if corres!={}: CH_CORRES = corres
        else: CH_CORRES = {"0":{"0":" ","1":LOWER_BLOCK},"1":{"0":UPPER_BLOCK,"1":FULL_BLOCK}}
        ret_fig = Figfont(height=8, baseline=7, max_length=16+2)
        iter_bin_dic = iter(self.bin_dic)
        while True:
            try:
                i = next(iter_bin_dic)
                font_whole = []
                for line in range(0,16,2):
                    font_line = "".join(list(map(
                        lambda f1,f2: CH_CORRES[f1][f2],
                        self.bin_dic[i][line], self.bin_dic[i][line+1] # the 0-1 from every 2 lines
                    )))
                    font_whole.append(font_line)
                ret_fig.font_dic.update({i: font_whole})
            except StopIteration:
                break
        ret_fig.codetag_count = self.codetag_cnt
        ret_fig.font_header = f"flf2a$ {self._attribute_str(ret_fig)}\n{ret_fig.font_comment}\n"
        return ret_fig
    
    def ch_braille_dots(self) -> Figfont:
        """
        "Braille" font, show the glyph in "braille".\n\n\
        Idea is inspired by drawille <https://github.com/asciimoo/drawille>.
        
        :return: A `Figfont` object. See Figfont.
        :rtype: Figfont
        """
        # braille like this: ⣿
        # every dot marked as:
        # 0 3
        # 1 4
        # 2 5
        # 6 7
        # like binary, when the dot is visible, the number on that place is 1 or 0 => 2**i or 0
        ## for example: [0,1,1,0,1,1,0,0]
        ## 2**1 + 2**2 + 2**4 + 2**5 = 54 = 0x36
        # 0x2800 plus that number is the unicode ordinal of target braille
        ## [0,1,1,0,1,1,0,0] => \u2836 => ⠶
        ## ==>
        ## 0 0
        ## 1 1
        ## 1 1
        ## 0 0
        # note that \u2800 is `⠀`, it is "BRAILLE PATTERN BLANK", not a common space
        BRAIL_OFFSET = [ # [line + ?, column + ?]
            [0, 0], #0
            [1, 0], #1
            [2, 0], #2
            [0, 1], #3
            [1, 1], #4
            [2, 1], #5
            [3, 0], #6
            [3, 1]  #7
        ]
        ret_fig = Figfont(height=4, baseline=4, max_length=8+2)
        iter_bin_dic = iter(self.bin_dic)
        while True:
            try:
                i = next(iter_bin_dic)
                font_whole = []
                for line in range(0,16,4):
                    font_length = len(self.bin_dic[i][line])
                    font_line = ""
                    for col in range(0, font_length, 2):
                        res_ordinal = 0x2800
                        for dot in range(0, 8):
                            # [[1 or 0]] * 2**dot
                            res_ordinal += int(self.bin_dic[i][line+BRAIL_OFFSET[dot][0]][col+BRAIL_OFFSET[dot][1]]) * (1 << dot)
                        font_line += chr(res_ordinal)
                    font_whole.append(font_line)
                ret_fig.font_dic.update({i: font_whole})
            except StopIteration:
                break
        ret_fig.font_comment += "\nThis font's idea is inspired by drawille <https://github.com/asciimoo/drawille>."
        ret_fig.comment_lines += 1
        ret_fig.codetag_count = self.codetag_cnt
        ret_fig.font_header = f"flf2a$ {self._attribute_str(ret_fig)}\n{ret_fig.font_comment}\n"
        return ret_fig
    def ch_box_drawing(self, style="bold", split_block=True) -> Figfont:
        """
        Use box drawing characters to draw every block.\n\n\
        **Notes**: 撇、捺越多的字，字越密(Unifont 16*16 像素而言)，生成的字形越抽象。\n  
        撇捺较多时，参数 `split_block=True`(default) 会好一些；\n  
        字形较密(e.g `槽`在 `True` 时右半声旁有点抽象)时 `False` 会好一些。

        :param style: The style(flavour) of box drawing. \n\n\
            The expected values are: `bold`, `normal`, `double`, `borad`. See below. \n\n\
            ```
        "bold":  ["━","┏","┓","┗","┛","┣","┫","┳","┻","╋","┃"],
        "normal":["─","┌","┐","└","┘","├","┤","┬","┴","┼","│"],
        "double":["═","╔","╗","╚","╝","╠","╣","╦","╩","╬","║"],
        "borad": ["─","╭","╮","╰","╯","├","┤","┬","┴","┼","│"]
            ```
        :type style: str
        :param split_block: Split the blocks. \n\n\
            ```
        True:  ┏━┳━┓
               ┗━┻━┛
        False: ┏━━━┓
               ┗━━━┛
            ```
        :type split_block: bool
        :return: A `Figfont` object. See Figfont.
        :rtype: Figfont
        """
        BT = { #BOX_DRAWING_TABLE
            "bold":  ["\u2501","\u250f","\u2513","\u2517","\u251b","\u2523","\u252b","\u2533","\u253b","\u254b","\u2503"],
            "normal":["\u2500","\u250c","\u2510","\u2514","\u2518","\u251c","\u2524","\u252c","\u2534","\u253c","\u2502"],
            "double":["\u2550","\u2554","\u2557","\u255a","\u255d","\u2560","\u2563","\u2566","\u2569","\u256c","\u2551"],
            "borad": ["\u2500","\u256d","\u256e","\u2570","\u256f","\u251c","\u2524","\u252c","\u2534","\u253c","\u2502"]
            #"bold":  ["━","┏","┓","┗","┛","┣","┫","┳","┻","╋","┃"],
            #"normal":["─","┌","┐","└","┘","├","┤","┬","┴","┼","│"],
            #"double":["═","╔","╗","╚","╝","╠","╣","╦","╩","╬","║"],
            #"borad": ["─","╭","╮","╰","╯","├","┤","┬","┴","┼","│"]
            ##########  0 , 1 , 2 , 3 , 4 , 5 , 6 , 7 , 8 , 9 , 10
        }
        ret_fig = Figfont(height=17, baseline=15, max_length=33+2)
        iter_bin_dic = iter(self.bin_dic)
        if(style not in BT): # style not in BT.keys()
            raise ValueError(f"`style` agrument must be in {list(BT.keys())}")
        # Let me declare how the generator work, it's a bit complex.
        # There's a full glyph: (The unifont glyph is 16*16)
        ## ┏━┳━┳━┳━┳━┳━┳━┳━┳━┳━┳━┳━┳━┳━┳━┳━┓
        ## ┣━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━┫
        ## ┣━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━┫
        ## ┣━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━┫
        ## ┣━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━┫
        ## ┣━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━┫
        ## ┣━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━┫
        ## ┣━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━┫
        ## ┣━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━┫
        ## ┣━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━┫
        ## ┣━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━┫
        ## ┣━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━┫
        ## ┣━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━┫
        ## ┣━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━┫
        ## ┣━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━┫
        ## ┣━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━╋━┫
        ## ┗━┻━┻━┻━┻━┻━┻━┻━┻━┻━┻━┻━┻━┻━┻━┻━┛
        ## 16+1 lines, 16*2+1 columns.
        ## The '+1' corresponds the last line and the last column.
        ## The '*2' due to `━` after the connecting character(like `┏`).
        # For each 0,1 in the bin_dic, we only consider the connecting character.
        # `1`,`2`,`3`,`4` is the area of block, `|`,`-`,`+` is the area of box drawing characters.
        # We are considering the `+` in the image below:
        ## 2 | 1
        ## --+--
        ## 3 | 4
        # The block is filled with the "0","1" from the bin_dic.
        # The block area is given value:
        ## 2^1|2^0
        ## ---+---
        ## 2^2|2^3
        # If we calculate the value (in binary) as i, we'll use the `boxt[i]` value
        #split_block=True; <=> False.
        ## 0b0000:
        ### 0| 0     0| 0
        ### -  - <=> -  -
        ### 0| 0     0| 0
        ## 0b0001:
        ### 0| 1     0| 1
        ### -┗━- <=> -┗━-
        ### 0| 0     0| 0
        ## 0b0010:
        ### 1| 0     1| 0
        ### -┛ - <=> -┛ -
        ### 0| 0     0| 0
        ## 0b0011:
        ### 1| 1     1| 1
        ### -┻━- <=> -━━-
        ### 0| 0     0| 0
        ## 0b0100:
        ### 0| 0     0| 0
        ### -┓ - <=> -┓ -
        ### 1| 0     1| 0
        ## 0b0101:
        ### 0| 1     0| 1
        ### -╋━- <=> -╋━-
        ### 1| 0     1| 0
        ## 0b0110:
        ### 1| 0     1| 0
        ### -┫ - <=> -┃ -
        ### 1| 0     1| 0
        ## 0b0111:
        ### 1| 1     1| 1
        ### -╋━- <=> -┏━-
        ### 1| 0     1| 0
        ## 0b1000:
        ### 0| 0     0| 0
        ### -┏━- <=> -┏━-
        ### 0| 1     0| 1
        ## 0b1001:
        ### 0| 1     0| 1
        ### -┣━- <=> -┃ -
        ### 0| 1     0| 1
        ## 0b1010:
        ### 1| 0     1| 0
        ### -╋━- <=> -╋━-
        ### 0| 1     0| 1
        ## 0b1011:
        ### 1| 1     1| 1
        ### -╋━- <=> -┓ -
        ### 0| 1     0| 1
        ## 0b1100:
        ### 0| 0     0| 0
        ### -┳━- <=> -━━-
        ### 1| 1     1| 1
        ## 0b1101:
        ### 0| 1     0| 1
        ### -╋━- <=> -┛ -
        ### 1| 1     1| 1
        ## 0b1110:
        ### 1| 0     1| 0
        ### -╋━- <=> -┗━-
        ### 1| 1     1| 1
        ## 0b1111:
        ### 1| 1     1| 1
        ### -╋━- <=> -  -
        ### 1| 1     1| 1
        bs = BT[style]
        boxt = []
        if(split_block):
            #      0b0000,0b0001=1,    0b0010=2,  0b0011=3,    0b0100=4,  0b0101=5,    0b0110=6,  0b0111=7,    0b1000=8,    0b1001=9,    0b1010=10,   1b1011=11,   0b1100=12,   0b1101=13,   0b1110=14,   0b1111=15
            boxt = ["  ", bs[3]+bs[0], bs[4]+" ", bs[8]+bs[0], bs[2]+" ", bs[9]+bs[0], bs[6]+" ", bs[9]+bs[0], bs[1]+bs[0], bs[5]+bs[0], bs[9]+bs[0], bs[9]+bs[0], bs[7]+bs[0], bs[9]+bs[0], bs[9]+bs[0], bs[9]+bs[0]]
        else:
            #      0b0000,0b0001=1,    0b0010=2,  0b0011=3,    0b0100=4,  0b0101=5,    0b0110=6,   0b0111=7,    0b1000=8,    0b1001=9,    0b1010=10,   1b1011=11, 0b1100=12,   0b1101=13, 0b1110=14,   0b1111=15
            boxt = ["  ", bs[3]+bs[0], bs[4]+" ", bs[0]+bs[0], bs[2]+" ", bs[9]+bs[0], bs[10]+" ", bs[1]+bs[0], bs[1]+bs[0], bs[10]+" ",  bs[9]+bs[0], bs[2]+" ", bs[0]+bs[0], bs[4]+" ", bs[3]+bs[0], "  "]
        while True:
            try:
                i = next(iter_bin_dic)
                font_whole = []
                font_length = len(self.bin_dic[i][0])
                # In the loop, the position is given(if the position isn't accessible, the value is 0<=>"0"):
                ## line-1,col-1 | line-1,col
                ## -------------+-----------
                ##  line,col-1  |  line,col
                # The variable name:
                ## b | a
                ## --+--
                ## c | d
                for line in range(0,16+1): # 0->16
                    bi:list = self.bin_dic[i]
                    font_line = ""
                    for col in range(0, font_length+1): # 0->8 or 16
                        # The code is a whole shit... Please forgive me.
                        a=b=c=d=-1
                        if(line-1 < 0) :      a=b=0
                        if(col-1 < 0):      b=c=0
                        if(line > 15):      c=d=0
                        if(col>font_length-1):a=d=0
                        if(a==-1): a=int(bi[line-1][col])
                        if(b==-1): b=int(bi[line-1][col-1])
                        if(c==-1): c=int(bi[line][col-1])
                        if(d==-1): d=int(bi[line][col])
                        # end of this
                        font_line += boxt[a + b*2 + c*4 + d*8]
                    font_line = font_line.removesuffix(" ") # The end of the line is like `┏━┳━┓ `, We should remove the ` ` suffix
                    font_whole.append(font_line)
                ret_fig.font_dic.update({i: font_whole})
            except StopIteration:
                break
        ret_fig.codetag_count = self.codetag_cnt
        ret_fig.font_header = f"flf2a$ {self._attribute_str(ret_fig)}\n{ret_fig.font_comment}\n"
        return ret_fig


## To Binary String FigFont
def generate_flf(output_flf:str, fig_font:Figfont):
    """
    Generate FIGfont file.\n\n
    You're supposed to make sure the generated files are small enough to be read by the FIGdrivers.
    
    :param output_flf: Where the FIGfont file should be generate.
    :type output_flf: str
    :param fig_font: The Figfont instance object to generate FIGfont file.
    :type fig_font: Figfont
    """
    binary_str_file=open(output_flf, "w", encoding="utf-8")
    binary_str_file.write(fig_font.font_header)
    # begin required characters
    for i in range(0x0020, 0x007E+1):
        binary_str_file.write("@\n".join(fig_font.font_dic[i]) + "@@\n")
    for i in range(0, 7): #[0x00C4,0x00D6,0x00DC,0x00E4,0x00F6,0x00FC,0x00DF]
        binary_str_file.write("@\n"*(fig_font.height-1) + "@@\n")
    # end required characters
    # unrequired code tags(主要是中文字符)
    iter_font_dic = iter(fig_font.font_dic)
    while True:
        try:
            i = next(iter_font_dic)
            if(is_ne_ch(i)): continue # the necessary font, skip
            binary_str_file.write(f"{hex(i)} {chr(i)}\n" + "@\n".join(fig_font.font_dic[i]) + "@@\n")
        except StopIteration:
            break
    binary_str_file.close()


if __name__ == "__main__":
    default_bin_dic:dict = generate_bin_dic()
    font_generator = Generator_figfont(default_bin_dic)
    OUT_PREFIX = "fig-fonts/chinese_"
    CUROUT = CURRENT_DIR+OUT_PREFIX 

    font_solid_box_big = font_generator.ch_filling()
    font_solid_box_small = font_generator.ch_half_block()
    font_braille_dots = font_generator.ch_braille_dots()
    generate_flf(output_flf=CUROUT+"solid_box_big.flf", fig_font=font_solid_box_big)
    generate_flf(output_flf=CUROUT+"solid_box_small.flf", fig_font=font_solid_box_small)
    generate_flf(output_flf=CUROUT+"braille_dots.flf", fig_font=font_braille_dots)

    font_block_bold_split = font_generator.ch_box_drawing()
    font_block_bold = font_generator.ch_box_drawing(split_block=False)
    font_block_split = font_generator.ch_box_drawing(style="normal")
    font_block = font_generator.ch_box_drawing(style="normal", split_block=False)
    font_block_double_split = font_generator.ch_box_drawing(style="double")
    font_block_double = font_generator.ch_box_drawing(style="double", split_block=False)
    font_block_borad_split = font_generator.ch_box_drawing(style="borad")
    font_block_borad = font_generator.ch_box_drawing(style="borad", split_block=False)
    generate_flf(output_flf=CUROUT+"block_bold_split.flf", fig_font=font_block_bold_split)
    generate_flf(output_flf=CUROUT+"block_bold.flf", fig_font=font_block_bold)
    generate_flf(output_flf=CUROUT+"block_split.flf", fig_font=font_block_split)
    generate_flf(output_flf=CUROUT+"block.flf", fig_font=font_block)
    generate_flf(output_flf=CUROUT+"block_double_split.flf", fig_font=font_block_double_split)
    generate_flf(output_flf=CUROUT+"block_double.flf", fig_font=font_block_double)
    generate_flf(output_flf=CUROUT+"block_borad_split.flf", fig_font=font_block_borad_split)
    generate_flf(output_flf=CUROUT+"block_borad.flf", fig_font=font_block_borad)

    font_ascii_big = font_generator.ch_filling(ch_fill="#%", ch_blank=".,")
    font_ascii_small = font_generator.ch_half_block(corres={"0":{"0":" ","1":","},"1":{"0":"'","1":";"}})
    generate_flf(output_flf=CUROUT+"ascii_big.flf", fig_font=font_ascii_big)
    generate_flf(output_flf=CUROUT+"ascii_small.flf", fig_font=font_ascii_small)

