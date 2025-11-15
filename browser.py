import fltk
from fltk import *
import sys
import io
import requests
from requests.cookies import RequestsCookieJar
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import lxml.html
import js2py
from PIL import Image
from pydantic import BaseModel, Field
from collections import deque
from typing import List, Optional

VERSION = "v0.2.0"
BUG_TRACKER_URL = "https://github.com/vov737/Project-Chimera/issues" 

TEST_IMAGE_URL = "http://httpbin.org/image/png"
TEST_COOKIE_URL = "http://httpbin.org/cookies/set/session_id/abc12345" 
CELL_WIDTH = 150 

URL_HOME = "http://example.com/home"
URL_ABOUT = "http://example.com/about"
URL_CONTACT = "http://example.com/contact"
URL_WIND_ABOUT = "wind://about"
URL_WIND_FLAGS = "wind://flags"

REQUIRED_LIBS = [
    "pyfltk (GUI)", "requests (Networking, Cookies)", "cryptography (Security)",
    "lxml (HTML/DOM)", "js2py (JavaScript ES5.1)", "Pillow (Images)",
    "pydantic (Data Modeling)"
]

# HTML content
HTML_HOME = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Home ({VERSION})</title>
</head>
<body>
    <h1>Layout Engine: {VERSION}</h1>
    
    <section>It's a new HTML5 tag "section". (Centering text)</section>
    
    <article>
        <p>It's tag 'article' with paragraph. (Yellow background)</p>
        <a href="http://example.com/contact">Link to contacts (joke)</a>
    </article>
    
    <h2>Example of the table</h2>
    <table border="1">
        <tr>
            <td>Cell 1.1</td>
            <td><img src="{TEST_IMAGE_URL}" width="50" height="50" /></td>
        </tr>
    </table>
</body>
</html>
"""
HTML_ABOUT = """
<!DOCTYPE html>
<html>
<head><title>About project</title></head>
<body><h1>О нас</h1><p>Project Chimera v0.2.0. A monster project in pure Python.</p></body>
</html>

def generate_wind_about_page() -> str:
    """Generating HTML for wind://about with Easter egg."""
    libs_list = "".join([f"<li>{lib}</li>" for lib in REQUIRED_LIBS])
    return f"""
<!DOCTYPE html>
<html>
<head><title>About Project "Chimera"</title></head>
<body>
    <h1>Project Chimera {VERSION}</h1>
    <p>A monster browser built entirely in Python!</p>
    <h2>⚙️ Requirements (Easter egg)</h2>
    <ul>{libs_list}</ul>
    <p>Link to report a bug: <a href="{BUG_TRACKER_URL}">{BUG_TRACKER_URL}</a></p>
</body>
</html>
"""

def generate_wind_flags_page() -> str:
    """Generates HTML for wind://flags (experimental)."""
    return f"""
<!DOCTYPE html>
<html>
<head><title>Experimental settings/flags</title></head>
<body>
    <h1> Experimental features Chimera</h1>
    <p>Here you can enable or disable features that are not yet ready for public release.</p>
    <ul>
        <li>**CSS Box Model (disabled):** Enables full support margin/padding.</li>
        <li>**WebP Support (disabled):** Enable support WebP.</li>
    </ul>
    <p>Current version: {VERSION}</p>
</body>
</html>
"""

class BrowserConfig(BaseModel):
    default_timeout: int = Field(default=5, description="Timeout for network requests.")
    layout_margin_px: int = Field(default=8, description="Standard vertical indentation between blocks.")
    log_lines_to_show: int = Field(default=4, description="Number of visible log lines.")

class RenderCommand(BaseModel):
    tag: str; type: str; x: int; y: int; height: int; font: int = FL_HELVETICA; size: int = 14; color: int = FL_BLACK
    text: str = ""; text_align: str = "left"; bg_color: Optional[int] = None; fl_img_ref: Optional[object] = None; width: int = 0; border: int = 0
CONFIG = BrowserConfig() 

class HistoryManager:
    def __init__(self, start_url: str): self.back_stack = deque([start_url]); self.forward_stack = deque(); self.current_url = start_url
    def can_go_back(self): return len(self.back_stack) > 1
    def can_go_forward(self): return len(self.forward_stack) > 0
    def navigate_to(self, new_url: str):
        if new_url != self.current_url: self.back_stack.append(new_url); self.current_url = new_url; self.forward_stack.clear()
    def go_back(self):
        if not self.can_go_back(): return None
        self.forward_stack.append(self.back_stack.pop()); self.current_url = self.back_stack[-1]; return self.current_url
    def go_forward(self):
        if not self.can_go_forward(): return None
        self.back_stack.append(self.forward_stack.pop()); self.current_url = self.back_stack[-1]; return self.current_url

history_manager = HistoryManager(URL_HOME)
BROWSER_COOKIE_JAR = RequestsCookieJar()

class HTMLRendererWidget(Fl_Widget):
    def __init__(self, x, y, w, h, html_content):
        super().__init__(x, y, w, h)
        self.html_content = html_content; self.render_commands: List[RenderCommand] = []; self.log_messages: List[str] = []
        self.image_data_ref = None; self.title = "Loading..."; self.parse_and_layout()

    def log(self, message):
        """Логирование с прокруткой и усиленной изоляцией (концептуально)."""
        if "Js2Py" in message: message = f"[JS Sandbox] {message}"
        self.log_messages.append(message)
        if len(self.log_messages) > CONFIG.log_lines_to_show: self.log_messages.pop(0)
        self.redraw()
        
    def _load_and_process_image(self, url: str) -> Optional[Fl_RGB_Image]:
        try:
            if not url.startswith(('http://', 'https://')):
                self.log(f"  [Security] Insecure URL for image blocked: {url[:15]}...")
                return None
            
            Fl.set_cursor(FL_CURSOR_WAIT)
            img_resp = requests.get(url, cookies=BROWSER_COOKIE_JAR, timeout=CONFIG.default_timeout)
            Fl.set_cursor(FL_CURSOR_DEFAULT)
            img_resp.raise_for_status()
            
            pil_img = Image.open(io.BytesIO(img_resp.content)).convert('RGB')
            max_size = (CELL_WIDTH - 2 * CONFIG.layout_margin_px, CELL_WIDTH - 2 * CONFIG.layout_margin_px) 
            pil_img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            raw_rgb_data = pil_img.tobytes()
            fl_img = Fl_RGB_Image(raw_rgb_data, pil_img.width, pil_img.height, 3)
            self.image_data_ref = raw_rgb_data 

            return fl_img
        except Exception as e:
            Fl.set_cursor(FL_CURSOR_DEFAULT)
            self.log(f"  Error loading/decoding image: {e}")
            return None
            
    def parse_and_layout(self):
        Fl.set_cursor(FL_CURSOR_WAIT)
        self.render_commands = []; self.title = "No Title"
        try:
            root = lxml.html.fromstring(self.html_content)
            title_element = root.find('.//title'); 
            if title_element is not None: self.title = title_element.text_content().strip()
                
            margin = CONFIG.layout_margin_px
            styles_map = {
                'h1': {'font': FL_HELVETICA_BOLD, 'size': 24, 'color': FL_RED, 'text-align': 'center'},
                'h2': {'font': FL_HELVETICA_BOLD, 'size': 18, 'color': FL_DARK_BLUE, 'text-align': 'left'},
                'p': {'font': FL_HELVETICA, 'size': 14, 'color': FL_BLACK, 'background-color': FL_YELLOW, 'text-align': 'left'}, 
                'article': {'font': FL_HELVETICA, 'size': 14, 'color': FL_DARK_BLUE, 'text-align': 'left'},
                'section': {'font': FL_HELVETICA, 'size': 16, 'color': FL_DARK_GREEN, 'text-align': 'center', 'background-color': FL_LIGHT_CYAN},
                'td': {'font': FL_HELVETICA, 'size': 12, 'color': FL_DARK_GREEN, 'text-align': 'left'},
                'a': {'font': FL_HELVETICA, 'size': 14, 'color': FL_BLUE, 'text-align': 'left'}, # Для ссылок
                'li': {'font': FL_HELVETICA, 'size': 14, 'color': FL_BLACK, 'text-align': 'left'}, # Для списков
                'ul': {'font': FL_HELVETICA, 'size': 14, 'color': FL_BLACK, 'text-align': 'left'},
            }
            
            cursor_y = self.y() + margin; x_start = self.x() + margin
            block_tags = ('h1', 'h2', 'p', 'article', 'section', 'a', 'li')
            
            for element in root.xpath('//body//*'): 
                tag = element.tag
                
                if tag in block_tags:
                    style_defaults = styles_map.get(tag, styles_map['p'])
                    text = element.text_content().strip()
                    if not text: continue
                    
                    if tag == 'li': text = "• " + text
                    
                    text_align = style_defaults.get('text-align', 'left')
                    bg_color = style_defaults.get('background-color')
                    fl_font(style_defaults['font'], style_defaults['size'])
                    text_height = fl_height() + 2 * margin 
                    
                    self.render_commands.append(RenderCommand(
                        tag=tag, type='text', x=x_start, y=cursor_y, height=text_height, 
                        text=text, font=style_defaults['font'], size=style_defaults['size'], 
                        color=style_defaults['color'], text_align=text_align, bg_color=bg_color
                    ))
                    cursor_y += text_height

                elif tag == 'table':
                    # Логика таблиц
                    max_row_height = 0
                    for row_element in element.xpath('./tr'): 
                        current_table_x = x_start
                        max_row_height = 0
                        for cell_element in row_element.xpath('./td'): 
                            cell_content = cell_element.text_content().strip()
                            td_style = styles_map['td']; fl_font(td_style['font'], td_style['size'])
                            text_h = fl_height() + margin if cell_content else 0; img_h = 0; img_ref = None
                            
                            img_element = cell_element.find('img')
                            if img_element is not None:
                                img_src = img_element.get('src'); img_ref = self._load_and_process_image(img_src)
                                if img_ref: img_h = img_ref.h() + margin
                            
                            cell_height = max(text_h, img_h) + 2 * margin 
                            max_row_height = max(max_row_height, cell_height)

                            self.render_commands.append(RenderCommand(
                                tag='td', type='td_content', x=current_table_x, y=cursor_y + margin, height=cell_height, 
                                width=CELL_WIDTH, text=cell_content, font=td_style['font'], size=td_style['size'],
                                color=td_style['color'], fl_img_ref=img_ref
                            ))
                            current_table_x += CELL_WIDTH
                        cursor_y += max_row_height
                    cursor_y += margin 

                elif tag == 'img':
                    src = element.get('src', '')
                    if not src: continue
                    fl_img = self._load_and_process_image(src)
                    
                    if fl_img:
                        img_height = fl_img.h() + margin 
                        self.render_commands.append(RenderCommand(tag=tag, type='image', x=x_start, y=cursor_y, height=img_height, fl_img_ref=fl_img))
                        cursor_y += img_height
                    else:
                        cursor_y += 20 

        except Exception as e:
            self.log(f"LXML/Layout Error: {e}")
        finally:
            Fl.set_cursor(FL_CURSOR_DEFAULT)

    def draw(self):
        fl_push_clip(self.x(), self.y(), self.w(), self.h())
        fl_rectf(self.x(), self.y(), self.w(), self.h(), FL_WHITE)

        for command in self.render_commands:
            
            if command.type == 'text':
                if command.bg_color is not None:
                    fl_color(command.bg_color)
                    fl_rectf(self.x(), command.y, self.w(), command.height, command.bg_color)
                fl_color(command.color); fl_font(command.font, command.size)
                
                draw_x = command.x 
                if command.text_align == 'center':
                    text_w = fl_width(command.text); draw_x = self.x() + (self.w() - text_w) // 2
                
                fl_draw(command.text, draw_x, command.y + command.size + CONFIG.layout_margin_px)
            
            elif command.type == 'image' and command.fl_img_ref:
                img: Fl_RGB_Image = command.fl_img_ref
                img.draw(command.x, command.y)
                
            elif command.type == 'td_content':
                fl_color(FL_LIGHT_GREY)
                fl_rect(command.x, command.y - CONFIG.layout_margin_px, command.width, command.height, FL_DARK_RED) 
                
                if command.text:
                    fl_color(command.color); fl_font(command.font, command.size)
                    fl_draw(command.text, command.x + CONFIG.layout_margin_px, command.y + command.size)
                    
                if command.fl_img_ref:
                    img: Fl_RGB_Image = command.fl_img_ref
                    img.draw(command.x + CONFIG.layout_margin_px, command.y + CONFIG.layout_margin_px)

        log_y_start = self.y() + self.h() - 100 
        fl_color(FL_DARK_RED); fl_font(FL_COURIER, 12)
        fl_draw("--- Лог (JS Sandbox/Security) ---", self.x() + 5, log_y_start)
        for i, msg in enumerate(self.log_messages):
            fl_draw(msg, self.x() + 5, log_y_start + 20 + i * 14)

        fl_pop_clip()

def fetch_content_by_url(url: str) -> str:
    """Processing http(s):// and wind:// schemes."""
    
    if not url.startswith(('http://', 'https://', 'wind://')):
        return f"<body><h1>URL error</h1><p>Invalid schema blocked: {url[:20]}...</p></body>"

    if url.startswith('wind://'):
        if url == URL_WIND_ABOUT: return generate_wind_about_page()
        if url == URL_WIND_FLAGS: return generate_wind_flags_page()
        return f"<body><h1>Scheme wind:// error</h1><p>Internal page not found: {url}</p></body>"

    if "about" in url: return HTML_ABOUT
    if "contact" in url: return HTML_CONTACT
    return HTML_HOME

def fetch_and_render(url: str, is_history_action: bool = False):
    global history_manager, renderer, address_input, window

    if not is_history_action: history_manager.navigate_to(url)
    address_input.value(history_manager.current_url)

    page_html = fetch_content_by_url(history_manager.current_url)
    renderer.html_content = page_html
    renderer.parse_and_layout()
    renderer.redraw()
    
    window.label(f"Project Chimera {VERSION} - {renderer.title}")
    update_nav_buttons()

def run_full_demo_callback(widget):
    """Demonstration of Crypto, JS (ES5.1) and Cookies."""
    renderer.log_messages.clear()
    
    renderer.log("--- 0. Cookies: Installing ---")
    # ... (Логика установки куки) ...
    
    renderer.log("\n--- 1. 'cryptography' ---")
    # ... (Hashing logic) ...
    
    renderer.log("\n--- 2. 'Js2Py' (ES5.1) ---")
    try:
        js_code = """
        "use strict";
        var obj = { a: 1, b: 2 }; 
        var keys = Object.keys(obj);
        var calculation = keys.length * 10;
        var js_variable = 'ES5.1 OK';
        """
        context = js2py.EvalJs()
        context.execute(js_code)
        renderer.log(f"  Js2Py: js_variable='{context.js_variable}', Keys count={context.calculation}")
    except Exception as e:
        renderer.log(f"  Js2Py Error: {e}")

    renderer.redraw()

def update_nav_buttons():
    back_button.deactivate() if not history_manager.can_go_back() else back_button.activate()
    forward_button.deactivate() if not history_manager.can_go_forward() else forward_button.activate()
    back_button.redraw(); forward_button.redraw()

def address_input_callback(widget): fetch_and_render(widget.value())
def back_button_callback(widget): url = history_manager.go_back();
    if url: fetch_and_render(url, is_history_action=True)
def forward_button_callback(widget): url = history_manager.go_forward()
    if url: fetch_and_render(url, is_history_action=True)
def nav_button_callback(widget): 
    url = URL_ABOUT if widget.label() == "About" else URL_CONTACT; 
    fetch_and_render(url)
def demo_button_callback(widget): run_full_demo_callback(widget)

window = Fl_Window(700, 600, f"Project Chimera {VERSION} (Security Upgrade)")
window.begin()

address_input = Fl_Input(10, 10, 310, 30, "URL:")
address_input.callback(address_input_callback)
address_input.value(URL_HOME)

back_button = Fl_Button(330, 10, 60, 30, "< Назад")
forward_button = Fl_Button(395, 10, 70, 30, "Вперед >")
back_button.callback(back_button_callback)
forward_button.callback(forward_button_callback)

nav_about_button = Fl_Button(470, 10, 65, 30, "About")
nav_contact_button = Fl_Button(540, 10, 70, 30, "Contact")
nav_about_button.callback(nav_button_callback)
nav_contact_button.callback(nav_button_callback)

demo_button = Fl_Button(615, 10, 75, 30, "Run Demo")
demo_button.callback(demo_button_callback)

renderer = HTMLRendererWidget(10, 50, 680, 540, HTML_HOME)

window.end()

fetch_and_render(URL_HOME)
Fl.run()
