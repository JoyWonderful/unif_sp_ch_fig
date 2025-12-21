import figlet from "./figlet.mjs";

const FONT_DIR = ["fonts/"];
const FONT_EXT = ".flf";
const FONT_LIST = [
    "chinese_ascii_small", "chinese_ascii_big", 
    "chinese_solid_box_small", "chinese_solid_box_big", "chinese_braille_dots"
];

// undefined: haven't parsed yet; 0: be parsing; 1: have already parsed
let is_parsed = [];
/** @type {HTMLSelectElement} */
var select_input;
/**@type {HTMLTextAreaElement} */
var str_input;
/**@type {HTMLInputElement} */
var width_input;
var txt_output = "";

var progInfo = {
    tmObj: 0,
    set: function(str) {
        var target = document.querySelector("aside#prog-info");
        if(target.hasAttribute("data-timeout")) {
            clearTimeout(this.tmObj);
            target.removeAttribute("data-timeout");
        }
        target.classList.add("active");
        target.innerHTML = str;
    },
    destroy: function(delay) {
        var target = document.querySelector("aside#prog-info");
        if(target.hasAttribute("data-timeout")) clearTimeout(this.tmObj);
        else target.setAttribute("data-timeout", "");
        this.tmObj = setTimeout(() => {target.classList.remove("active");target.removeAttribute("data-timeout")}, delay);
    }
}
async function get_font(id) {
    if(is_parsed[id] === 0) return;
    if(is_parsed[id] === 1) {generate_result(id, str_input.value, width_input.value); return;}
    select_input.disabled = true;
    progInfo.set("正在加载字体，请稍候");
    is_parsed[id] = 0;
    let res = await fetch(FONT_DIR+FONT_LIST[id]+FONT_EXT);
    let res_text = await res.text(); // raw flf font file
    figlet.parseFont(FONT_LIST[id], res_text);
    is_parsed[id] = 1;
    select_input.disabled = false;
    progInfo.set("加载完成");
    progInfo.destroy(3000);
    generate_result(id, str_input.value, width_input.value);
}
function generate_result(id, data, width) {
    if(is_parsed[id] === undefined) {get_font(id); return;}
    if(is_parsed[id] === 0) return;
    let area_output = document.querySelector("#output-area");
    txt_output = figlet.textSync(data, {font: FONT_LIST[id], width: width==""?undefined:width});
    area_output.innerText = txt_output;
}

function get_proper_width() {
    let new_test_el = document.createElement("span");
    new_test_el.style.fontFamily = "var(--monospace-font-family)";
    new_test_el.innerText = "a";

    document.body.appendChild(new_test_el);
    let ch_width = new_test_el.getBoundingClientRect().width;
    document.body.removeChild(new_test_el);
    let element_width = document.querySelector("#output-area").getBoundingClientRect().width;
    let generation_width = Math.round(element_width / ch_width);

    width_input.value = generation_width;
    generate_result(select_input.value, str_input.value, width_input.value);
}

window.addEventListener("DOMContentLoaded", () => {
    select_input = document.querySelector("select#input-font");
    width_input = document.querySelector("input#input-width");
    str_input = document.querySelector("textarea#input-text");

    for(let i = 0; i < FONT_LIST.length; i++) {
        let new_select_option = document.createElement("option");
        new_select_option.value = i;
        new_select_option.innerText = FONT_LIST[i];
        select_input.append(new_select_option);
    }
    select_input.addEventListener("input", ()=>{get_font(select_input.value)});
    str_input.addEventListener("input", ()=>{generate_result(select_input.value, str_input.value, width_input.value)});
    width_input.addEventListener("input", ()=>{generate_result(select_input.value, str_input.value, width_input.value)});
    document.getElementById("auto-get-width").addEventListener("click", get_proper_width);

    document.querySelector("button#copy").addEventListener("click", () => {
        navigator.clipboard.writeText(txt_output).then(
        () => { // success/fulfilled
            progInfo.set("已复制");
            progInfo.destroy(1000);
        },
        () => { // rejected
            try {
                let temparea = document.createElement("textarea");
                temparea.value = txt_output;
                document.body.appendChild(temparea);
                temparea.select();
                let res = document.execCommand("copy");
                temparea.remove();
                if(res) { // ok
                    progInfo.set("已复制");
                    console.log("Copy: execCommand");
                    progInfo.destroy(1000);
                }
                else throw new Error("Copy failed"); // fail
            }
            catch(err) {
                console.error("Copy failed");
                console.error(err);
                progInfo.set("复制失败<br>请检查是否有写入剪贴板权限，或手动复制");
                progInfo.destroy(1000);
            }
        });
    });
});
