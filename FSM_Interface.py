"""
Finite State Machine Interface

Purpose: Drag-and-drop interface for building and running FSMs. External data stream possible
Usage:

Author: Kyle Ulberg
Initial Release: August 25, 2021
Changelog:

Known Issues:

"""
from tkinter import *
from tkinterdnd2 import *
from PIL import Image, ImageDraw, ImageTk
import threading
import time
import math
import sys
import json


class Main(threading.Thread): # TODO: Terminate threads on app close
    def __init__(self, **kwargs):
        threading.Thread.__init__(self)
        self.main = None
        self.kwargs = kwargs
        self.start()
        time.sleep(.1) # TODO: Check if necessary or possible to trim

    def run(self):
        self.main = Thread(self.kwargs)
        self.main.run()

class Fun(threading.Thread): # TODO: Terminate threads on app close
    def __init__(self, main, function):
        threading.Thread.__init__(self)
        self.main = main
        self.function = function
        self.start()
        time.sleep(.1) # TODO: Check if necessary or possible to trim

    def run(self):
        exec(compile('self.main.'+self.function, '', 'exec'))

class Thread:
    def __init__(self, kwargs):
        # external = bool; True prevents manual input, requires threading
        # directory = str; Same folder as .py, input location otherwise
        # file = str; Autoloads FSMI save file on launch
        self.kwarg = {}
        for key, val in kwargs.items():
            self.kwarg[key] = val

        self.root = TkinterDnD.Tk()
        self.root.title("FSM-I")
        self.root.geometry("1600x900")
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.canvas = Canvas(self.root, width=1410, height=895)
        self.canvas.drop_target_register(DND_FILES)
        self.canvas.dnd_bind('<<Drop>>', self.load_drop)
        self.f = Frame(self.root)
        self.f2 = Frame(self.root)
        self.nodes = []
        self.new_name = self.name_gen()

        self.lim3_u = self.f.register(self.limit_three_unique)
        self.labels = []
        self.labels_active = {}  # {Label: Color}
        self.drag_line = {}
        self.add_row()
        self.active = {0: 0, 1: False}  # Holds the active "state" Node object for runtime
        self.cross = self.canvas.create_polygon(100, 100, 105, 110,
                                                100, 120, 110, 115,
                                                120, 120, 115, 110,
                                                120, 100, 110, 105,
                                                fill='red')
        self.canvas.tag_bind(self.cross, '<Button-1>', lambda e: self.run_select(e))
        self.canvas.moveto(self.cross, 1500, 500)
        self.images = [ImageTk.PhotoImage(Image.new('RGBA', (1410, 895), self.root.winfo_rgb('black') + (20,)))]
        self.block = self.canvas.create_image(1410 / 2, 895 / 2, image=self.images[-1])
        self.canvas.itemconfigure(self.block, state=HIDDEN)

        self.high = []
        for i in range(6):
            image = Image.new('RGBA', (100, 100), self.root.winfo_rgb('white') + (0,))
            image2 = ImageDraw.Draw(image)
            image2.ellipse((0, 0, 100, 100), fill=self.root.winfo_rgb('white') + (20 * i,))
            self.images.append(ImageTk.PhotoImage(image))
            self.high.append(self.canvas.create_image(200 + i * 100, 200, image=self.images[-1]))
            self.canvas.itemconfigure(self.high[-1], state=HIDDEN)
        for i in range(6):
            image = Image.new('RGBA', (100, 100), self.root.winfo_rgb('white') + (0,))
            image2 = ImageDraw.Draw(image)
            image2.ellipse((0, 0, 100, 100), fill=self.root.winfo_rgb('white') + (120 - 20 * i,))
            image.save('test.png')
            self.images.append(ImageTk.PhotoImage(image))
            self.high.append(self.canvas.create_image(800 + i * 100, 200, image=self.images[-1]))
            self.canvas.itemconfigure(self.high[-1], state=HIDDEN)

        Button(self.f, text="SAVE", command=self.save).grid(column=0, row=0)
        Button(self.f, text="LOAD", command=self.load_notify).grid(column=1, row=0)
        Button(self.f, text="SHARE", command=self.share).grid(column=2, row=0, columnspan=3)
        self.nodeButton = Button(self.f, text="NODE", command=self.new_node)
        self.nodeButton.grid(column=0, row=99)
        self.signalButton = Button(self.f, text="SIGNAL", command=self.add_row)
        self.signalButton.grid(column=1, row=99)

        self.runButton = Button(self.f2, text="RUN", command=self.run_but)
        self.runButton.grid(column=0, row=0)
        self.stopButton = Button(self.f2, text="STOP", command=self.stop)
        self.stopButton.grid(column=1, row=0)
        self.stopButton.config(state=DISABLED)
        self.recButton = Button(self.f2, text="RECORD", command=self.record)
        self.recButton.grid(column=4, row=0, columnspan=1)
        self.recButton.config(state=DISABLED)
        self.runDisplay = Label(self.f2, text='<runtime output>', height=1, width=25, relief=GROOVE)
        self.runDisplay.grid(column=0, row=1, columnspan=5)
        self.canvas.grid(column=0, row=0)
        self.f.grid(column=1, row=0, sticky=NE)
        self.f2.grid(column=1, row=0, sticky=SE)

        if 'file' in self.kwarg:
            self.load(self.kwarg['file'])
        if 'external' in self.kwarg: # TODO: Better handling of strange kwarg combinations / failed loads / etc
            if not self.kwarg['external']:
                self.run()


    class Node:
        def __init__(self, main):
            self.main = main
            canvas = main.canvas

            self.x = 150
            self.y = 150
            self.orbit = {} # {Signal: [Color, Tag Object, Linked Node]}
            self.links = {} # {Target Node: Link Object}
            self.self_links = None # LinkSelf Object

            self.color = 'blue'
            self.image = canvas.create_oval(100, 100, 200, 200, fill=self.color, outline='black')
            canvas.tag_bind(self.image, '<Button-1>', lambda e: self.pick(e))
            canvas.tag_bind(self.image, '<B1-Motion>', lambda e: self.drag(e))
            canvas.tag_bind(self.image, '<ButtonRelease-1>', lambda e: self.drop())
            canvas.tag_bind(self.image, '<Button-3>', lambda e: self.node_options())

            self.text = canvas.create_text(150, 150, text='<null>\n<multi-line>', fill="white")
            canvas.tag_bind(self.text, '<Button-1>', lambda e: self.pick(e))
            canvas.tag_bind(self.text, '<B1-Motion>', lambda e: self.drag(e))
            canvas.tag_bind(self.text, '<ButtonRelease-1>', lambda e: self.drop())
            canvas.tag_bind(self.text, '<Button-3>', lambda e: self.node_options())

            main.nodes.append(self)
            main.update_node(self)

        def get_text(self):
            return self.main.canvas.itemcget(self.text, 'text')

        def update_orbit(self, old, new):
            self.orbit = {new if k == old else k:v for k,v in self.orbit.items()}

        def delete_load(self):
            if not self.orbit == 0:
                for orb in self.orbit:
                    self.orbit[orb][1].delete_tag()
            if not self.links == 0:
                for link in self.links:
                    self.links[link].delete_link()
            if self.self_links is not None:
                self.self_links.delete_link()
            for node in self.main.nodes:
                for orb in node.orbit:
                    if node.orbit[orb][2] is self:
                        node.orbit[orb][2] = 0
            self.main.canvas.delete(self.image, self.text)
            self.main.nodes.remove(self)

        def delete_node(self, window):
            if not self.orbit == 0:
                for orb in self.orbit:
                    self.orbit[orb][1].delete_tag()
            if not self.links == 0:
                for link in self.links:
                    self.links[link].delete_link()
            if self.self_links is not None:
                self.self_links.delete_link()
            for node in self.main.nodes:
                for orb in node.orbit:
                    if node.orbit[orb][2] is self:
                        node.orbit[orb][2] = 0
            self.main.canvas.delete(self.image, self.text)
            self.main.nodes.remove(self)
            window.destroy()
            self.main.update_nodes()

        def pick(self, event):
            self.x, self.y = event.x, event.y
            self.main.canvas.tag_raise(self.image)
            self.main.canvas.tag_raise(self.text)

        def drag(self, event):
            self.main.canvas.move(self.image, event.x - self.x, event.y - self.y)
            self.main.canvas.move(self.text, event.x - self.x, event.y - self.y)
            for orb in self.orbit:
                self.main.canvas.move(self.orbit[orb][1].image, event.x - self.x, event.y - self.y)
                self.main.canvas.move(self.orbit[orb][1].text, event.x - self.x, event.y - self.y)
            if self.self_links is not None:
                self.main.canvas.move(self.self_links.image, event.x - self.x, event.y - self.y)
                self.main.canvas.move(self.self_links.bg, event.x - self.x, event.y - self.y)
                self.main.canvas.move(self.self_links.text, event.x - self.x, event.y - self.y)
            for n in self.main.nodes:
                for l in n.links:
                    n.links[l].move_link(n, l)
            self.x, self.y = event.x, event.y
            # print(event.x, event.y)

        def drop(self):
            self.main.update_nodes()

        def node_options(self):  # TODO: More options (sound, output, etc)
            self.main.canvas.tag_raise(self.image)
            self.main.canvas.tag_raise(self.text)
            InputWindow = Toplevel(self.main.root)
            InputWindow.title("Node Options")
            InputWindow.geometry("210x400")
            InputWindow.grab_set()

            Label(InputWindow, text='color:').grid(row=0, column=0)
            t_color = Entry(InputWindow, width=20)
            t_color.insert(END, self.color)
            t_color.grid(row=0, column=1)

            Label(InputWindow, text='text:').grid(row=1, column=0)
            t_text = Text(InputWindow, height=4, width=20)
            t_text.insert(END, self.get_text())
            t_text.grid(row=1, column=1)

            options = [t_color, t_text]
            Button(InputWindow, text="SAVE CHANGES", command=lambda:
                self.save_options(InputWindow, options)).grid(row=98, column=0, columnspan=2)
            Button(InputWindow, text="DELETE NODE", command=lambda:
                self.delete_node(InputWindow)).grid(row=99, column=0, columnspan=2)

        def save_options(self, window, options):
            flag = 0 # All options must pass
            color = options[0].get()
            text = options[1].get(1.0, END)
            restore = [self.color, self.get_text()] # TODO: Restore point
            try:
                self.main.canvas.itemconfigure(self.image, fill=color)
                self.main.canvas.itemconfigure(self.text, fill=self.main.color_neg(color))
                self.color = color
                flag += 1
            except:
                options[0].config(bg='red')
                window.update()
                time.sleep(.1)
                options[0].config(bg='white')

            try:
                self.main.canvas.itemconfigure(self.text, text=text[0:len(text)-1])
                flag += 1
            except:
                options[1].config(bg='red')
                window.update()
                time.sleep(.1)
                options[1].config(bg='white')

            if flag == 2:
                window.destroy()
                self.main.update_nodes()

    class Tag:
        def __init__(self, main, color, text, x, y):
            self.main = main
            self.canvas = main.canvas
            #self.image = canvas.create_image((200, 200), image=circle)
            self.color = color
            self.image = self.canvas.create_oval(x - 15, y - 15, x + 15, y + 15, fill=color, outline='black')
            self.canvas.tag_bind(self.image, '<Button-1>', lambda e: self.tag_pick(self.image, e))
            self.canvas.tag_bind(self.image, '<B1-Motion>', lambda e: self.tag_drag(e))
            self.canvas.tag_bind(self.image, '<ButtonRelease-1>', lambda e: self.tag_drop(self, e))
            self.canvas.tag_bind(self.image, '<Button-3>', lambda e: self.link_delete())

            self.text = self.canvas.create_text(x, y, text=text, font=('Purisa', 8), fill=self.main.color_neg(color))
            self.canvas.tag_bind(self.text, '<Button-1>', lambda e: self.tag_pick(self.image, e))
            self.canvas.tag_bind(self.text, '<B1-Motion>', lambda e: self.tag_drag(e))
            self.canvas.tag_bind(self.text, '<ButtonRelease-1>', lambda e: self.tag_drop(self, e))
            self.canvas.tag_bind(self.text, '<Button-3>', lambda e: self.link_delete())

        def flash(self):
            self.main.canvas.itemconfigure(self.image, fill=self.main.color_neg(self.color))
            self.main.canvas.itemconfigure(self.text, fill=self.color)
            self.main.root.update()
            time.sleep(.1)
            self.main.canvas.itemconfigure(self.image, fill=self.color)
            self.main.canvas.itemconfigure(self.text, fill=self.main.color_neg(self.color))

        def save_options(self, window, options): # TODO: Remove or implement
            flag = 0
            try:
                self.main.canvas.itemconfigure(self.image, fill=options[0].get())
                self.main.canvas.itemconfigure(self.text, fill=self.main.color_neg(options[0].get()))
                self.color = options[0].get()
                flag += 1
            except:
                options[0].config(bg='red')
                window.update()
                time.sleep(.02)
                options[0].config(bg='white')
            if flag == 1:
                window.destroy()
                self.main.update_nodes()

        def delete_tag(self):
            self.main.canvas.delete(self.image, self.text)

        def tag_pick(self, tag, event):
            x0, y0, x1, y1 = self.canvas.coords(tag)
            x = (x0 + x1) / 2
            y = (y0 + y1) / 2
            color = self.canvas.itemcget(tag, 'fill')
            self.main.drag_line[0] = [self.canvas.create_line(x, y, event.x, event.y,
                                                              fill=self.main.color_neg(color), width=6),
                                      self.canvas.create_line(x, y, event.x, event.y, fill=color, width=4), x, y]

        def tag_drag(self, event):
            self.canvas.coords(self.main.drag_line[0][0], self.main.drag_line[0][2], self.main.drag_line[0][3],
                               event.x, event.y)
            self.canvas.coords(self.main.drag_line[0][1], self.main.drag_line[0][2], self.main.drag_line[0][3],
                               event.x, event.y)

        def tag_drop(self, tag, event):
            self.canvas.delete(self.main.drag_line[0][0])
            self.canvas.delete(self.main.drag_line[0][1])
            self.main.drag_line.clear()
            widgets = [c if not c == '' else None for c in
                       self.canvas.find_overlapping(event.x, event.y, event.x, event.y)]
            if len(widgets) > 0:
                # print(widgets)
                matches = []
                for i in widgets:
                    # print(canvas.itemcget(i, 'fill'))
                    for node in self.main.nodes:
                        if node.image == i:
                            # print(canvas.itemcget(node.text, 'text'))
                            matches.append(node)
                root_node = 0
                root_orb = 0
                for node in self.main.nodes:
                    for orb in node.orbit:
                        if node.orbit[orb][1] is tag:
                            root_node = node
                            root_orb = orb
                if len(matches) == 1:
                    # print(root_node.orbit[root_orb][2], root_node.orbit[root_orb][2] == root_node)
                    root_node.orbit[root_orb][2] = matches[0]
                    self.main.update_nodes()

        def link_delete(self):
            root_node = 0
            root_orb = 0
            for node in self.main.nodes:
                for orb in node.orbit:
                    if node.orbit[orb][1] is self:
                        root_node = node
                        root_orb = orb
            if not root_node.orbit[root_orb][2] == 0:
                root_node.orbit[root_orb][2] = 0
                self.main.update_nodes()

    class Link:
        def __init__(self, main, color, color2, text, x, y, x2, y2):
            self.main = main
            self.canvas = main.canvas
            calc1 = ((x2 - x) * .8 + x, (y2 - y) * .8 + y)
            calc2 = ((x2 - x) * .7 + x, (y2 - y) * .7 + y)
            calc3 = ((x2 - x) * .5 + x, (y2 - y) * .5 + y)
            #w = math.pow(math.pow(calc1[0], 2) + math.pow(calc1[1], 2), .5) * .0625
            w = 45
            angle = math.atan2((y2 - y), (x2 - x))
            self.line0 = self.canvas.create_line(x, y, calc1[0], calc1[1], width=w+2, fill='black')
            self.line1 = self.canvas.create_line(x, y, calc1[0], calc1[1], width=w, fill=color)
            self.poly = self.canvas.create_polygon(x2, y2, calc2[0] + math.sin(angle + math.pi) * w,
                                                      calc2[1] - math.cos(angle + math.pi) * w,
                                                      calc2[0] - math.sin(angle + math.pi) * w,
                                                      calc2[1] + math.cos(angle + math.pi) * w,
                                              fill=color2, outline='black')
            self.text = self.canvas.create_text(calc3[0], calc3[1],
                                           text=text, fill=self.main.color_neg(color), angle=angle)
            self.canvas.tag_lower(self.text)
            self.canvas.tag_lower(self.poly)
            self.canvas.tag_lower(self.line1)
            self.canvas.tag_lower(self.line0)
            self.canvas.itemconfigure(self.line0, tags='LINES')
            self.canvas.itemconfigure(self.line1, tags='LINES0')
            self.canvas.itemconfigure(self.poly, tags='POLYS')
            self.canvas.itemconfigure(self.text, tags='TEXTS')

        def move_link(self, node, link):
            node_x = sum(self.canvas.coords(node.image)[::2])/2
            node_y = sum(self.canvas.coords(node.image)[1::2])/2
            target_x = sum(self.canvas.coords(link.image)[::2])/2
            target_y = sum(self.canvas.coords(link.image)[1::2])/2
            calc1 = ((target_x - node_x) * .8 + node_x, (target_y - node_y) * .8 + node_y)
            calc2 = ((target_x - node_x) * .7 + node_x, (target_y - node_y) * .7 + node_y)
            calc3 = ((target_x - node_x) * .5 + node_x, (target_y - node_y) * .5 + node_y)
            #w = math.pow(math.pow(calc1[0], 2) + math.pow(calc1[1], 2), .5) * .0625
            w = 45
            angle = math.atan2((target_y - node_y), (target_x - node_x))

            self.canvas.coords(self.line0, node_x, node_y, calc1[0], calc1[1])
            self.canvas.coords(self.line1, node_x, node_y, calc1[0], calc1[1])
            #canvas.itemconfigure(self.line1, width=w+2)
            #canvas.itemconfigure(self.line2, width=w)
            self.canvas.coords(self.poly, target_x, target_y,
                          calc2[0] + math.sin(angle + math.pi) * w,
                          calc2[1] - math.cos(angle + math.pi) * w,
                          calc2[0] - math.sin(angle + math.pi) * w,
                          calc2[1] + math.cos(angle + math.pi) * w)
            c = self.canvas.coords(self.text)
            self.canvas.move(self.text, calc3[0] - c[0], calc3[1] - c[1])

        def delete_link(self):
            self.canvas.delete(self.line0, self.line1, self.poly, self.text)

    class LinkDouble:
        def __init__(self, main, color01, color02, color11, color12, text, text2, x, y, x2, y2):
            self.main = main
            self.canvas = main.canvas
            calc1 = ((x2 - x) * .8 + x, (y2 - y) * .8 + y)
            calc2 = ((x2 - x) * .7 + x, (y2 - y) * .7 + y)
            calc3 = ((x2 - x) * .5 + x, (y2 - y) * .5 + y)
            #w = math.pow(math.pow(calc1[0], 2) + math.pow(calc1[1], 2), .5) * .0625
            w = 45
            angle = math.atan2((y2 - y), (x2 - x))
            off_x, off_y = -math.sin(angle+math.pi)*w/2, math.cos(angle+math.pi)*w/2

            self.line01 = self.canvas.create_line(x+off_x*2, y+off_y*2, calc1[0]+off_x*2, calc1[1]+off_y*2, width=2)
            self.line1 = self.canvas.create_line(x+off_x, y+off_y, calc1[0]+off_x, calc1[1]+off_y,
                                                 width=w, fill=color01)
            self.poly1 = self.canvas.create_polygon(x2, y2, calc2[0], calc2[1],
                                                       calc2[0] - math.sin(angle + math.pi) * w + off_x,
                                                       calc2[1] + math.cos(angle + math.pi) * w + off_y,
                                               fill=color02, outline='black')
            self.text1 = self.canvas.create_text(calc3[0]+off_x, calc3[1]+off_y,
                                            text=text, fill=self.main.color_neg(color01))
            self.canvas.tag_lower(self.text1)
            self.canvas.tag_lower(self.poly1)
            self.canvas.tag_lower(self.line1)
            self.canvas.itemconfigure(self.line1, tags='LINES')
            self.canvas.itemconfigure(self.poly1, tags='POLYS')
            self.canvas.itemconfigure(self.text1, tags='TEXTS')

            calc1 = ((x - x2) * .8 + x2, (y - y2) * .8 + y2)
            calc2 = ((x - x2) * .7 + x2, (y - y2) * .7 + y2)
            calc3 = ((x - x2) * .5 + x2, (y - y2) * .5 + y2)

            self.line02 = self.canvas.create_line(x2-off_x*2, y2-off_y*2, calc1[0]-off_x*2, calc1[1]-off_y*2, width=2)
            self.line2 = self.canvas.create_line(x2-off_x, y2-off_y, calc1[0]-off_x, calc1[1]-off_y,
                                                 width=w, fill=color11)
            self.poly2 = self.canvas.create_polygon(x, y, calc2[0], calc2[1],
                                                     calc2[0] + math.sin(angle + math.pi) * w - off_x,
                                                     calc2[1] - math.cos(angle + math.pi) * w - off_y,
                                               fill=color12, outline='black')
            self.text2 = self.canvas.create_text(calc3[0]-off_x, calc3[1]-off_y,
                                            text=text2, fill=self.main.color_neg(color11))
            self.canvas.tag_lower(self.text2)
            self.canvas.tag_lower(self.poly2)
            self.canvas.tag_lower(self.line2)
            self.canvas.itemconfigure(self.line2, tags='LINES')
            self.canvas.itemconfigure(self.poly2, tags='POLYS')
            self.canvas.itemconfigure(self.text2, tags='TEXTS')

            self.canvas.tag_lower(self.line01)
            self.canvas.itemconfigure(self.line01, tags='LINES0')
            self.canvas.tag_lower(self.line02)
            self.canvas.itemconfigure(self.line02, tags='LINES0')

        def move_link(self, node, link):
            x = sum(self.canvas.coords(node.image)[::2])/2
            y = sum(self.canvas.coords(node.image)[1::2])/2
            x2 = sum(self.canvas.coords(link.image)[::2])/2
            y2 = sum(self.canvas.coords(link.image)[1::2])/2
            calc1 = ((x2 - x) * .8 + x, (y2 - y) * .8 + y)
            calc2 = ((x2 - x) * .7 + x, (y2 - y) * .7 + y)
            calc3 = ((x2 - x) * .5 + x, (y2 - y) * .5 + y)
            #w = math.pow(math.pow(calc1[0], 2) + math.pow(calc1[1], 2), .5) * .0625
            w = 45
            angle = math.atan2((y2 - y), (x2 - x))
            off_x, off_y = -math.sin(angle+math.pi)*w/2, math.cos(angle+math.pi)*w/2

            self.canvas.coords(self.line01, x+off_x*2, y+off_y*2, calc1[0]+off_x*2, calc1[1]+off_y*2)
            self.canvas.coords(self.line1, x+off_x, y+off_y, calc1[0]+off_x, calc1[1]+off_y)
            self.canvas.itemconfigure(self.line1, width=w)
            self.canvas.coords(self.poly1, x2, y2,
                          calc2[0], calc2[1],
                          calc2[0] - math.sin(angle + math.pi) * w + off_x,
                          calc2[1] + math.cos(angle + math.pi) * w + off_y)
            c = self.canvas.coords(self.text1)
            self.canvas.move(self.text1, calc3[0]+off_x-c[0], calc3[1]+off_y-c[1])

            calc1 = ((x - x2) * .8 + x2, (y - y2) * .8 + y2)
            calc2 = ((x - x2) * .7 + x2, (y - y2) * .7 + y2)
            calc3 = ((x - x2) * .5 + x2, (y - y2) * .5 + y2)

            self.canvas.coords(self.line02, x2-off_x*2, y2-off_y*2, calc1[0]-off_x*2, calc1[1]-off_y*2)
            self.canvas.coords(self.line2, x2-off_x, y2-off_y, calc1[0]-off_x, calc1[1]-off_y)
            self.canvas.itemconfigure(self.line2, width=w)
            self.canvas.coords(self.poly2, x, y, calc2[0], calc2[1],
                                            calc2[0] + math.sin(angle + math.pi) * w - off_x,
                                            calc2[1] - math.cos(angle + math.pi) * w - off_y)
            c = self.canvas.coords(self.text2)
            self.canvas.move(self.text2, calc3[0]-off_x-c[0], calc3[1]-off_y-c[1])

        def delete_link(self):
            self.canvas.delete(self.line01, self.line02)
            self.canvas.delete(self.line1, self.poly1, self.text1)
            self.canvas.delete(self.line2, self.poly2, self.text2)

    class LinkSelf:
        def __init__(self, main, node, color, text, x, y):
            self.main = main
            self.canvas = main.canvas
            self.image = self.canvas.create_oval(x - 90, y - 90, x+10, y+10, fill=color, outline='black')
            self.bg = self.canvas.create_oval(x - 50, y - 50, x - 30, y - 30,
                                              fill=self.main.root.cget('bg'), outline='black')
            self.text = self.canvas.create_text(x - 40, y - 70, text=text, fill=self.main.color_neg(color))
            self.canvas.tag_lower(self.image, node)
            self.canvas.tag_lower(self.bg, node)
            self.canvas.tag_lower(self.text, node)

        def delete_link(self):
            self.canvas.delete(self.image, self.bg, self.text)

    class SignalButton:
        def __init__(self, main, text):
            self.main = main
            self.but = Button(self.main.f, text=text)
            self.text = text
            self.but.config(command=self.but_send)

        def but_send(self):
            self.main.send(self.text)

        def delete_but(self):
            self.but.destroy()


    def run(self):
        self.root.mainloop()

    def quit(self): # TODO: Troubleshoot function calls after quit(); Some error correctly, others hang... maybe
        self.stop() # TODO: Troubleshoot X-close not stopping correctly
        time.sleep(.1)
        self.root.quit()

    def new_node(self):
        self.Node(self)

    def start(self, text):
        matches = []
        for node in self.nodes:
            if self.canvas.itemcget(node.text, 'text') == text:
                matches.append(node)
        if len(matches) == 1:
            self.active[0] = matches[0]
            self.run_but()

    def display(self, text):
        self.runDisplay.config(text=text)

    def get_active(self):
        if not self.active[0] == 0:
            return self.canvas.itemcget(self.active[0].text, 'text')
        else:
            return -1

    # Does all the heavy lifting for signal changes on nodes (signal/link display/color, etc)
    def update_node(self, node):
        for label in self.labels_active:
            if label in node.orbit:
                node.orbit[label][0] = self.labels_active[label]
            else:
                node.orbit[label] = [self.labels_active[label], 0, 0]
        remove = []
        for orb in node.orbit:
            if orb not in self.labels_active:
                remove.append(orb)
        for rem in remove:
            node.orbit[rem][1].delete_tag()
            del node.orbit[rem]
        if node.self_links is not None:
            node.self_links.delete_link()
            node.self_links = None
        for link in node.links:
            node.links[link].delete_link()
        node.links.clear()

        a, b, c, d = self.canvas.coords(node.image)
        center_x = (a+c)/2
        center_y = (b+d)/2
        angle = 3
        links = {} # {Target Node Object: [Signal 1, Signal 2, ...]}
        links_self = []
        for orb in node.orbit:
            if not node.orbit[orb][1] == 0:
                node.orbit[orb][1].delete_tag()
            self.canvas.delete(node.orbit[orb][1])
            x = center_x+(math.sin(angle)*60)
            y = center_y+(math.cos(angle)*60)
            node.orbit[orb][1] = self.Tag(self, node.orbit[orb][0], orb, x, y)
            angle -= .5
            if not node.orbit[orb][2] == 0:
                if not node.orbit[orb][2] == node:
                    if node.orbit[orb][2] in links:
                        links[node.orbit[orb][2]].append(orb)
                    else:
                        links[node.orbit[orb][2]] = [orb]
                else:
                    links_self.append(orb)
        for link in links:
            flag = False
            for orb in link.orbit:
                if node in link.orbit[orb]: # Safety check for LinkDouble
                    flag = True
            if not flag:
                links_text = str([t + '\n' for t in links[link]]).replace("\\n'", "\n").replace(", '", "")[2:-2]
                target_x = sum(self.canvas.coords(link.image)[::2])/2
                target_y = sum(self.canvas.coords(link.image)[1::2])/2
                cols = []
                for orb in node.orbit:
                    if node.orbit[orb][2] == link and node.orbit[orb][0] not in cols:
                        cols.append(node.orbit[orb][0])
                if len(cols) == 1:
                    color = cols[0]
                    node.links[link] =\
                        self.Link(self, color, color, links_text, center_x, center_y, target_x, target_y)
                else:
                    node.links[link] =\
                        self.Link(self, node.color, link.color, links_text, center_x, center_y, target_x, target_y)
            else:
                links2 = {} # {Target Node Object: [Signal 1, Signal 2, ...]}
                for orb in link.orbit:
                    if not link.orbit[orb][2] == 0:
                        if not link.orbit[orb][2] == link:
                            if link.orbit[orb][2] in links2:
                                links2[link.orbit[orb][2]].append(orb)
                            else:
                                links2[link.orbit[orb][2]] = [orb]
                links_text = str([t + '\n' for t in links[link]]).replace("\\n'", "\n").replace(", '", "")[2:-2]
                links_text2 = str([t + '\n' for t in links2[node]]).replace("\\n'", "\n").replace(", '", "")[2:-2]
                target_x = sum(self.canvas.coords(link.image)[::2])/2
                target_y = sum(self.canvas.coords(link.image)[1::2])/2
                cols1 = []
                for l in links[link]:
                    if self.labels_active[l] not in cols1:
                        cols1.append(self.labels_active[l])
                cols2 = []
                for l in links2[node]:
                    if self.labels_active[l] not in cols2:
                        cols2.append(self.labels_active[l])
                if len(cols1) == 1 and len(cols2) == 1:
                    node.links[link] = self.LinkDouble(self, cols1[0], cols1[0], cols2[0], cols2[0],
                                                       links_text, links_text2, center_x, center_y, target_x, target_y)
                elif len(cols1) == 1:
                    node.links[link] = self.LinkDouble(self, cols1[0], cols1[0], link.color, node.color,
                                                       links_text, links_text2, center_x, center_y, target_x, target_y)
                elif len(cols2) == 1:
                    node.links[link] = self.LinkDouble(self, node.color, link.color, cols2[0], cols2[0],
                                                       links_text, links_text2, center_x, center_y, target_x, target_y)
                else:
                    node.links[link] = self.LinkDouble(self, node.color, link.color, link.color, node.color,
                                                       links_text, links_text2, center_x, center_y, target_x, target_y)
                if node in link.links:
                    link.links[node].delete_link()
                link.links[node] = node.links[link]
        if len(links_self) > 0:
            links_self_text = str([t+'\n' for t in links_self]).replace("\\n'", "\n").replace(", '", "")[2:-2]
            cols = []
            for l in links_self:
                if self.labels_active[l] not in cols:
                    cols.append(self.labels_active[l])
            if len(cols) == 1:
                node.self_links = self.LinkSelf(self, node.image, cols[0], links_self_text, center_x, center_y)
            else:
                node.self_links = self.LinkSelf(self, node.image, node.color, links_self_text, center_x, center_y)

    def update_nodes(self):
        for node in self.nodes:
            self.update_node(node)

    def update_labels(self):
        self.labels_active.clear()
        for label in self.labels:
            if not label == 0:
                self.labels_active[label[0].get()] = label[2].cget('bg')
        self.update_nodes()

    def update_widget(self, new, old):
        self.labels_active.clear()
        for label in self.labels:
            if not label == 0:
                if not label[0].get() == old:
                    self.labels_active[label[0].get()] = label[2].cget('bg')
                else:
                    self.labels_active[new] = label[2].cget('bg')
        for node in self.nodes:
            node.update_orbit(old, new)
        self.update_nodes()

    # Generates unique signal keys for add_row()
    def name_gen(self):
        num = '0123456789'
        alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        alphanum = alpha+num
        while True:
            for a in num:
                for b in num:
                    for c in num:
                        if a+b+c not in self.labels_active.keys():
                            yield a+b+c
            for a in alpha:
                for b in alpha:
                    for c in alpha:
                        if a+b+c not in self.labels_active.keys():
                            yield a+b+c
            for a in alphanum:
                for b in alphanum:
                    for c in alphanum:
                        if a+b+c not in self.labels_active.keys():
                            yield a+b+c

    def add_row(self):
        if len(self.labels_active) < 10:
            row = len(self.labels)
            self.labels.append([Entry(self.f, width=3),
                           Entry(self.f, width=18),
                           Button(self.f, text=' ', command=lambda: self.col_row(row)),
                           Button(self.f, text='x', fg='red', command=lambda: self.del_row(row))])
            self.labels[-1][0].insert(END, next(self.new_name))
            self.labels[-1][0].grid(row=row+1, column=0)
            self.labels[-1][1].insert(END, 'Signal ' + str(row))
            self.labels[-1][1].grid(row=row+1, column=1, columnspan=2)
            self.labels[-1][2].grid(row=row+1, column=3)
            self.labels[-1][3].grid(row=row+1, column=4)
            self.labels[-1][0].config(validate="key", validatecommand=(self.lim3_u, '%P', '%s'))
            self.labels_active[self.labels[-1][0].get()] = self.labels[-1][2].cget('bg')
            self.update_labels()
        else:
            lab = []
            for l in self.labels:
                if not l == 0:
                    lab.append(l)
            for l in lab:
                l[0].config(bg='red')
                l[1].config(bg='red')
            self.root.update()
            time.sleep(.1)
            for l in lab:
                l[0].config(bg='white')
                l[1].config(bg='white')

    def del_row(self, row):
        # Removing grid objects:
        self.labels[row][0].destroy()
        self.labels[row][1].destroy()
        self.labels[row][2].destroy()
        self.labels[row][3].destroy()
        # Deleting unused records for the dupe check below:
        self.labels[row] = 0
        self.update_labels()

    # Colors the node link pull-tabs
    def col_row(self, row):
        InputWindow = Toplevel(self.root)
        InputWindow.title("Link Color Options")
        InputWindow.geometry("200x100")
        InputWindow.grab_set()

        Label(InputWindow, text='color').grid(row=0, column=0)
        t_color = Entry(InputWindow, width=20)
        t_color.insert(END, self.labels[row][2].cget('bg'))
        t_color.grid(row=0, column=1)

        Button(InputWindow, text="SAVE CHANGES", command=lambda:
        self.col_set(row, InputWindow, t_color)).grid(row=99, column=0, columnspan=2)

    def col_set(self, row, window, color):
        try:
            self.labels[row][2].config(bg=color.get())
            self.labels_active[row] = self.labels[row][2].cget('bg')
            self.update_labels()
            window.destroy()
        except:
            color.config(bg='red')
            window.update()
            time.sleep(.1)
            color.config(bg='white')

    # Limits text field to 3 characters of any combination, even symbols
    # '%P' in validatecommand sends what the entry field WOULD hold if this returns True
    def limit_three(self, new):
        if len(new) > 3:
            return False
        else:
            return True

    # Limits text field to 3 characters of any combination, even symbols
    # Also prevents dupes
    # '%P' in validatecommand sends what the entry field WOULD hold if this returns True
    # '%s' in validatecommand sends what the entry field holds before change
    def limit_three_unique(self, new, old):
        if len(new) > 3:
            return False
        else:
            for i in self.labels:
                if i == 0:
                    pass
                elif i[0].get() == new:
                    i[0].config(bg='red')
                    self.root.update()
                    time.sleep(.1)
                    i[0].config(bg='white')
                    return False
            self.update_widget(new, old)
            return True

    # For overlapping colors (like text on tile) inverts the code to always be visible
    def color_neg(self, color):
        rgb = tuple((c // 256 for c in self.root.winfo_rgb(color)))
        if sum(1 if 128 - 50 < c < 128 + 50 else 0 for c in rgb) < 3: # Prevents gray on gray
            return '#%02x%02x%02x' % tuple(255-c for c in rgb)
        elif sum(rgb) > 765 / 2:
            return 'white'
        else:
            return 'black'

    def run_but(self):
        if not self.active[1]:
            self.active[1] = True
            self.runDisplay.config(text='Select Starting Node')
            self.runDisplay.config(bg='red')
            self.canvas.tag_raise(self.cross)

            self.runButton.config(state=DISABLED)
            self.stopButton.config(state=NORMAL)
            self.nodeButton.config(state=DISABLED)
            self.signalButton.config(state=DISABLED)
            for label in self.labels:
                if not label == 0:
                    label[0].config(state=DISABLED)
                    label[1].config(state=DISABLED)
                    label[2].config(state=DISABLED)
                    label[3].config(state=DISABLED)
            try: # Prevents errors on application close
                while self.active[0] == 0:
                    self.canvas.moveto(self.cross, self.canvas.winfo_pointerx()-self.root.winfo_rootx()-10,
                                       self.canvas.winfo_pointery()-self.root.winfo_rooty()-10)
                    self.root.update()
            except:
                return 0
            if self.active[0] == 1: # Using stopButton to cancel runButton
                self.active[0] = 0
                self.active[1] = False
                self.canvas.moveto(self.cross, 1500, 500)

                self.runDisplay.config(text='<runtime output>')
                self.runDisplay.config(bg='SystemButtonFace')
                self.runButton.config(bg='SystemButtonFace')
                self.stopButton.config(bg='SystemButtonFace')
                self.recButton.config(bg='SystemButtonFace')
                for label in self.labels:
                    if not label == 0:
                        label[0].config(state=NORMAL)
                        label[1].config(state=NORMAL)
                        label[2].config(state=NORMAL)
                        label[3].config(state=NORMAL)

                self.canvas.itemconfigure(self.block, state=HIDDEN)
                self.nodeButton.config(state=NORMAL)
                self.signalButton.config(state=NORMAL)
                self.runButton.config(state=NORMAL)
                self.stopButton.config(state=DISABLED)
                self.recButton.config(state=DISABLED)
                return 0

            signal_buttons = []
            for label in self.labels:
                if not label == 0:
                    signal_buttons.append(self.SignalButton(self, label[0].get()))
                    signal_buttons[-1].but.grid(row=label[0].grid_info()['row'], column=0)

            self.canvas.itemconfigure(self.block, state=NORMAL)
            self.canvas.tag_raise(self.block)
            self.canvas.moveto(self.cross, 1500, 500)
            self.runButton.config(bg='green')
            self.stopButton.config(bg='red')
            self.recButton.config(bg='cyan')
            self.runDisplay.config(text='<runtime output>')
            self.runDisplay.config(bg='SystemButtonFace')

            self.recButton.config(state=NORMAL)

            while self.active[1]:
                try: # Prevents errors on normal application close
                    self.canvas.moveto(self.high[0], self.canvas.coords(self.active[0].text)[0],
                                       self.canvas.coords(self.active[0].text)[1])
                    self.canvas.itemconfigure(self.high[0], state=NORMAL)
                    self.canvas.tag_raise(self.high[0])
                    self.high.append(self.high.pop(0))
                    self.root.update()
                    time.sleep(.02)
                    self.canvas.itemconfigure(self.high[-1], state=HIDDEN)
                except:
                    return 0

            # Runtime ending
            self.runButton.config(bg='SystemButtonFace')
            self.stopButton.config(bg='SystemButtonFace')
            self.recButton.config(bg='SystemButtonFace')

            self.canvas.itemconfigure(self.block, state=HIDDEN)
            self.nodeButton.config(state=NORMAL)
            self.signalButton.config(state=NORMAL)
            for but in signal_buttons:
                but.delete_but()
            for label in self.labels:
                if not label == 0:
                    label[0].config(state=NORMAL)
                    label[1].config(state=NORMAL)
                    label[2].config(state=NORMAL)
                    label[3].config(state=NORMAL)

            self.runButton.config(state=NORMAL)
            self.stopButton.config(state=DISABLED)
            self.recButton.config(state=DISABLED)
            self.rec.clear()

    def stop(self):
        if self.active[1] and not self.active[0] == 0:
            self.active[0] = 0
            self.active[1] = False
            self.canvas.moveto(self.cross, 1500, 500)
        elif self.active[1]:
            self.active[0] = 1

    def run_select(self, event):
        widgets = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        if len(widgets) > 0:
            matches = []
            for i in widgets:
                for node in self.nodes:
                    if node.image == i:
                        matches.append(node)
            if len(matches) == 1:
                self.active[0] = matches[0]

    def send(self, signal):
        # Returns 0 if signal handled, -1 if signal not found, -2 if not running
        signal = str(signal)
        if self.active[1]:
            if signal in self.labels_active:
                self.active[0].orbit[signal][1].flash()
                if not self.active[0].orbit[signal][2] == 0:
                    self.rec.append([self.canvas.itemcget(self.active[0].text, 'text'),
                                     signal, self.canvas.itemcget(self.active[0].orbit[signal][2].text, 'text')])
                    self.active[0] = self.active[0].orbit[signal][2]
                else:
                    self.rec.append([self.canvas.itemcget(self.active[0].text, 'text'), signal, None])
                return 0
            else: # TODO: Runtime feedback. Flash screen?
                self.rec.append([None, signal, None])
                return -1
        else:
            return -2

    def save(self):
        t = time.localtime()
        out = {'nodes': {}, 'orbits': [], 'labels': []}
        for node in self.nodes:
            out['nodes'][str(node)] = [node.color, node.get_text(), self.canvas.coords(node.text)]
            for orb in node.orbit:
                out['orbits'].append([str(node), orb, str(node.orbit[orb][2])])
        for label in self.labels:
            if not label == 0:
                out['labels'].append([label[0].get(), label[1].get(), label[2].cget('bg')])
        with open(self.kwarg['directory'] + 'FSM_save_' +
                  str(t[7]) + '_' + str(t[3]) + '_' + str(t[4]) + '_' + str(t[5]) +
                  '.txt', 'a', encoding='utf-8') as file:
            restore = sys.stdout
            sys.stdout = file
            json.dump(out, file)
            """
            for l in out:
                print(out[l])
            """
            sys.stdout = restore

    def load_notify(self):
        InputWindow = Toplevel(self.root)
        InputWindow.title("Notify")
        InputWindow.geometry("250x50")
        InputWindow.grab_set()

        Label(InputWindow, text='Drag and drop saves on main canvas to load!').pack()
        Button(InputWindow, text="OK", command=lambda: self.close_window(InputWindow)).pack()

    def load(self, file):
        # Returns -1 on failure
        self.stop()
        rem = []
        for node in self.nodes:
            rem.append(node)
        for r in rem:
            r.delete_load()
        del rem
        for label in self.labels:
            if not label == 0:
                label[0].destroy()
                label[1].destroy()
                label[2].destroy()
                label[3].destroy()
        self.labels.clear()

        try:
            try:
                with open(self.kwarg['directory'] + file, 'r', encoding='utf-8') as f:
                    self.load2(json.load(f))
            except:
                with open(self.kwarg['directory'] + r'{}'.format(file)[1:-1], 'r', encoding='utf-8') as f:
                    self.load2(json.load(f))
        except:
            return -1

    def load_drop(self, event):
        self.stop()
        rem = []
        for node in self.nodes:
            rem.append(node)
        for r in rem:
            r.delete_load()
        del rem
        for label in self.labels:
            if not label == 0:
                label[0].destroy()
                label[1].destroy()
                label[2].destroy()
                label[3].destroy()
        self.labels.clear()
        try:
            with open(event.data, 'r', encoding='utf-8') as file:
                self.load2(json.load(file))
        except:
            with open(r'{}'.format(event.data)[1:-1], 'r', encoding='utf-8') as file:
                self.load2(json.load(file))

    def load2(self, data):
        pointers = {}
        for l in data['labels']:
            self.add_row()
            self.labels[-1][0].delete(0, END)
            self.labels[-1][0].insert(END, l[0])
            self.labels[-1][1].delete(0, END)
            self.labels[-1][1].insert(END, l[1])
            self.labels[-1][2].config(bg=l[2])
        for n in data['nodes']:
            pointers[n] = self.Node(self)
            pointers[n].color = data['nodes'][n][0]
            self.canvas.itemconfigure(pointers[n].image, fill=data['nodes'][n][0])
            self.canvas.itemconfigure(pointers[n].text, text=data['nodes'][n][1])
            self.canvas.itemconfigure(pointers[n].text, fill=self.color_neg(data['nodes'][n][0]))
            x = sum(i for i in self.canvas.coords(pointers[n].image)[::2])/2
            y = sum(i for i in self.canvas.coords(pointers[n].image)[1::2])/2
            self.canvas.move(pointers[n].image, data['nodes'][n][2][0]-x, data['nodes'][n][2][1]-y)
            self.canvas.move(pointers[n].text, data['nodes'][n][2][0] - x, data['nodes'][n][2][1] - y)
        for orb in data['orbits']:
            if not orb[2] == '0': # {Signal: [Color, Tag Object, Linked Node]}
                pointers[orb[0]].orbit[orb[1]][2] = pointers[orb[2]]
        self.update_labels()

    def close_window(self, window):
        window.destroy()

    def share(self): # TODO: idk
        pass

    rec = []
    def record(self):
        if self.active[1]:
            t = time.localtime()
            with open(self.kwarg['directory'] + 'FSM_record_' +
                      str(t[7]) + '_' + str(t[3]) + '_' + str(t[4]) + '_' + str(t[5]) +
                      '.txt', 'a', encoding='utf-8') as file:
                restore = sys.stdout
                sys.stdout = file
                for r in self.rec:
                    print(r)
                sys.stdout = restore

    # Converts a record file to list of signals that can be sent used in module mode for scripted playback
    def record_signals(self):
        pass # TODO: record_signals()


    # To split a coords list into (x,y) tuples:
    #x = [1, 2, 3, 4, 5, 6, 7, 8]
    #[(x[::2][i]+10, x[1::2][i]+20) for i in range(len(x[::2]))]


    # TODO: Multiple active window threads?
    # TODO: Run state options (like sound on a certain node state)
    # TODO: Examples! Binary stream divisibility, fake production machine, etc
    #       Some in save format, some in module format with fake signal waiting, etc
    #       Calculate pi append to display?
    # TODO: Help menu (explain mechanics, controls, module use, colors, save system, etc)
    #       Whip up an image in paint?
    # TODO: Window resizing


if __name__ == "__main__":
    main = Thread({'external':False, 'directory':''})
