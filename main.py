# (c) Pokormi-kota, 2023

from datetime import date
# from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# from matplotlib.backend_bases import key_press_handler
import pandas as pd
from pathlib import Path
from PIL import Image, ImageTk, ImageSequence
# import re
import random
from re import sub
# import tkinter
from tkinter.filedialog import askdirectory, askopenfilenames
from tkinter import _tkinter
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
# from ttkbootstrap.dialogs import dialogs

ASSETS_PATH = Path(__file__).parent / 'assets'

# Next lines add the module directory to the system path to import its other submodules
# import sys, os, inspect
# SCRIPT_DIR = os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))
# sys.path.append(os.path.dirname(SCRIPT_DIR))

# print(os.path.abspath('VibraTable_Template_NIISF.docx'))

from scrolled import ScrolledxyFrame, MessageDialog, AnimatedGif
from Testus import vibraTableOne, INFO_FILE, save_xlsx, staticTableOne, save_static_xlsx, FORCE_FILE
from docGenerator import vibraTable_DocGenerator, statica_DocGenerator, residualStarain_DocGenerator

# another way to add path
OUTPUT_PATH = Path(__file__).parent

def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)


image_files = {
            'coolgif': 'rickroll-roll.gif',
            'logo': 'Logo.png',
            'sizes1': 'Sizes.png',
            'sizes2': 'cat.jpg',
            }


class PPU_Testus(ttk.Frame):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pack(fill=BOTH, expand=YES)

        self.image_files = {
            'forget_mems': ['godfather_w.png',
                            'rememberall.jpg',
                            'kevin.jpg',
                            ],
            'save_mems': ['save1.jpg',
                          'save2.jpg',
                          ]
            }
            
        # Make paned template
        p = ttk.Panedwindow(self, orient=HORIZONTAL)
        p.pack(fill=BOTH, expand=YES)
        
        # left panel
        self.notebook = ttk.Notebook(p)    
        self.left_panel1 = LeftPanelVibration(self.notebook, controller=self, padding=(10,10,10,0))
        self.notebook.add(self.left_panel1, text='Вибростолик')
        self.left_panel2 = LeftPanelStatica(self.notebook, controller=self, padding=(10,10,10,0))
        self.notebook.add(self.left_panel2, text='УПСИ-1')
        self.left_panel3 = LeftPanelResidualStrain(self.notebook, controller=self, padding=(10,10,10,0))
        self.notebook.add(self.left_panel3, text='Ост.Деф.')
        
        # right panel
        self.right_panel = RightPanel(p, self)
        
        p.add(self.notebook)
        p.add(self.right_panel)

        # self.form = 'rectangle'
        self.setvar('shape', 'rectangle')
        
        
        
    def calculate(self):
        
        try:
            n = self.getvar("num_entries")
            self.form = self.getvar('shape')
            h = float(sub(',', '.', self.getvar(f'h')))
            if self.form == 'rectangle':
                a = float(sub(',', '.', self.getvar(f'a')))
                b = float(sub(',', '.', self.getvar(f'b')))
            elif self.form == 'custom':
                a = float(sub(',', '.', self.getvar(f's')))
                b = 1
            # elif self.form == 'primary':   
            #     a = get_mean(self, [f'a_entry{i}' for i in range(1,5)])
            #     b = get_mean(self, [f'b_entry{i}' for i in range(1,5)])
            
            if self.getvar('channels_order') == '1':
                axes = ['1','2']
            elif self.getvar('channels_order') == '0':
                axes = ['2','1']
                
            try:
                self.plots, self.datas, self.results = vibraTableOne(name = self.getvar('name'),
                                        files = [self.getvar(f'info_file{i}') for i in range(n)],
                                        a = a,
                                        b = b,
                                        h = h,
                                        heights = [float(sub(',', '.', self.getvar(f'height{i}'))) for i in range(n)],
                                        axes = axes,
                                        loads = [float(sub(',', '.', self.getvar(f'mass{i}'))) for i in range(n)]
                                )
            except FileNotFoundError as err:
                print(err)
                raise ValueError
            
            # Delete everything from right panel if the button pressed repeatedly
            if (hasattr(self.right_panel, 'scroll_frm') == True) and (self.right_panel.scroll_frm.winfo_exists() == True):
                self.right_panel.clear_it()
            if (hasattr(self.right_panel, 'input') == True) and (self.right_panel.input.winfo_exists() == True):
                self.right_panel.clear_it()
                
            self.right_panel.add_scroll_frame()
            for fig in list(self.plots.values()):
                add_mpl_figure(self.right_panel.scroll_frm, fig)
                
        except (_tkinter.TclError, ValueError):  #
            # Exception called when some initial data is missing
            img = ASSETS_PATH / random.choice(self.image_files['forget_mems'])
            md = MessageDialog("", parent=self.right_panel, title='Ты кое-что забыл', icon=img)
            md.show()
            
    def calculateStatica(self):
        
        try:
            self.form = self.getvar('shape')
            h = float(sub(',', '.', self.getvar(f'h')))
            if self.form == 'rectangle':
                a = float(sub(',', '.', self.getvar(f'a')))
                b = float(sub(',', '.', self.getvar(f'b')))
            elif self.form == 'custom':
                a = float(sub(',', '.', self.getvar(f's')))
                b = 1
            # elif self.form == 'primary':   
            #     a = get_mean(self, [f'a_entry{i}' for i in range(1,5)])
            #     b = get_mean(self, [f'b_entry{i}' for i in range(1,5)])
            
            try:
                init_force = int(self.getvar(f'init_force'))
            except (_tkinter.TclError, ValueError):
                init_force = None
            try:
                cut_start = int(self.getvar(f'cut_start'))
            except (_tkinter.TclError, ValueError):
                cut_start = 0
            try:
                cut_end = int(self.getvar(f'cut_end'))
            except (_tkinter.TclError, ValueError):
                cut_end = 1

            
            try:
                self.plots, self.datas, self.results = staticTableOne(name = self.getvar('name'),
                                        file = self.getvar(f'statica_file'),
                                        a = a,
                                        b = b,
                                        h = h,
                                        P1 = self.getvar(f'P1'),
                                        P2 = self.getvar(f'P2'),
                                        P3 = self.getvar(f'P3'),
                                        forcemeter = self.getvar(f'force'),
                                        cut_start = cut_start,
                                        cut_end = cut_end,
                                        init_force = init_force
                                )
            except FileNotFoundError as err:
                print(err)
                print('Не найден файл "Force_set.txt"')
                raise ValueError
            
            # Delete everything from right panel if the button pressed repeatedly
            if (hasattr(self.right_panel, 'scroll_frm') == True) and (self.right_panel.scroll_frm.winfo_exists() == True):
                self.right_panel.clear_it()
            if (hasattr(self.right_panel, 'input') == True) and (self.right_panel.input.winfo_exists() == True):
                self.right_panel.clear_it()
                
            self.right_panel.add_scroll_frame()
            for fig in list(self.plots.values()):
                add_mpl_figure(self.right_panel.scroll_frm, fig)
                
        except (_tkinter.TclError, ValueError):
            # Exception called when some initial data is missing
            img = ASSETS_PATH / random.choice(self.image_files['forget_mems'])
            md = MessageDialog("", parent=self.right_panel, title='Ты кое-что забыл', icon=img)
            md.show()
            
    def calculateResStrain(self):
        
        try:
            # Delete everything from right panel if the button pressed repeatedly
            # try:
            self.right_panel.clear_it()
            # except _tkinter.TclError:
            #     pass
            self.form = self.getvar('shape')
            h = float(sub(',', '.', self.getvar(f'h')))
            if self.form == 'rectangle':
                a = float(sub(',', '.', self.getvar(f'a')))
                b = float(sub(',', '.', self.getvar(f'b')))
            elif self.form == 'custom':
                a = float(sub(',', '.', self.getvar(f's')))
                b = 1
            # elif self.form == 'primary':   
            #     a = get_mean(self, [f'a_entry{i}' for i in range(1,5)])
            #     b = get_mean(self, [f'b_entry{i}' for i in range(1,5)])
            name = self.getvar('name')
            h_residual = float(sub(',', '.', self.getvar('h_residual')))
            resStrain = (1 - h_residual/h) *100

            
                
            self.right_panel.print_it(f"Остаточная деформация = {resStrain:.2f} %")

                
        except (_tkinter.TclError, ValueError):
            # Exception called when some initial data is missing
            img = ASSETS_PATH / random.choice(self.image_files['forget_mems'])
            md = MessageDialog("", parent=self.right_panel, title='Ты кое-что забыл', icon=img)
            md.show()
        
            

    def save(self):
        # try:
            if hasattr(self, 'plots'):
                self.update_idletasks()
                save_dir = askdirectory()
                n = self.getvar("num_entries")
                h = float(sub(',', '.', self.getvar(f'h')))
                if self.form == 'rectangle':
                    a = float(sub(',', '.', self.getvar(f'a')))
                    b = float(sub(',', '.', self.getvar(f'b')))
                elif self.form == 'custom':
                    a = float(sub(',', '.', self.getvar(f's')))
                    b = 1
                elif self.form == 'primary':
                    a = get_mean(self, [f'a_entry{i}' for i in range(1,5)])
                    b = get_mean(self, [f'b_entry{i}' for i in range(1,5)])
                for name, fig in self.plots.items():
                    fig.savefig(f'{save_dir + "/" + name}', dpi=300)
                save_xlsx(datas = self.datas, 
                          extra_res = self.results,
                          name = self.getvar('name'),
                          savedir = save_dir)
                try:
                    m = float(sub(',', '.', self.getvar(f'm')))
                except (_tkinter.TclError, ValueError):
                    m = None
                    print('Массу забыли')
                    
                try:
                    protocol = self.getvar(f'protocol')
                except (_tkinter.TclError, ValueError):
                    protocol = None
                    print('Номер протокола забыли')
                    
                vibraTable_DocGenerator(
                    name = self.getvar('name'),
                    a = a,
                    b = b,
                    h = h,
                    m = m,
                    heights = [float(sub(',', '.', self.getvar(f'height{i}'))) for i in range(n)],
                    test_date = self.left_panel1.test_date.entry.get(),
                    loads = [float(sub(',', '.', self.getvar(f'mass{i}'))) for i in range(n)],
                    protocol = protocol,
                    results = self.results,
                    savedir = save_dir
                    )
                # If success
                img = ASSETS_PATH / random.choice(self.image_files['save_mems'])
                md = MessageDialog("", title='Всё получилось!', icon=img)
                md.show()
            
            else:
                if (
                    ((hasattr(self.right_panel, 'scroll_frm') == False) or (self.right_panel.scroll_frm.winfo_exists() == False))    
                    and
                    ((hasattr(self.right_panel, 'input') == False) or (self.right_panel.input.winfo_exists() == False))
                    ):
                    if hasattr(self.right_panel, 'anim') and (self.right_panel.anim.winfo_exists() == True):
                        self.right_panel.stop_gif()
                    else:
                        self.right_panel.add_gif()
                print('No pictures yet created')
                
        # except AttributeError:
        #     print('Some error occured')
    
    def save_statica(self):
        if hasattr(self, 'plots'):
            self.update_idletasks()
            save_dir = askdirectory()
            h = float(sub(',', '.', self.getvar(f'h')))
            if self.form == 'rectangle':
                a = float(sub(',', '.', self.getvar(f'a')))
                b = float(sub(',', '.', self.getvar(f'b')))
            elif self.form == 'custom':
                a = float(sub(',', '.', self.getvar(f's')))
                b = 1
            elif self.form == 'primary':
                a = get_mean(self, [f'a_entry{i}' for i in range(1,5)])
                b = get_mean(self, [f'b_entry{i}' for i in range(1,5)])
                
            for name, fig in self.plots.items():
                fig.savefig(f'{save_dir + "/" + name}', dpi=300)
                        
            save_static_xlsx(datas = [self.datas['force'], self.datas['deflection']],
                                    colnames = ['Нагрузка, Н', 'Перемещение, мм'],
                                    name = f"{self.getvar('name')}_load-deflection",
                                    savedir = save_dir)
            save_static_xlsx(datas = [self.results['stress'], self.results['epsylon'], self.results['elasticity']],
                                colnames = ['Удельная нагрузка, МПа','Относительная деф-я, %','Модуль упругости, МПа'],
                                name = f"{self.getvar('name')}_statica",
                                savedir = save_dir)
            
            try:
                m = float(sub(',', '.', self.getvar(f'm')))
            except (_tkinter.TclError, ValueError):
                m = None
                print('Массу забыли')
            try:
                protocol = self.getvar(f'protocol')
            except (_tkinter.TclError, ValueError):
                protocol = None
                print('Номер протокола забыли')
                
            statica_DocGenerator(
                name = self.getvar('name'),
                a = a,
                b = b,
                h = h,
                m = m,
                test_date = self.left_panel2.test_date.entry.get(),
                protocol = protocol,
                results = self.results,
                savedir = save_dir
                )
            
            # If success
            img = ASSETS_PATH / random.choice(self.image_files['save_mems'])
            md = MessageDialog("", title='Всё получилось!', icon=img)
            md.show()
        
        else:
            if (
                ((hasattr(self.right_panel, 'scroll_frm') == False) or (self.right_panel.scroll_frm.winfo_exists() == False))    
                and
                ((hasattr(self.right_panel, 'input') == False) or (self.right_panel.input.winfo_exists() == False))
                ):
                if hasattr(self.right_panel, 'anim') and (self.right_panel.anim.winfo_exists() == True):
                    self.right_panel.stop_gif()
                else:
                    self.right_panel.add_gif()
            print('No pictures yet created')
            
    def save_resStrain(self):
        if hasattr(self.right_panel, 'input') and (self.right_panel.input.winfo_exists() == True):
            self.update_idletasks()
            save_dir = askdirectory()
            h = float(sub(',', '.', self.getvar(f'h')))
            if self.form == 'rectangle':
                a = float(sub(',', '.', self.getvar(f'a')))
                b = float(sub(',', '.', self.getvar(f'b')))
            elif self.form == 'custom':
                a = float(sub(',', '.', self.getvar(f's')))
                b = 1
            elif self.form == 'primary':
                a = get_mean(self, [f'a_entry{i}' for i in range(1,5)])
                b = get_mean(self, [f'b_entry{i}' for i in range(1,5)])
                
            h_residual = float(sub(',', '.', self.getvar('h_residual')))
            
            try:
                m = float(sub(',', '.', self.getvar(f'm')))
            except (_tkinter.TclError, ValueError):
                m = None
                print('Массу забыли')
            try:
                protocol = self.getvar(f'protocol')
            except (_tkinter.TclError, ValueError):
                protocol = None
                print('Номер протокола забыли')
                
            residualStarain_DocGenerator(
                name = self.getvar('name'),
                a = a,
                b = b,
                h = h,
                m = m,
                test_date = self.left_panel3.test_date.entry.get(),
                protocol = protocol,
                h_residual = h_residual,
                savedir = save_dir
                )
            
            # If success
            img = ASSETS_PATH / random.choice(self.image_files['save_mems'])
            md = MessageDialog("", title='Всё получилось!', icon=img)
            md.show()
        
        else:
            if (
                ((hasattr(self.right_panel, 'scroll_frm') == False) or (self.right_panel.scroll_frm.winfo_exists() == False))    
                and
                ((hasattr(self.right_panel, 'input') == False) or (self.right_panel.input.winfo_exists() == False))
                ):
                if hasattr(self.right_panel, 'anim') and (self.right_panel.anim.winfo_exists() == True):
                    self.right_panel.stop_gif()
                else:
                    self.right_panel.add_gif()
            print('No pictures yet created')
                
                
    def run_print(self):
        """Used for test"""
        self.right_panel.print_it(f"Название образца {self.getvar('name')}")
        a = get_mean(self, [f'a_entry{i}' for i in range(1,5)])
        self.right_panel.print_it(f'a_mean = {a}')
        
    def clear_pictures(self):
        self.right_panel.clear_it()
        
        
# Left panel frame
class LeftPanelVibration(ttk.Frame):
    
    def __init__(self, master, controller, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.pack(fill=BOTH, expand=YES)
        self.controller = controller
        
        # header
        hdr_frame = ttk.Frame(self, padding=10, bootstyle=PRIMARY)
        hdr_frame.pack(fill=BOTH, pady=1, side=TOP)

        logo_text = ttk.Label(
            master=hdr_frame,
            text='Исходные данные',
            font=('TkDefaultFixed', 20),
            bootstyle=(INVERSE, PRIMARY)
        )
        logo_text.pack(side=LEFT, padx=10)
        
        
        ## series name input
        name_input = ttk.Frame(self)
        name_input.pack(side=TOP, padx=2, pady=10)
        text = ttk.Label(
            master=name_input,
            text='Номер (название) образца',
            justify = CENTER,
            wraplength = 120,
            # height=5,
            width=20,
            bootstyle=PRIMARY,
        )
        text.pack(side=LEFT, padx=(10,10))
        insert_validate = self.register(validate_empty)
        self.name_input = ttk.Entry(name_input, textvariable='name', validate="focusout", validatecommand=(insert_validate, '%P'))
        self.name_input.pack(side=LEFT, padx=(10,10))
        
        
        # ## production date input
        # product_date = ttk.Frame(self)
        # product_date.pack(side=TOP, padx=2, pady=10)
        # text = ttk.Label(
        #     master=product_date,
        #     text='Дата изготовления',
        #     justify = CENTER,
        #     wraplength = 150,
        #     width=20,
        #     bootstyle=PRIMARY
        # )
        # text.pack(side=LEFT, padx=(10,10))

        # self.product_date = ttk.DateEntry(master=product_date, 
        #                                   dateformat='%Y-%m-%d', 
        #                                   firstweekday=0, 
        #                                   startdate=date.today(),
        #                                   )
        # self.product_date.pack(side=LEFT, padx=(10,10)) 
        
        
        protocol_input = ttk.Frame(self)
        protocol_input.pack(side=TOP, padx=2, pady=10)
        text = ttk.Label(
            master=protocol_input,
            text='Номер протокола (опционально)',
            justify = CENTER,
            wraplength = 120,
            # height=5,
            width=20,
            bootstyle=PRIMARY,
        )
        text.pack(side=LEFT, padx=(10,10))
        self.protocol_input = ttk.Entry(protocol_input, textvariable='protocol')
        self.protocol_input.pack(side=LEFT, padx=(10,10))
        
        
        # Test date input
        test_date = ttk.Frame(self)
        test_date.pack(side=TOP, padx=2, pady=10)
        text = ttk.Label(
            master=test_date,
            text='Дата испытаний',
            justify = CENTER,
            wraplength = 150,
            width=20,
            bootstyle=PRIMARY
        )
        text.pack(side=LEFT, padx=(10,10))
        self.test_date = ttk.DateEntry(master=test_date, 
                                       dateformat='%Y-%m-%d', 
                                       firstweekday=0, 
                                       startdate=date.today(),
                                       )
        self.test_date.pack(side=LEFT, padx=(10,10))        
        
        
        # Sizes input
        sizes = SizesFrm1(self)
        sizes.pack(side=TOP, fill=X, padx=2, pady=10)
                
        
        ## files input
        file_input_frm = ttk.Frame(self)
        file_input_frm.pack(side=TOP, fill=BOTH, padx=2, pady=10, expand=YES)
        file_input_hdr = ttk.Frame(file_input_frm)
        file_input_hdr.pack(side=TOP, fill=X, padx=2, pady=0)
        input_frm =  ScrolledFrame(file_input_frm, bootstyle=DEFAULT, height=160, width=600, autohide=True)
        input_frm.pack(fill=BOTH, pady=1, side=TOP, expand=YES)
        text = ttk.Label(
            master=file_input_hdr,
            text='Пригруз, кг',
            justify = CENTER,
            wraplength = 100,
            width=11,
            bootstyle=PRIMARY
        )
        text.pack(side=RIGHT, padx=2)
        text = ttk.Label(
            master=file_input_hdr,
            text='Высота под нагрузкой(h), мм',
            justify = CENTER,
            wraplength = 100,
            width=15,
            bootstyle=PRIMARY
        )
        text.pack(side=RIGHT, padx=2)
        entry_list, mass_list, height_list = [], [], []
        self.setvar("num_entries", len(entry_list))
        self.add_entry(input_frm, entry_list, mass_list, height_list)
        btn_frm = ttk.Frame(file_input_frm)
        btn_frm.pack(side=BOTTOM, padx=0, pady=1)
        
        
        _func = lambda: self.add_entry(input_frm, entry_list, mass_list, height_list)
        btn = ttk.Button(
            master=btn_frm, 
            # image='Browse', 
            text='Добавить испытание',
            bootstyle=(OUTLINE, SECONDARY),
            command=_func,
            width=20
        )
        btn.pack(side=LEFT, ipadx=5, padx=20, pady=1)
        _func = lambda: self.del_last_frm(input_frm, entry_list, mass_list, height_list)
        btn = ttk.Button(
            master=btn_frm,
            # image='Browse',
            text='Удалить испытание',
            bootstyle=(OUTLINE, SECONDARY),
            command=_func,
            width=20
        )
        btn.pack(side=RIGHT, ipadx=5, padx=20, pady=1)
        
        
        channels_order = ttk.Checkbutton(self, text=f'Обратный порядок каналов', variable='channels_order')
        self.setvar(f'channels_order', '0')
        channels_order.pack(side=TOP, fill=X, padx=20, pady=10, expand=NO)
        
        # Logo
        img = Image.open(ASSETS_PATH / image_files['logo'])
        zoom = 120/img.size[1]
        pixels_x, pixels_y = tuple([int(zoom * x)  for x in img.size])
        logo_img = ImageTk.PhotoImage(img.resize((pixels_x, pixels_y)))
        
        hdr_label = ttk.Label(
            master=self,
            image=logo_img,
            text=f"{ASSETS_PATH / image_files['logo']}",
            bootstyle=(PRIMARY)
        )
        hdr_label.image = logo_img
        hdr_label.pack(side=BOTTOM, padx=10, pady=(10,0), anchor='sw')
        
        
        ## result buttons
        res_btn_frm = ttk.Frame(self)
        res_btn_frm.pack(side=BOTTOM, padx=0, pady=10)
        clear_btn = ttk.Button(
            master=res_btn_frm, 
            # image='Clear', 
            text='Очистить',
            bootstyle=(OUTLINE, DANGER),
            command=self.reset_entries,
            width=10
        )
        clear_btn.pack(side=LEFT, ipadx=5, ipady=5, padx=20, pady=1)
        calc_btn = ttk.Button(
            master=res_btn_frm, 
            # image='Calculate', 
            text='Рассчитать',
            bootstyle=(SUCCESS),
            command=self.calculate, #processing()
            # command=self.run_print
            width=10
            # command=lambda: self.controller.run_print()
        )
        calc_btn.pack(side=RIGHT, ipadx=5, ipady=5, padx=20, pady=1)
    
    def add_entry(self, master, entry_list, mass_list, height_list):
        insert_validate = self.register(validate_empty)
        entry_frm = ttk.Frame(master)
        entry_frm.pack(side=TOP, fill=X, expand=YES, padx=0, pady=8)
        text = ttk.Label(
            master=entry_frm,
            text=f'Файл испытаний {len(entry_list)+1}',
            # font=('TkDefaultFixed', 10),
            justify = CENTER,
            # wraplength = 150,
            width=18,
            bootstyle=PRIMARY
        )
        text.pack(side=LEFT, expand=NO, padx=(10,0))
        info_file = BrowseFileFrm(entry_frm, default_val=INFO_FILE, var_name=f'info_file{len(entry_list)}')
        info_file.pack(side=LEFT, fill=X, expand=YES, padx=(0,10))
        mass = ttk.Entry(entry_frm,
                         textvariable=f'mass{len(entry_list)}',
                         width=10,
                         validate="focusout", validatecommand=(insert_validate, '%P'))
        mass.pack(side=RIGHT, padx=10)
        height = ttk.Entry(entry_frm,
                           textvariable=f'height{len(entry_list)}',
                           width=15,
                           validate="focusout", validatecommand=(insert_validate, '%P'))
        height.pack(side=RIGHT, padx=10)
        entry_list.append(get_entry(info_file))
        mass_list.append(mass.get())
        height_list.append(height.get())
        self.setvar("num_entries", len(entry_list))
        master.yview_moveto(0.5)

        
    def del_last_frm(self, master, entry_list, mass_list, height_list):
        if len(entry_list)>1:
            master.winfo_children()[-1].destroy()
            entry_list.pop()
            mass_list.pop()
            height_list.pop()
            self.setvar("num_entries", len(entry_list))
            master.yview_moveto(1)
        else:
            pass
        

    def reset_entries(self):
        """Clears all entryes in frame"""
        for entry in get_all_entry_widgets(self):
            # print(entry)
            try:
                # default = entry.master.default
                if entry['state'] == NORMAL:
                    entry.delete(0, END)
                    entry.insert(0, entry.master.default)
                else:
                    entry.config(state=NORMAL)
                    entry.delete(0, END)
                    entry.insert(0, entry.master.default)
                    entry.config(state=DISABLED)
                
            except AttributeError:
                if entry['state'] == NORMAL:
                    entry.delete(0, END)
                else:
                    entry.config(state=NORMAL)
                    entry.delete(0, END)
                    entry.config(state=DISABLED)
                    
        self.controller.clear_pictures()

    def calculate(self):
        # message = get_entry(self.start_dir)
        # print(message)
        # test_text = message
        # self.controller.run_print()
        self.controller.calculate()
        # print(self.getvar('start_dir'))
        # print(info_file)
        # master.update
        
# Left panel frame
class LeftPanelStatica(ttk.Frame):
    
    def __init__(self, master, controller, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.pack(fill=BOTH, expand=YES)
        self.controller = controller
        
        # header
        hdr_frame = ttk.Frame(self, padding=10, bootstyle=PRIMARY)
        hdr_frame.pack(fill=BOTH, pady=1, side=TOP)

        logo_text = ttk.Label(
            master=hdr_frame,
            text='Исходные данные',
            font=('TkDefaultFixed', 20),
            bootstyle=(INVERSE, PRIMARY)
        )
        logo_text.pack(side=LEFT, padx=10)
        
        
        ## series name input
        name_input = ttk.Frame(self)
        name_input.pack(side=TOP, padx=2, pady=10)
        text = ttk.Label(
            master=name_input,
            text='Номер (название) образца',
            justify = CENTER,
            wraplength = 120,
            # height=5,
            width=20,
            bootstyle=PRIMARY,
        )
        text.pack(side=LEFT, padx=(10,10))
        insert_validate = self.register(validate_empty)
        self.name_input = ttk.Entry(name_input, textvariable='name', validate="focusout", validatecommand=(insert_validate, '%P'))
        self.name_input.pack(side=LEFT, padx=(10,10))
        
        # file_validate = self.register(validate_file)
        
        # Protocol number
        protocol_input = ttk.Frame(self)
        protocol_input.pack(side=TOP, padx=2, pady=10)
        text = ttk.Label(
            master=protocol_input,
            text='Номер протокола (опционально)',
            justify = CENTER,
            wraplength = 120,
            # height=5,
            width=20,
            bootstyle=PRIMARY,
        )
        text.pack(side=LEFT, padx=(10,10))
        self.protocol_input = ttk.Entry(protocol_input, textvariable='protocol')
        self.protocol_input.pack(side=LEFT, padx=(10,10))
        
    
        
        # Test date input
        test_date = ttk.Frame(self)
        test_date.pack(side=TOP, padx=2, pady=10)
        text = ttk.Label(
            master=test_date,
            text='Дата испытаний',
            justify = CENTER,
            wraplength = 150,
            width=20,
            bootstyle=PRIMARY
        )
        text.pack(side=LEFT, padx=(10,10))
        self.test_date = ttk.DateEntry(master=test_date, 
                                       dateformat='%Y-%m-%d', 
                                       firstweekday=0, 
                                       startdate=date.today(),
                                       )
        self.test_date.pack(side=LEFT, padx=(10,10))        
        
        
        # Sizes input
        sizes = SizesFrm1(self)
        sizes.pack(side=TOP, fill=X, padx=2, pady=10)
                
        
        ## files input
        file_input_frm = ttk.Frame(self)
        file_input_frm.pack(side=TOP, fill=X, expand=NO, padx=0, pady=(30,0))
        text = ttk.Label(
            master=file_input_frm,
            text=f'Файл испытаний',
            # font=('TkDefaultFixed', 10),
            justify = CENTER,
            # wraplength = 150,
            width=18,
            bootstyle=PRIMARY
        )
        text.pack(side=LEFT, expand=NO, padx=(10,0))
        info_file = BrowseFileFrm(file_input_frm, default_val='Выберите файл испытания на УПСИ-1', var_name=f'statica_file')
        info_file.pack(side=LEFT, fill=X, expand=YES, padx=(0,10))
        
        
        # Droplists
        options_input_frm = ttk.Frame(self)
        options_input_frm.pack(side=TOP, fill=X, expand=NO, padx=0, pady=30)
        
        try:
            force_options = list(pd.read_table(FORCE_FILE, encoding='mbcs', header=None, 
                                        skiprows=10, usecols=[0,1]
                                        ).reset_index(drop=True).iloc[:,0])
        except FileNotFoundError:
            print(f'Мы не смогли найти файл {FORCE_FILE}. \nБез него ничего не получится.')
        except ValueError:
            print(f'В структуре файла {FORCE_FILE} ошибка, возможно лишние строки в шапке или лишние столбцы')
            
        forcemeter = MyCombobox(options_input_frm, values=force_options, textvariable='force',
                        default_val=force_options[0], text='Силоизмеритель, кг', width=20, state="readonly")
        forcemeter.pack(side=LEFT, padx=0, pady=0)
        
        
        deflection_options = ['25','50','нет']
        P1 = MyCombobox(options_input_frm, values=deflection_options, textvariable='P1',
                        default_val=deflection_options[1], text='Прогибомер 1, мм', width=18)
        P1.pack(side=LEFT, padx=5, pady=0)
        P2 = MyCombobox(options_input_frm, values=deflection_options, textvariable='P2',
                        default_val=deflection_options[2], text='Прогибомер 2, мм', width=18)
        P2.pack(side=LEFT, padx=5, pady=0)
        P3 = MyCombobox(options_input_frm, values=deflection_options, textvariable='P3',
                        default_val=deflection_options[2], text='Прогибомер 3, мм', width=18)
        P3.pack(side=LEFT, padx=5, pady=0)
        
        
        # Optional record cuts
        cuts_frm = ttk.Frame(self)
        cuts_frm.pack(side=TOP, fill=X, pady=(30,0))
        text = ttk.Label(
            master=cuts_frm,
            text='*Подрезать начало на',
            justify = RIGHT,
            wraplength = 150,
            bootstyle=PRIMARY
        )
        text.pack(side=LEFT, padx=(10,10))
        cut_start = ttk.Entry(cuts_frm, textvariable='cut_start', width=10)
        cut_start.pack(side=LEFT, expand=NO)
        text = ttk.Label(
            master=cuts_frm,
            text='сек',
            justify = RIGHT,
            wraplength = 150,
            bootstyle=PRIMARY
        )
        text.pack(side=LEFT, padx=(10,0))
        
        text = ttk.Label(
            master=cuts_frm,
            text='*Подрезать конец на',
            justify = RIGHT,
            wraplength = 150,
            bootstyle=PRIMARY
        )
        text.pack(side=LEFT, padx=(30,10))
        cut_end = ttk.Entry(cuts_frm, textvariable='cut_end', width=10)
        cut_end.pack(side=LEFT, expand=NO)
        text = ttk.Label(
            master=cuts_frm,
            text='сек',
            justify = RIGHT,
            wraplength = 150,
            bootstyle=PRIMARY
        )
        text.pack(side=LEFT, padx=(10,0))
        
        # insert initial force
        force_frm = ttk.Frame(self)
        force_frm.pack(side=TOP, fill=X, pady=(20,0))
        text = ttk.Label(
            master=force_frm,
            text='*Начальная сила',
            justify = RIGHT,
            wraplength = 150,
            bootstyle=PRIMARY
        )
        text.pack(side=LEFT, padx=(10,10))
        init_force = ttk.Entry(force_frm, textvariable='init_force', width=10)
        init_force.pack(side=LEFT, expand=NO)
        text = ttk.Label(
            master=force_frm,
            text='Н',
            justify = RIGHT,
            wraplength = 150,
            bootstyle=PRIMARY
        )
        text.pack(side=LEFT, padx=(10,0))
        
        
        # Logo
        img = Image.open(ASSETS_PATH / image_files['logo'])
        zoom = 120/img.size[1]
        pixels_x, pixels_y = tuple([int(zoom * x)  for x in img.size])
        logo_img = ImageTk.PhotoImage(img.resize((pixels_x, pixels_y)))
        
        hdr_label = ttk.Label(
            master=self,
            image=logo_img,
            text=f"{ASSETS_PATH / image_files['logo']}",
            bootstyle=(PRIMARY)
        )
        hdr_label.image = logo_img
        hdr_label.pack(side=BOTTOM, padx=10, pady=(10,0), anchor='sw')
        
        
        ## Result buttons
        res_btn_frm = ttk.Frame(self)
        res_btn_frm.pack(side=BOTTOM, padx=0, pady=10)
        clear_btn = ttk.Button(
            master=res_btn_frm, 
            # image='Clear', 
            text='Очистить',
            bootstyle=(OUTLINE, DANGER),
            command=self.reset_entries,
            width=10
        )
        clear_btn.pack(side=LEFT, ipadx=5, ipady=5, padx=20, pady=1)
        calc_btn = ttk.Button(
            master=res_btn_frm, 
            # image='Calculate', 
            text='Рассчитать',
            bootstyle=(SUCCESS),
            command=self.calculate, #processing()
            # command=self.run_print
            width=10
            # command=lambda: self.controller.run_print()
        )
        calc_btn.pack(side=RIGHT, ipadx=5, ipady=5, padx=20, pady=1)
        

    def reset_entries(self):
        """Clears all entryes in frame"""
        for entry in get_all_entry_widgets(self):
            # print(entry)
            try:
                # default = entry.master.default
                if entry['state'] == NORMAL:
                    entry.delete(0, END)
                    entry.insert(0, entry.master.default)
                else:
                    entry.config(state=NORMAL)
                    entry.delete(0, END)
                    entry.insert(0, entry.master.default)
                    entry.config(state=DISABLED)
                
            except AttributeError:
                if entry['state'] == NORMAL:
                    entry.delete(0, END)
                else:
                    entry.config(state=NORMAL)
                    entry.delete(0, END)
                    entry.config(state=DISABLED)
                    
        self.controller.clear_pictures()

    def calculate(self):
        # message = get_entry(self.start_dir)
        # print(message)
        # test_text = message
        # self.controller.run_print()
        self.controller.calculateStatica()
        # print(self.getvar('start_dir'))
        # print(info_file)
        # master.update



class LeftPanelResidualStrain(ttk.Frame):
    
    def __init__(self, master, controller, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.pack(fill=BOTH, expand=YES)
        self.controller = controller
        
        # header
        hdr_frame = ttk.Frame(self, padding=10, bootstyle=PRIMARY)
        hdr_frame.pack(fill=BOTH, pady=1, side=TOP)

        logo_text = ttk.Label(
            master=hdr_frame,
            text='Исходные данные',
            font=('TkDefaultFixed', 20),
            bootstyle=(INVERSE, PRIMARY)
        )
        logo_text.pack(side=LEFT, padx=10)
        
        
        ## series name input
        name_input = ttk.Frame(self)
        name_input.pack(side=TOP, padx=2, pady=10)
        text = ttk.Label(
            master=name_input,
            text='Номер (название) образца',
            justify = CENTER,
            wraplength = 120,
            # height=5,
            width=20,
            bootstyle=PRIMARY,
        )
        text.pack(side=LEFT, padx=(10,10))
        insert_validate = self.register(validate_empty)
        self.name_input = ttk.Entry(name_input, textvariable='name', validate="focusout", validatecommand=(insert_validate, '%P'))
        self.name_input.pack(side=LEFT, padx=(10,10))
        
        # file_validate = self.register(validate_file)
        
        # Protocol number
        protocol_input = ttk.Frame(self)
        protocol_input.pack(side=TOP, padx=2, pady=10)
        text = ttk.Label(
            master=protocol_input,
            text='Номер протокола (опционально)',
            justify = CENTER,
            wraplength = 120,
            # height=5,
            width=20,
            bootstyle=PRIMARY,
        )
        text.pack(side=LEFT, padx=(10,10))
        self.protocol_input = ttk.Entry(protocol_input, textvariable='protocol')
        self.protocol_input.pack(side=LEFT, padx=(10,10))
        
    
        
        # Test date input
        test_date = ttk.Frame(self)
        test_date.pack(side=TOP, padx=2, pady=10)
        text = ttk.Label(
            master=test_date,
            text='Дата испытаний',
            justify = CENTER,
            wraplength = 150,
            width=20,
            bootstyle=PRIMARY
        )
        text.pack(side=LEFT, padx=(10,10))
        self.test_date = ttk.DateEntry(master=test_date, 
                                       dateformat='%Y-%m-%d', 
                                       firstweekday=0, 
                                       startdate=date.today(),
                                       )
        self.test_date.pack(side=LEFT, padx=(10,10))        
        
        
        # Sizes input
        sizes = SizesFrm1(self)
        sizes.pack(side=TOP, fill=X, padx=2, pady=10)
                
        # Residual height
        h_frm = ttk.Frame(self)
        h_frm.pack(side=TOP, padx=2, pady=20)
        text = ttk.Label(
            master=h_frm,
            text='h (после испытания), мм',
            justify = CENTER,
            wraplength = 150,
            bootstyle=PRIMARY
        )
        text.pack(side=LEFT, padx=(10,10))
        self.h = ttk.Entry(h_frm, textvariable='h_residual', validate="focusout", validatecommand=(insert_validate, '%P'), width=15)
        self.h.pack(side=LEFT, padx=(10,10))
        
        
        # Logo
        img = Image.open(ASSETS_PATH / image_files['logo'])
        zoom = 120/img.size[1]
        pixels_x, pixels_y = tuple([int(zoom * x)  for x in img.size])
        logo_img = ImageTk.PhotoImage(img.resize((pixels_x, pixels_y)))
        
        hdr_label = ttk.Label(
            master=self,
            image=logo_img,
            text=f"{ASSETS_PATH / image_files['logo']}",
            bootstyle=(PRIMARY)
        )
        hdr_label.image = logo_img
        hdr_label.pack(side=BOTTOM, padx=10, pady=(10,0), anchor='sw')
        
        
        ## Result buttons
        res_btn_frm = ttk.Frame(self)
        res_btn_frm.pack(side=BOTTOM, padx=0, pady=10)
        clear_btn = ttk.Button(
            master=res_btn_frm, 
            # image='Clear', 
            text='Очистить',
            bootstyle=(OUTLINE, DANGER),
            command=self.reset_entries,
            width=10
        )
        clear_btn.pack(side=LEFT, ipadx=5, ipady=5, padx=20, pady=1)
        calc_btn = ttk.Button(
            master=res_btn_frm, 
            # image='Calculate', 
            text='Рассчитать',
            bootstyle=(SUCCESS),
            command=self.calculate,
            width=10
        )
        calc_btn.pack(side=RIGHT, ipadx=5, ipady=5, padx=20, pady=1)
        

    def reset_entries(self):
        """Clears all entryes in frame"""
        for entry in get_all_entry_widgets(self):
            # print(entry)
            try:
                # default = entry.master.default
                if entry['state'] == NORMAL:
                    entry.delete(0, END)
                    entry.insert(0, entry.master.default)
                else:
                    entry.config(state=NORMAL)
                    entry.delete(0, END)
                    entry.insert(0, entry.master.default)
                    entry.config(state=DISABLED)
                
            except AttributeError:
                if entry['state'] == NORMAL:
                    entry.delete(0, END)
                else:
                    entry.config(state=NORMAL)
                    entry.delete(0, END)
                    entry.config(state=DISABLED)
                    
        self.controller.clear_pictures()

    def calculate(self):
        self.controller.calculateResStrain()


 
        
class SizesFrm(ttk.Frame):
    def __init__(self, master, name, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.pack(fill=X, expand=YES)
        
        # Sizes input
        # sizes = ttk.Frame(self)
        # sizes.pack(side=TOP, fill=X, padx=2, pady=10)
        
        text = ttk.Label(
            master=self,
            text=name,
            # font=('TkDefaultFixed', 10),
            justify = CENTER,
            wraplength = 150,
            bootstyle=PRIMARY
        )
        text.pack(side=LEFT, padx=(10,10))
        
        insert_validate = self.register(validate_empty)
        self.entry1 = ttk.Entry(self, textvariable=f'{name}_entry1', validate="focusout", validatecommand=(insert_validate, '%P'), width=10)
        self.setvar(f'{name}_entry1', 100)
        self.entry1.pack(side=LEFT, expand=YES, padx=10)
        self.entry2 = ttk.Entry(self, textvariable=f'{name}_entry2', validate="focusout", validatecommand=(insert_validate, '%P'), width=10)
        self.setvar(f'{name}_entry2', 100)
        self.entry2.pack(side=LEFT, expand=YES, padx=10)
        self.entry3 = ttk.Entry(self, textvariable=f'{name}_entry3', validate="focusout", validatecommand=(insert_validate, '%P'), width=10)
        self.setvar(f'{name}_entry3', 100)
        self.entry3.pack(side=LEFT, expand=YES, padx=10)
        self.entry4 = ttk.Entry(self, textvariable=f'{name}_entry4', validate="focusout", validatecommand=(insert_validate, '%P'), width=10)
        self.setvar(f'{name}_entry4', 100)
        self.entry4.pack(side=LEFT, expand=YES, padx=10)

class SizesFrm1(ttk.Frame):
    # sizes = ttk.Frame(self)
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.pack(side=TOP, fill=X, padx=2, pady=10)
        
        # self.image_files = {
        #     'sizes1': 'Sizes.png',
        #     'sizes2': 'cat.jpg',
        # }
        
        text = ttk.Label(
        master=self,
        text='Размеры образца',
        justify = CENTER,
        wraplength = 250,
        bootstyle=PRIMARY
        )
        text.pack(side=TOP, padx=(10,10))
        
        self.frm = ttk.Frame(self)
        self.frm.pack(side=TOP)
        self.choice1()
        
        btn_frm = ttk.Frame(self)
        btn_frm.pack(side=BOTTOM, padx=0, pady=1)
        
        choice1_btn = ttk.Button(
            master=btn_frm, 
            # image='Calculate', 
            text='Прямоугольная форма',
            bootstyle=SECONDARY,
            command=self.choice1, #processing()
            width=20
        )
        choice1_btn.pack(side=LEFT, anchor=S, ipadx=5, ipady=5, padx=20, pady=1)
        
        choice2_btn = ttk.Button(
            master=btn_frm, 
            # image='Calculate', 
            text='Произвольная форма',
            bootstyle=SECONDARY,
            command=self.choice2, #processing()
            width=20
        )
        choice2_btn.pack(side=RIGHT, anchor=S, ipadx=5, ipady=5, padx=20, pady=1)
    
    def choice1(self):
        """For rectangle shape."""
        try:
            self.frm.destroy()
        except:
            pass
        self.frm = ttk.Frame(self)
        self.frm.pack(side=TOP)
        self.setvar('shape','rectangle')
        # image
        img = Image.open(ASSETS_PATH / image_files['sizes1'])
        zoom = 150/img.size[1]
        pixels_x, pixels_y = tuple([int(zoom * x)  for x in img.size])
        size_img = ImageTk.PhotoImage(img.resize((pixels_x, pixels_y)))
        size_lbl = ttk.Label(
            master=self.frm,
            image=size_img,
            text=f"{ASSETS_PATH / image_files['sizes1']}",
            bootstyle=PRIMARY
        )
        size_lbl.image = size_img
        size_lbl.pack(side=LEFT, padx=10, pady=10, anchor='w')
        
        a_frm = ttk.Frame(self.frm)
        a_frm.pack(fill=X, expand=YES)
        text = ttk.Label(
            master=a_frm,
            text='a, мм',
            justify = CENTER,
            wraplength = 150,
            bootstyle=PRIMARY
        )
        text.pack(side=LEFT, padx=(10,10))
        
        insert_validate = self.register(validate_empty)
        self.a = ttk.Entry(a_frm, textvariable='a', validate="focusout", validatecommand=(insert_validate, '%P'), width=10)
        self.a.pack(side=TOP, fill=X, expand=YES, padx=2, pady=10)
        self.setvar('a', '100')
        
        b_frm = ttk.Frame(self.frm)
        b_frm.pack(fill=X, expand=YES)
        text = ttk.Label(
            master=b_frm,
            text='b, мм',
            justify = CENTER,
            wraplength = 150,
            bootstyle=PRIMARY
        )
        text.pack(side=LEFT, padx=(10,10))
        self.b = ttk.Entry(b_frm, textvariable='b', validate="focusout", validatecommand=(insert_validate, '%P'), width=10)
        self.b.pack(side=TOP, fill=X, expand=YES, padx=2, pady=10)
        self.setvar('b', '100')
        
        
        h_frm = ttk.Frame(self.frm)
        h_frm.pack(fill=X, expand=YES)
        text = ttk.Label(
            master=h_frm,
            text='h (начальная), мм',
            justify = CENTER,
            wraplength = 150,
            bootstyle=PRIMARY
        )
        text.pack(side=LEFT, padx=(10,10))
        self.h = ttk.Entry(h_frm, textvariable='h', validate="focusout", validatecommand=(insert_validate, '%P'), width=10)
        self.h.pack(side=TOP, fill=X, expand=YES, padx=2, pady=10)
        
        
        m_frm = ttk.Frame(self.frm)
        m_frm.pack(fill=X, expand=YES)
        text = ttk.Label(
            master=m_frm,
            text='Масса, г (опционально)',
            justify = CENTER,
            wraplength = 150,
            bootstyle=PRIMARY
        )
        text.pack(side=LEFT, padx=(10,10))
        self.h = ttk.Entry(m_frm, textvariable='m', validate="focusout", width=10)
        self.h.pack(side=TOP, fill=X, expand=YES, padx=2, pady=10)
        

        
    def choice2(self):
        """For custom shape."""
        try:
            self.frm.destroy()
        except:
            pass
        self.frm = ttk.Frame(self)
        self.frm.pack(side=TOP)
        self.setvar('shape','custom')
        # image
        img = Image.open(ASSETS_PATH / image_files['sizes2'])
        zoom = 150/img.size[1]
        pixels_x, pixels_y = tuple([int(zoom * x)  for x in img.size])
        size_img = ImageTk.PhotoImage(img.resize((pixels_x, pixels_y)))
        size_lbl = ttk.Label(
            master=self.frm,
            image=size_img,
            text=f"{ASSETS_PATH / image_files['sizes2']}",
            bootstyle=PRIMARY
        )
        size_lbl.image = size_img
        size_lbl.pack(side=LEFT, padx=10, pady=10, anchor='w')
        
        s_frm = ttk.Frame(self.frm)
        s_frm.pack(fill=X, expand=YES)
        insert_validate = self.register(validate_empty)
        text = ttk.Label(
            master=s_frm,
            text='S, мм^2',
            justify = CENTER,
            wraplength = 150,
            bootstyle=PRIMARY
        )
        text.pack(side=LEFT, padx=(10,10))
        self.b = ttk.Entry(s_frm, textvariable='s', validate="focusout", validatecommand=(insert_validate, '%P'), width=10)
        self.b.pack(side=TOP, fill=X, expand=YES, padx=2, pady=10)
        self.setvar('s', '100')
        
        
        h_frm = ttk.Frame(self.frm)
        h_frm.pack(fill=X, expand=YES)
        text = ttk.Label(
            master=h_frm,
            text='h (начальная), мм',
            justify = CENTER,
            wraplength = 150,
            bootstyle=PRIMARY
        )
        text.pack(side=LEFT, padx=(10,10))
        self.h = ttk.Entry(h_frm, textvariable='h', validate="focusout", validatecommand=(insert_validate, '%P'), width=10)
        self.h.pack(side=TOP, fill=X, expand=YES, padx=2, pady=10)
        
        
        m_frm = ttk.Frame(self.frm)
        m_frm.pack(fill=X, expand=YES)
        text = ttk.Label(
            master=m_frm,
            text='Масса, кг (опционально)',
            justify = CENTER,
            wraplength = 150,
            bootstyle=PRIMARY
        )
        text.pack(side=LEFT, padx=(10,10))
        self.h = ttk.Entry(m_frm, textvariable='m', validate="focusout", width=10)
        self.h.pack(side=TOP, fill=X, expand=YES, padx=2, pady=10)
        
            
class MyCombobox(ttk.Frame):
    def __init__(self, master, textvariable, default_val, values, text, width=20, state='normal', *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.pack(fill=X, expand=NO)
        
        self.default = default_val
        
        text = ttk.Label(
            master=self,
            text=text,
            # font=('TkDefaultFixed', 10),
            justify = CENTER,
            # wraplength = 150,
            width=width,
            bootstyle=PRIMARY
        )
        text.pack(side=TOP, padx=1)

        entry = ttk.Combobox(self, values=values, width=width, textvariable=textvariable, state=state)
        entry.pack(side=TOP, padx=1)
        # entry.config(state=DISABLED)
        entry.setvar(textvariable, default_val)

        
class BrowseDirFrm(ttk.Frame):
    
    def __init__(self, master, default_val, var_name, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.pack(fill=X, expand=YES)
        
        self.default = default_val

        dir_entry = ttk.Entry(self, textvariable=var_name)
        dir_entry.config(state=DISABLED)
        dir_entry.setvar(var_name, default_val)
        dir_entry.pack(side=LEFT, fill=X, expand=YES)
        
        btn = ttk.Button(
            master=self, 
            # image='Browse', 
            text='Обзор',
            bootstyle=(OUTLINE, SECONDARY),
            command=self.get_directory
        )
        btn.pack(side=RIGHT, ipadx=5, ipady=0, padx=5, pady=1)
        
    def get_directory(self):
        """Open dialogue to get directory and update variable"""
        self.update_idletasks()
        d = askdirectory()
        if d:
            # .cget gets entry's textvariable name
            self.setvar(get_all_entry_widgets(self)[0].cget('textvariable'), d) #there is only one entry
            
        
class BrowseFileFrm(ttk.Frame):
    
    def __init__(self, master, default_val, var_name, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.pack(fill=X, expand=YES)
        
        self.default = default_val

        file_entry = ttk.Entry(self, textvariable=var_name)
        file_entry.pack(side=LEFT, fill=X, expand=YES)
        file_entry.config(state=DISABLED)
        file_entry.setvar(var_name, default_val)

        btn = ttk.Button(
            master=self, 
            # image='Browse',
            text='Обзор',
            bootstyle=(OUTLINE, SECONDARY),
            command=self.get_file
        )
        btn.pack(side=RIGHT, ipadx=5, ipady=0, padx=5, pady=1)
        
    def get_file(self):
        """Open dialogue to get file and update variable"""
        self.update_idletasks()
        d = askopenfilenames()[0]
        if d:
            # .cget gets entry's textvariable name
            self.setvar(get_all_entry_widgets(self)[0].cget('textvariable'), d) #there is only one entry


# Right panel frame
class RightPanel(ttk.Frame):
    
    def __init__(self, master, controller, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.pack(fill=BOTH, expand=YES)
        self.controller = controller            
            
        # header_right
        hdr_r_frame = ttk.Frame(self, padding=10, bootstyle=PRIMARY)
        hdr_r_frame.pack(fill=BOTH, side=TOP, pady=40)
        
        hdr_r_text = ttk.Label(
            master=hdr_r_frame,
            text='Результаты',
            font=('TkDefaultFixed', 20),
            bootstyle=(INVERSE, PRIMARY)
        )
        hdr_r_text.pack(side=LEFT, padx=10)
        
        save_btn = ttk.Button(
            master=self, 
            # image='Calculate', 
            text='Сохранить',
            bootstyle=(SUCCESS),
            command = self.save_command #processing()
            # command=lambda: self.controller.run_print
            
        )
        save_btn.pack(side=BOTTOM, ipadx=5, ipady=5, padx=20, pady=20, anchor=SE)
        
        
    def add_gif(self):
        self.anim = AnimatedGif(self, ASSETS_PATH / image_files['coolgif'])
        self.anim.pack()


    def stop_gif(self):
        # stop GIF
        if self.anim.gifBool == True:
            self.anim.after_cancel(self.anim.cancel)
        # play GIF
        else:
            self.anim.next_frame()
        self.anim.gifBool = not self.anim.gifBool
        
    def add_scroll_frame(self):
        """Add scrolled window to place matplotlib figures"""
        try:
            self.scroll_frm.container.destroy()
        except AttributeError:
            pass
        self.scroll_frm = ScrolledxyFrame(self, bootstyle=DEFAULT)
        self.scroll_frm.pack(fill=BOTH, pady=1, side=TOP, expand=YES)
        
    def print_it(self, text):
        self.input = ttk.Frame(self, padding=10, bootstyle=PRIMARY)
        self.input.pack(fill=BOTH, pady=1, side=TOP)
        
        label = ttk.Label(
            master=self.input,
            text=text,
            bootstyle=(INVERSE, PRIMARY)
        )
        label.pack(side=LEFT, padx=10)
        
    def clear_it(self):
        try:
            if hasattr(self, 'anim'):
                self.anim.destroy()
            if hasattr(self, 'input'):
                self.input.destroy()
            self.scroll_frm.destroy()
            self.scroll_frm.container.destroy()
        except AttributeError:
            pass
        
    def save_command(self):
        if self.controller.notebook.tab(self.controller.notebook.select(), "text") == 'Вибростолик':
            self.controller.save()
        elif self.controller.notebook.tab(self.controller.notebook.select(), "text") == 'УПСИ-1':
            self.controller.save_statica()
        elif self.controller.notebook.tab(self.controller.notebook.select(), "text") == 'Ост.Деф.':
            self.controller.save_resStrain()
        
        
def add_mpl_figure(wid, fig):
    wid.mpl_canvas = FigureCanvasTkAgg(fig, wid)
    wid.mpl_canvas.draw()
    # wid.mpl_canvas.get_tk_widget().pack(side=BOTTOM, fill=BOTH, expand=True)

    wid.toolbar = NavigationToolbar2Tk(wid.mpl_canvas, wid)
    wid.toolbar.update()
    wid.mpl_canvas._tkcanvas.pack(side=BOTTOM, fill=BOTH, expand=False)


def all_children(wid, finList=None, indent=0):
    """Get all children widgets recursively"""
    finList = finList or []
    # print(f"{'   ' * indent}{wid=}")
    children = wid.winfo_children()
    for item in children:
        finList.append(item)
        all_children(item, finList, indent + 1)
    return finList

def get_all_entry_widgets(parent_widget):
    """Get all entry children"""
    entries = []
    for child_widget in all_children(parent_widget):
        if child_widget.winfo_class() == 'TEntry':
            entries.append(child_widget)
    return entries

def get_entry(parent_widget):
    """Get first entry child"""
    # entries = []
    for child_widget in all_children(parent_widget):
        if child_widget.winfo_class() == 'TEntry':
            # entries.append(child_widget.get)
            # print(child_widget.get())
            return child_widget.get()

def validate_empty(entry):
    if entry == "":
        return False
    else:
        return True

def get_mean(wid, varnames_list):
    mean = 0
    for varnamme in varnames_list:
        mean += float(wid.getvar(varnamme))
    mean /= len(varnames_list)
    
    return mean

def quit_me():
    """Properly close tkinter window. Used for gui that contain matplotlib.plot,
    that will otherwise return an error.
    """
    print('quit')
    app.quit()
    app.destroy()

if __name__ == "__main__":

    app = ttk.Window(
        title="PPU-Testus. Обработка испытаний виброизоляции",
        themename="flatly",
        # size=(350, 450),
        # resizable=(False, False),
    )
    PPU_Testus(app)
    app.protocol("WM_DELETE_WINDOW", quit_me)
    app.mainloop()