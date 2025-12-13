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
INPUT_SP_CHINESE_CH_FILE = CURRENT_DIR + "assets/gb2312-chinese.modify.txt"
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
            line_break_cnt = 4 # when to break(based on hex digits)
            if(len(hex_ch) == 32): line_break_cnt = 2
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
    
    def ch_half_block(self) -> Figfont:
        """
        Just like `ch_filling`, but combine 2 lines to 1 line.\n\n\
        The most common used.
        
        :return: A `Figfont` object. See Figfont.
        :rtype: Figfont
        """
        # upper = "▀"; lower = "▄"; full = "█"
        UPPER_BLOCK = "\u2580"
        LOWER_BLOCK = "\u2584"
        FULL_BLOCK = "\u2588"
        CH_CORRES = {"0":{"0":" ","1":LOWER_BLOCK},"1":{"0":UPPER_BLOCK,"1":FULL_BLOCK}}
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
        "Braille" font, show the glyph in "braille".
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
        binary_str_file.write("@\n"*15 + "@@\n")
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
    font_solid_box_big = font_generator.ch_filling()
    font_solid_box_small = font_generator.ch_half_block()
    font_braille_dots = font_generator.ch_braille_dots()
    generate_flf(output_flf=CURRENT_DIR+"fig-fonts/chinese_solid_box_big.flf", fig_font=font_solid_box_big)
    generate_flf(output_flf=CURRENT_DIR+"fig-fonts/chinese_solid_box_small.flf", fig_font=font_solid_box_small)
    generate_flf(output_flf=CURRENT_DIR+"fig-fonts/chinese_braille_dots.flf", fig_font=font_braille_dots)

