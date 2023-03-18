import random
import textwrap
import tkinter as tk

from fpdf import FPDF
from PIL import Image, ImageTk
from tkinter import filedialog
from pdf2image import convert_from_path

img = Image.new('RGB', (10, 10))

for x in range(10):
    for y in range(10):
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        img.putpixel((x, y), (r, g, b))

root = tk.Tk()
root.geometry("960x600")
root.minsize(960, 600)
root.state('zoomed')
root.title("Text Editor To PDF")
root.wm_iconphoto(True, ImageTk.PhotoImage(img))

frame = tk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True)

line_numbers = tk.Text(frame, width=4, padx=4,
                       pady=4, takefocus=0,border=0,
                       background='lightgray',
                       state=tk.DISABLED)
line_numbers.pack(side=tk.LEFT, fill=tk.Y)

fonts = {
    'Courier': 7,
    'Arial': 5.25,
    'Times': 4.9,
    'Symbol': 5.5,
    'ZapfDingbats': 8,
}
selected_font = tk.StringVar(root)
selected_font.set(list(fonts.keys())[0])

root.update()
text = tk.Text(frame, wrap=tk.NONE, undo=True,
               font=(selected_font.get(), 10),
               width=int(2*root.winfo_reqwidth()/3))
text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

root.update()
pdf_frame = tk.Frame(frame, bg="white",
                     width=int(root.winfo_reqwidth()/3))
pdf_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

root.update()
canvas = tk.Canvas(pdf_frame,
                   width=int(root.winfo_reqwidth()/3))
canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

scrollbar = tk.Scrollbar(canvas, orient=tk.VERTICAL,
                         command=canvas.yview)
scrollbar.pack(side=tk.LEFT, fill=tk.Y)

canvas.configure(yscrollcommand=scrollbar.set)
canvas.bind('<Configure>', lambda e: canvas.configure(
    scrollregion=canvas.bbox('all')))


def _on_mousewheel(event=None):
    canvas.yview_scroll(int(-1*(event.delta/120)),
                        "units")


def _bound_to_mousewheel(event=None):
    canvas.bind_all("<MouseWheel>", _on_mousewheel)


def _unbound_to_mousewheel(event=None):
    canvas.unbind_all("<MouseWheel>")
    
canvas.bind('<Enter>', _bound_to_mousewheel)
canvas.bind('<Leave>', _unbound_to_mousewheel)


def display_pdf(filepath):
    try:
        canvas.delete('all')
        images = convert_from_path(
            filepath, dpi=200,
            poppler_path=r'poppler-0.68.0\bin')
        for i, image in enumerate(images):
            image = image.resize((int(root.winfo_width()/3),
                                  root.winfo_height()))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            img_tk = ImageTk.PhotoImage(image=image)
            label = tk.Label(canvas, image=img_tk)
            label.image = img_tk
            canvas.create_window(0, i*root.winfo_height(),
                                  anchor=tk.NW, window=label)
    except Exception as e:
        print(e)


def on_scroll(*args):
    line_numbers.yview_moveto(args[0])
    text.yview_moveto(args[0])


def update_line_numbers(event=None):
    line_numbers.config(state=tk.NORMAL,
                        font=(selected_font.get(),
                              selected_size.get()))
    line_numbers.delete('1.0', tk.END)
    lines = text.get('1.0', tk.END).count('\n')
    for i in range(1, lines+1):
        line_numbers.insert(tk.END, str(i) + '\n')
    line_numbers.config(state=tk.DISABLED,
                        font=(selected_font.get(),
                              selected_size.get()))
        

def open_file(*args):
    global filepath
    file_path = filedialog.askopenfilename()
    if not file_path:
        return
    filepath = file_path
    with open(file_path, 'r') as file:
        text.delete('1.0', tk.END)
        text.insert('1.0', file.read())
        update_line_numbers()
    root.title(f"Text Editor To PDF: {filepath}")
    display_pdf(filepath.split('/')[-1].split(
        '.')[0].replace(' ', '_') + '.pdf')


def save_file(*args):
    global filepath
    if 'filepath' not in globals():
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt")
    else:
        file_path = filepath
    if not file_path:
        return
    with open(file_path, 'w') as file:
        file.write(text.get('1.0', tk.END))
    filepath = file_path
    root.title(f"Text Editor To PDF: {filepath}")


def save_file_as(*args):
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt")
    if not file_path:
        return
    with open(file_path, 'w') as file:
        file.write(text.get('1.0', tk.END))
    global filepath
    filepath = file_path
    root.title(f"Text Editor To PDF: {filepath}")


def text_to_pdf():
    global filepath

    save_file()
    text_data = str(text.get('1.0', tk.END))

    a4_width_mm = 210
    fontsize_pt = selected_size.get()
    pt_to_mm = fontsize_pt * 0.035
    fontsize_mm = fontsize_pt * pt_to_mm
    margin_bottom_mm = 10
    character_width_mm = fonts[selected_font.get()] * pt_to_mm
    width_text = a4_width_mm / character_width_mm  

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(True, margin=margin_bottom_mm)
    pdf.add_page()
    pdf.set_font(family=selected_font.get().capitalize(),
                 size=fontsize_pt)
    splitted = text_data.split('\n')

    for _, line in enumerate(splitted):
        lines = textwrap.wrap(line, width_text)
        if lines and lines[0].startswith('~'):
            for _ in range(int(lines[0][1])):
                pdf.ln()
                pdf.cell(1, fontsize_mm, txt=' ' * 5, ln=1)
            lines[0] = lines[0][2:]
        if len(lines) == 0:
            pdf.ln()
        for wrap in lines:
            pdf.cell(0, fontsize_mm, wrap, ln=1)
    pdf.output(
        filepath.split('/')[-1].split(
            '.')[0].replace(' ', '_') + '.pdf', 'F')
    display_pdf(filepath.split('/')[-1].split(
        '.')[0].replace(' ', '_') + '.pdf')


def cut(event=None):
    text.event_generate("<<Cut>>")
    update_line_numbers()


def copy(event=None):
    text.event_generate("<<Copy>>")


def paste(event=None):
    text.event_generate("<<Paste>>")
    update_line_numbers()


def delete_next_word(event=None):
    pos = text.search(r'\s', tk.INSERT, regexp=True,
                      stopindex=tk.END)
    if pos:
        text.delete(tk.INSERT, pos)


def delete_previous_word(event=None):
    pos = text.search(r'\s', tk.INSERT, regexp=True,
                      backwards=True)
    if pos:
        pos = pos.split('.')[0] + '.' + str(
            int(pos.split('.')[1])+1)
        text.delete(pos, tk.INSERT)


def font_changed(*args):
    text.config(font=(selected_font.get(),
                      selected_size.get()))

menu_bar = tk.Menu(root)
text.config(yscrollcommand=on_scroll)
line_numbers.config(yscrollcommand=on_scroll)
text.bind('<Any-KeyPress>', update_line_numbers)

selected_font.trace('w', font_changed)
font_menu = tk.Menu(menu_bar, tearoff=0)
font_menu.add_command(label="Fonts")
for font_family in fonts:
    font_menu.add_command(
        label=font_family,
        command=lambda font_family=font_family:
            selected_font.set(font_family))

font_sizes = [8, 10, 12, 14, 16, 18, 20, 24, 28, 32]
size_menu = tk.Menu(menu_bar, tearoff=0)
size_menu.add_command(label="Size")

selected_size = tk.IntVar(root)
selected_size.set(font_sizes[1])
selected_size.trace('w', font_changed)

for font_size in font_sizes:
    size_menu.add_command(
        label=font_size,
        command=lambda font_size=font_size:
            selected_size.set(font_size))

file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Open", command=open_file)
file_menu.add_command(label="Save", command=save_file)
file_menu.add_command(label="Save As", command=save_file_as)
file_menu.add_separator()
file_menu.add_command(label="To PDF", command=text_to_pdf)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

menu_bar.add_cascade(label="File", menu=file_menu)
menu_bar.add_cascade(label="Fonts", menu=font_menu)
menu_bar.add_cascade(label="Sizes", menu=size_menu)

text.bind("<Control-x>", cut)
text.bind("<Control-c>", copy)
text.bind("<Control-s>", save_file)
text.bind("<Control-a>", open_file)
text.bind("<Control-v>", paste)
text.bind("<Control-Delete>", delete_next_word)
text.bind("<Control-BackSpace>", delete_previous_word)

root.config(menu=menu_bar)
root.mainloop()
