from itertools import cycle
from pathlib import Path
from PIL import Image, ImageTk, ImageSequence
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.dialogs import dialogs
from tkinter import Pack, Place, Grid
import textwrap

ASSETS_PATH = Path(__file__).parent / 'assets'

class ScrolledxyFrame(ttk.Frame):
    def __init__(
        self,
        master=None,
        padding=2,
        bootstyle=DEFAULT,
        autohide=False,
        height=200,
        width=300,
        scrollheight=None,
        scrollwidth=None,
        **kwargs,
    ):
         # content frame container
        self.container = ttk.Frame(
            master=master,
            relief=FLAT,
            borderwidth=0,
            width=width,
            height=height,
        )
        # self.container.bind("<Configure>", lambda _: self._on_configure)
        self.container.propagate(0)
        
        # content frame
        super().__init__(
            master=self.container,
            padding=padding,
            bootstyle=bootstyle.replace('round', ''),
            width=width,
            height=height,
            **kwargs,
        )
        self.place(rely=1.0, height=scrollheight, width=scrollwidth)   # relwidth=1.0, 
        
        # horizontal scrollbar
        self.hscroll = ttk.Scrollbar(
            master=self.container,
            command=self.xview,
            orient=HORIZONTAL,
            bootstyle=bootstyle,
        )
        self.hscroll.pack(side=BOTTOM, fill=X)
        
        # vertical scrollbar
        self.vscroll = ttk.Scrollbar(
            master=self.container,
            command=self.yview,
            orient=VERTICAL,
            bootstyle=bootstyle,
        )
        self.vscroll.pack(side=RIGHT, fill=Y)
        
        self.winsys = self.tk.call("tk", "windowingsystem")
        
        # setup autohide scrollbar
        self.autohide = autohide
        if self.autohide:
            self.hide_scrollbars()

        # widget event binding
        self.container.bind("<Enter>", self._on_enter, "+")
        self.container.bind("<Leave>", self._on_leave, "+")
        self.container.bind("<Map>", self._on_map, "+")
        self.bind("<<MapChild>>", self._on_map_child, "+")
        # self.bind("<Configure>", self._on_configure, "+")
        
        # delegate content geometry methods to container frame
        _methods = vars(Pack).keys() | vars(Grid).keys() | vars(Place).keys()
        for method in _methods:
            if any(["pack" in method, "grid" in method, "place" in method]):
                # prefix content frame methods with 'content_'
                setattr(self, f"content_{method}", getattr(self, method))
                # overwrite content frame methods from container frame
                setattr(self, method, getattr(self.container, method))
                
    
    def yview(self, *args):
        """Update the vertical position of the content frame within the
        container.

        Parameters:

            *args (List[Any, ...]):
                Optional arguments passed to yview in order to move the
                content frame within the container frame.
        """
        if not args:
            first, _ = self.vscroll.get()
            self.yview_moveto(fraction=first)
        elif args[0] == "moveto":
            self.yview_moveto(fraction=float(args[1]))
        elif args[0] == "scroll":
            self.yview_scroll(number=int(args[1]), what=args[2])
        else:
            return

    def yview_moveto(self, fraction: float):
        """Update the vertical position of the content frame within the
        container.

        Parameters:

            fraction (float):
                The relative position of the content frame within the
                container.
        """
        base, thumb = self._measures()
        if fraction < 0:
            first = 0.0
        elif (fraction + thumb) > 1:
            first = 1 - thumb
        else:
            first = fraction
        self.vscroll.set(first, first + thumb)
        self.content_place(rely=-first * base)

    def yview_scroll(self, number: int, what: str):
        """Update the vertical position of the content frame within the
        container.

        Parameters:

            number (int):
                The amount by which the content frame will be moved
                within the container frame by 'what' units.

            what (str):
                The type of units by which the number is to be interpeted.
                This parameter is currently not used and is assumed to be
                'units'.
        """
        first, _ = self.vscroll.get()
        fraction = (number / 100) + first
        self.yview_moveto(fraction)
    
    def xview(self, *args):
        """Update the vertical position of the content frame within the
        container.

        Parameters:

            *args (List[Any, ...]):
                Optional arguments passed to yview in order to move the
                content frame within the container frame.
        """
        if not args:
            first, _ = self.hscroll.get()
            self.xview_moveto(fraction=first)
        elif args[0] == "moveto":
            self.xview_moveto(fraction=float(args[1]))
        elif args[0] == "scroll":
            self.xview_scroll(number=int(args[1]), what=args[2])
        else:
            return

    def xview_moveto(self, fraction: float):
        """Update the vertical position of the content frame within the
        container.

        Parameters:

            fraction (float):
                The relative position of the content frame within the
                container.
        """
        base, thumb = self._measureswidth()
        if fraction < 0:
            first = 0.0
        elif (fraction + thumb) > 1:
            first = 1 - thumb
        else:
            first = fraction
        
        self.hscroll.set(first, first + thumb)
        self.content_place(relx=-first * base)

    def xview_scroll(self, number: int, what: str):
        """Update the vertical position of the content frame within the
        container.

        Parameters:

            number (int):
                The amount by which the content frame will be moved
                within the container frame by 'what' units.

            what (str):
                The type of units by which the number is to be interpeted.
                This parameter is currently not used and is assumed to be
                'units'.
        """
        first, _ = self.hscroll.get()
        fraction = (number / 100) + first
        self.xview_moveto(fraction)
    
    def _add_scroll_binding(self, parent):
        """Recursive adding of scroll binding to all descendants."""
        children = parent.winfo_children()
        for widget in [parent, *children]:
            bindings = widget.bind()
            if self.winsys.lower() == "x11":
                if "<Button-4>" in bindings or "<Button-5>" in bindings:
                    continue
                else:
                    widget.bind("<Button-4>", self._on_mousewheel, "+")
                    widget.bind("<Button-5>", self._on_mousewheel, "+")
            else:
                if "<MouseWheel>" not in bindings:
                    widget.bind("<MouseWheel>", self._on_mousewheel, "+")
            if widget.winfo_children() and widget != parent:
                self._add_scroll_binding(widget)

    def _del_scroll_binding(self, parent):
        """Recursive removal of scrolling binding for all descendants"""
        children = parent.winfo_children()
        for widget in [parent, *children]:
            if self.winsys.lower() == "x11":
                widget.unbind("<Button-4>")
                widget.unbind("<Button-5>")
            else:
                widget.unbind("<MouseWheel>")
            if widget.winfo_children() and widget != parent:
                self._del_scroll_binding(widget)

    def enable_scrolling(self):
        """Enable mousewheel scrolling on the frame and all of its
        children."""
        self._add_scroll_binding(self)

    def disable_scrolling(self):
        """Disable mousewheel scrolling on the frame and all of its
        children."""
        self._del_scroll_binding(self)
    
    def hide_scrollbars(self):
        """Hide the scrollbars."""
        self.vscroll.pack_forget()
        self.hscroll.pack_forget()

    def show_scrollbars(self):
        """Show the scrollbars."""
        self.vscroll.pack(side=RIGHT, fill=Y)
        self.hscroll.pack(side=BOTTOM, fill=X)
    
    def _measures(self):
        """Measure the base size of the container and the thumb size
        for use in the yview methods"""
        outer = self.container.winfo_height()
        # print('outer height = ', outer)
        inner = max([self.winfo_reqheight(), outer])
        # print(self.winfo_height())
        # print(self.winfo_reqheight())
        base = inner / outer
        if inner == outer:
            thumb = 1.0
        else:
            thumb = outer / inner
        return base, thumb
    
    def _measureswidth(self):
        """Measure the base size of the container and the thumb size
        for use in the yview methods"""
        outer = self.container.winfo_width()
        # print('outer width = ', outer)
        inner = max([self.winfo_reqwidth(), outer])
        # print(self.winfo_reqwidth())
        # print(self.winfo_width())
        base = inner / outer
        if inner == outer:
            thumb = 1.0
        else:
            thumb = outer / inner
        return base, thumb
    
    def _on_map_child(self, event):
        """Callback for when a widget is mapped to the content frame."""
        if self.container.winfo_ismapped():
            self.yview()
            self.xview()
            
    def _on_enter(self, event):
        """Callback for when the mouse enters the widget."""
        self.enable_scrolling()
        if self.autohide:
            self.show_scrollbars()

    def _on_leave(self, event):
        """Callback for when the mouse leaves the widget."""
        self.disable_scrolling()
        if self.autohide:
            self.hide_scrollbars()
    
    def _on_configure(self, event):
        """Callback for when the widget is configured"""
        self.xview()
        self.yview()

    def _on_map(self, event):
        self.yview()
        self.xview()
        
    def _on_mousewheel(self, event):
        """Callback for when the mouse wheel is scrolled."""
        if self.winsys.lower() == "win32":
            delta = -int(event.delta / 120)
        elif self.winsys.lower() == "aqua":
            delta = -event.delta
        elif event.num == 4:
            delta = -10
        elif event.num == 5:
            delta = 10
        self.yview_scroll(delta, UNITS)

class ScrolledxyFrame1(ScrolledFrame):
    def __init__(
        self,
        master=None,
        padding=2,
        bootstyle=DEFAULT,
        autohide=False,
        height=200,
        width=300,
        scrollheight=None,
        quantity=2,
        **kwargs,
    ):
                
        super().__init__(
            master,
            padding,
            bootstyle,
            autohide=False,
            height=height,
            width=width,
            scrollheight=scrollheight,
            **kwargs,
            )
        
        self.place(rely=0.0, relwidth=1.0)
        self.quantity = quantity
        
        
        
        # horizontal scrollbar
        self.hscroll = ttk.Scrollbar(
            master=self.container,
            command=self.xview,
            orient=HORIZONTAL,
            bootstyle=bootstyle,
        )
        self.hscroll.pack(side=BOTTOM, fill=X)
        
        self.container.bind("<Configure>", lambda _: self._on_configure)
        self.container.propagate(0)
        
        self.autohide = autohide
        
        # delegate content geometry methods to container frame
        _methods = vars(Pack).keys() | vars(Grid).keys() | vars(Place).keys()
        for method in _methods:
            if any(["pack" in method, "grid" in method, "place" in method]):
                # prefix content frame methods with 'content_'
                setattr(self, f"content_{method}", getattr(self, method))
                # overwrite content frame methods from container frame
                setattr(self, method, getattr(self.container, method))
        
    def xview(self, *args):
        """Update the vertical position of the content frame within the
        container.

        Parameters:

            *args (List[Any, ...]):
                Optional arguments passed to yview in order to move the
                content frame within the container frame.
        """
        if not args:
            first, _ = self.hscroll.get()
            self.xview_moveto(fraction=first)
        elif args[0] == "moveto":
            self.xview_moveto(fraction=float(args[1]))
        elif args[0] == "scroll":
            self.xview_scroll(number=int(args[1]), what=args[2])
        else:
            return

    def xview_moveto(self, fraction: float):
        """Update the vertical position of the content frame within the
        container.

        Parameters:

            fraction (float):
                The relative position of the content frame within the
                container.
        """
        base, thumb = self._measureswidth()
        if fraction < 0:
            first = 0.0
        elif (fraction + thumb) > 1:
            first = 1 - thumb
        else:
            first = fraction
        self.hscroll.set(first, first + thumb)
        self.content_place(relx=-first * base)

    def xview_scroll(self, number: int, what: str):
        """Update the vertical position of the content frame within the
        container.

        Parameters:

            number (int):
                The amount by which the content frame will be moved
                within the container frame by 'what' units.

            what (str):
                The type of units by which the number is to be interpeted.
                This parameter is currently not used and is assumed to be
                'units'.
        """
        first, _ = self.hscroll.get()
        fraction = (number / 100) + first
        self.xview_moveto(fraction)
        
    def hide_scrollbars(self):
        """Hide the scrollbars."""
        self.vscroll.pack_forget()
        self.hscroll.pack_forget()

    def show_scrollbars(self):
        """Show the scrollbars."""
        self.vscroll.pack(side=RIGHT, fill=Y)
        self.hscroll.pack(side = BOTTOM, fill=X)
        
    def _measureswidth(self):
        """Measure the base size of the container and the thumb size
        for use in the yview methods"""
        outer = self.container.winfo_width()
        inner = max([self.winfo_width(), outer])
        base = inner / outer
        if inner == outer:
            thumb = 1.0
        else:
            thumb = outer / inner
        return base, thumb
        
    def _on_map_child(self, event):
        """Callback for when a widget is mapped to the content frame."""
        if self.container.winfo_ismapped():
            self.yview()
            self.xview()
            
    def _on_configure(self, event):
        """Callback for when the widget is configured"""
        self.yview()
        self.xview()

    def _on_map(self, event):
        self.yview()
        self.xview()

    # def _on_mousewheel(self, event):
    #     """Callback for when the mouse wheel is scrolled."""
    #     if self.winsys.lower() == "win32":
    #         delta = -int(event.delta / 120)
    #     elif self.winsys.lower() == "aqua":
    #         delta = -event.delta
    #     elif event.num == 4:
    #         delta = -10
    #     elif event.num == 5:
    #         delta = 10
    #     self.yview_scroll(delta, UNITS)

class MessageDialog(dialogs.MessageDialog):
    def __init__(
        self,
        message,
        title=" ",
        buttons=None,
        command=None,
        width=50,
        parent=None,
        alert=False,
        default=None,
        padding=(20, 20),
        icon=None,
        **kwargs,
    ):
        
        super().__init__(
            message,
            title,
            buttons,
            command,
            width,
            parent,
            alert,
            default,
            padding,
            icon,
            **kwargs,
        )
        
        # self._icon = icon
        
    def create_body(self, master):
        """Overrides the parent method; adds the message section."""
        container = ttk.Frame(master, padding=self._padding)
        if self._icon:
            try:
                # assume this is image data
                self._img = ttk.PhotoImage(data=self._icon)
                icon_lbl = ttk.Label(container, image=self._img)
                icon_lbl.pack(side=LEFT, padx=5)
            except:
                try:
                    # assume this is a file path
                    self._img = ttk.PhotoImage(file=self._icon)
                    icon_lbl = ttk.Label(container, image=self._img)
                    icon_lbl.pack(side=LEFT, padx=5)
                except:
                    # icon is neither data nor a valid file path
                    try:
                        # assume this is path to jpg file
                        self._img = ImageTk.PhotoImage(Image.open(self._icon))
                        icon_lbl = ttk.Label(container, image=self._img)
                        icon_lbl.pack(side=LEFT, padx=5)
                    except:
                        # icon is neither data nor a valid file path
                        print("MessageDialog icon is invalid")
                    
        if self._message:
            for msg in self._message.split("\n"):
                message = "\n".join(textwrap.wrap(msg, width=self._width))
                message_label = ttk.Label(container, text=message)
                message_label.pack(pady=(0, 3), fill=X, anchor=N)
        container.pack(fill=X, expand=True)

class AnimatedGif(ttk.Frame):
    """Creates a frame with .gif given in `file_path`."""
    def __init__(self, master, file_path):
        super().__init__(master, width=400, height=300)

        # create a cycle iterator
        with Image.open(file_path) as im:
            # create a sequence
            sequence = ImageSequence.Iterator(im)
            images = [ImageTk.PhotoImage(s) for s in sequence]
            self.image_cycle = cycle(images)

            # length of each frame
            self.framerate = im.info["duration"]

        self.img_container = ttk.Label(self, image=next(self.image_cycle))
        self.img_container.pack(fill="both", expand="yes")
        self.after(self.framerate, self.next_frame)
        self.gifBool = True  # defines that gif has started
        
    # play GIF
    def next_frame(self):
        """Update the image for each frame"""
        self.img_container.configure(image=next(self.image_cycle))
        # self.after(self.framerate, self.next_frame)
        self.cancel = self.after(self.framerate, self.next_frame)
        
if __name__ == "__main__":
    app = ttk.Window()

    # sf = ScrolledxyFrame(app, autohide=True)
    # sf.pack(fill=BOTH, expand=YES, padx=10, pady=10)

    img = ASSETS_PATH / 'godfather.jpg'
    md = MessageDialog("Задумайся", parent=app, icon=img)
    md.show()

    # add a large number of checkbuttons into the scrolled frame
    # for x in range(10):
    #     ttk.Button(sf, text=f"Checkbutton {x}").pack(side=LEFT, anchor=NW)
        
    # for x in range(20):
    #     ttk.Checkbutton(sf, text=f"Checkbutton {x}").pack(side=TOP, anchor=W)
    
    app.mainloop()

