#!/usr/bin/env python3
# V. 2.0

# use headbar
USE_HEADBAR = 1

# toolbar icon size
TICON_SIZE = 36

import gi
gi.require_version('EvinceDocument', '3.0')
gi.require_version('Gtk', '3.0')
gi.require_version('EvinceView', '3.0')
from gi.repository import Gtk, Gdk, GLib, Gio
from gi.repository import EvinceDocument
from gi.repository import EvinceView
import os,sys, datetime, subprocess

if (len(sys.argv) != 2):
    docfile=""
else:
    docfile=os.path.abspath(sys.argv[1])

file = Gio.File.new_for_path(sys.argv[1])
ftype = None
try:
    file_info = file.query_info('standard::*', Gio.FileQueryInfoFlags.NONE, None)
    ftype = Gio.FileInfo.get_content_type(file_info)
except:
    ftype = None

#
settings = None

# window size
WWIDTH = 0
WHEIGHT = 0
conf_file = os.path.dirname(os.path.abspath(sys.argv[0]))+"/conf.cfg"
with open(conf_file, "r") as fconf:
    WWIDTH = int(fconf.readline())
    WHEIGHT = int(fconf.readline())

#==========================================================


class passwordWin(Gtk.Dialog):
    def __init__(self, _parent):
        super().__init__(title="Password", transient_for=None, flags=0)
        self._parent = _parent
        self.main_box = self.get_content_area()
        #
        lbl = Gtk.Label(label="insert the password")
        self.main_box.add(lbl)
        #
        self.entry = Gtk.Entry.new()
        self.entry.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        self.entry.set_visibility(False)
        self.entry.set_invisible_char("*")
        self.main_box.add(self.entry)
        #
        btn = Gtk.Button(label="Accept")
        btn.connect('clicked', self.btn_clicked)
        self.main_box.add(btn)
        #
        self._value = 0
        #
        self.show_all()
    
    def btn_clicked(self, btn):
        _text = self.entry.get_text()
        if _text:
            self._value = _text
        self.close()


class EvinceViewer:

    def __init__(self):

        # create main window
        self.window = Gtk.Window()
        #
        self.window.set_title("Pdf Reader - "+os.path.basename(docfile))
        self.window.set_default_size(WWIDTH, WHEIGHT)
        pixbuf = Gtk.IconTheme.get_default().load_icon("applications-office", TICON_SIZE, 0)
        self.window.set_icon(pixbuf)
        #
        self.window.connect('destroy', Gtk.main_quit)
        self.window.connect('delete-event', Gtk.main_quit)
        self.window.connect("key-press-event", self.keypress)
        self.window.connect('scroll-event', self.fscroll_event)
        self.window.connect('show', self.show_event)
        # headbar
        if USE_HEADBAR:
            header = Gtk.HeaderBar(title="Pdf Reader - "+os.path.basename(docfile))
            header.props.show_close_button = True
            self.window.set_titlebar(header)
        
        # horizontal box
        self.hbox = Gtk.Box(orientation=0, spacing=0)
        self.window.add(self.hbox)
        # 
        self.main_box = Gtk.Box(orientation=1, spacing=0)
        self.hbox.pack_end(self.main_box, True, True, 0)
        # box for buttons - orizzontale
        button_box = Gtk.Box(orientation=0, spacing=5)
        self.main_box.add(button_box)
        
        # show history button
        pixbuf = Gtk.IconTheme.get_default().load_icon("address-book-new", TICON_SIZE, 0)
        hist_image = Gtk.Image.new_from_pixbuf(pixbuf)
        hist_button = Gtk.Button(image=hist_image)
        hist_button.set_tooltip_text("Bookmarks")
        button_box.add(hist_button)
        hist_button.connect("clicked", self.on_hist_button)
        hist_button.set_sensitive(False)
        
        # separator
        separator = Gtk.Separator()
        button_box.add(separator)
        # # open file button
        # pixbuf = Gtk.IconTheme.get_default().load_icon("document-open", TICON_SIZE, 0)
        # openf_image = Gtk.Image.new_from_pixbuf(pixbuf)
        # button_openf = Gtk.Button(image=openf_image)
        # button_openf.set_tooltip_text("Open a new file")
        # button_box.add(button_openf)
        # button_openf.connect("clicked", self.on_open_file)
        
        # separator
        separator = Gtk.Separator()
        button_box.add(separator)
        # print button
        pixbuf = Gtk.IconTheme.get_default().load_icon("document-print", TICON_SIZE, 0)
        print_image = Gtk.Image.new_from_pixbuf(pixbuf)
        button_print = Gtk.Button(image=print_image)
        button_print.set_tooltip_text("Print")
        button_box.add(button_print)
        
        # separator
        separator = Gtk.Separator()
        button_box.add(separator)
        # dual/single page button
        pixbuf = Gtk.IconTheme.get_default().load_icon("gtk-copy", TICON_SIZE, 0)
        dpage_image = Gtk.Image.new_from_pixbuf(pixbuf)
        button_dpage = Gtk.Button(image=dpage_image)
        self.dpage_state = False
        button_dpage.set_tooltip_text("Dual/Single page")
        button_box.add(button_dpage)
        button_dpage.connect("clicked", self.on_dual_page)
        # separator
        separator = Gtk.Separator()
        button_box.add(separator)
        # entry
        self.curr_entry = Gtk.Entry()
        self.curr_entry.props.xalign = 1
        self.curr_entry.props.width_chars = 5
        self.curr_entry.set_text("1")
        button_box.add(self.curr_entry)
        # 
        self.total_label = Gtk.Label()
        button_box.add(self.total_label)
        # previous page button
        pixbuf = Gtk.IconTheme.get_default().load_icon("go-previous", TICON_SIZE, 0)
        p_image = Gtk.Image.new_from_pixbuf(pixbuf)
        p_button = Gtk.Button(image=p_image)
        p_button.set_tooltip_text("Previous page")
        p_button.connect("clicked", self.prev_button)
        button_box.add(p_button)
        # next page button
        pixbuf = Gtk.IconTheme.get_default().load_icon("go-next", TICON_SIZE, 0)
        n_image = Gtk.Image.new_from_pixbuf(pixbuf)
        n_button = Gtk.Button(image=n_image)
        n_button.set_tooltip_text("Next page")
        n_button.connect("clicked", self.next_button)
        button_box.add(n_button)
        # separator
        separator = Gtk.Separator()
        button_box.add(separator)
        # zoom +
        pixbuf = Gtk.IconTheme.get_default().load_icon("zoom-in", TICON_SIZE, 0)
        zoomp_image = Gtk.Image.new_from_pixbuf(pixbuf)
        self.bt_zoomp = Gtk.Button(image=zoomp_image)
        self.bt_zoomp.set_tooltip_text("Zoom+")
        button_box.add(self.bt_zoomp)
        self.bt_zoomp.connect("clicked", self.fbt_zoomp)
        # label per lo zoom
        self.zoom_label = Gtk.Label()
        
        button_box.add(self.zoom_label)
        # zoom -
        pixbuf = Gtk.IconTheme.get_default().load_icon("zoom-out", TICON_SIZE, 0)
        zoomm_image = Gtk.Image.new_from_pixbuf(pixbuf)
        self.bt_zoomm = Gtk.Button(image=zoomm_image)
        self.bt_zoomm.set_tooltip_text("Zoom-")
        button_box.add(self.bt_zoomm)
        self.bt_zoomm.connect("clicked", self.fbt_zoomm)
        
        # separator
        separator = Gtk.Separator()
        button_box.add(separator)
        # rotate left button
        pixbuf = Gtk.IconTheme.get_default().load_icon("object-rotate-left", TICON_SIZE, 0)
        rl_image = Gtk.Image.new_from_pixbuf(pixbuf)
        rl_button = Gtk.Button(image=rl_image)
        rl_button.set_tooltip_text("Rotate left")
        button_box.add(rl_button)
        rl_button.connect("clicked", self.on_rotate_left)
        # rotate right button
        pixbuf = Gtk.IconTheme.get_default().load_icon("object-rotate-right", TICON_SIZE, 0)
        rr_image = Gtk.Image.new_from_pixbuf(pixbuf)
        rr_button = Gtk.Button(image=rr_image)
        rr_button.set_tooltip_text("Rotate right")
        button_box.add(rr_button)
        rr_button.connect("clicked", self.on_rotate_right)
        
        # separator
        separator = Gtk.Separator()
        button_box.add(separator)
        # search button
        pixbuf = Gtk.IconTheme.get_default().load_icon("edit-find", TICON_SIZE, 0)
        search_image = Gtk.Image.new_from_pixbuf(pixbuf)
        search_button = Gtk.Button(image=search_image)
        search_button.set_tooltip_text("Find")
        button_box.add(search_button)
            # creating a popover
        sb_pover = Gtk.Popover.new(search_button)
        sb_box = Gtk.Box(orientation=0, spacing=0)
                # widgets
        self.sb_entry = Gtk.Entry()
        self.sb_entry.set_alignment(1)
        self.sb_entry.set_size_request(300, -1)
        sb_box.add(self.sb_entry)
        self.sb_entry.connect("activate", self.on_entry_activate, sb_pover)
        sb_button = Gtk.Button(label="Search")
        sb_box.add(sb_button)
        sb_pover.add(sb_box)
        search_button.connect("clicked", self.on_sb_button_click, sb_pover)
        sb_button.connect("clicked", self.on_enter, sb_pover)
        #
        # next result button
        pixbuf = Gtk.IconTheme.get_default().load_icon("go-next", TICON_SIZE, 0)
        fnext_image = Gtk.Image.new_from_pixbuf(pixbuf)
        fnext_button = Gtk.Button(image=fnext_image)
        fnext_button.set_tooltip_text("Next result")
        button_box.add(fnext_button)
        fnext_button.connect("clicked", self.ffnext_button)
        # previous result button
        pixbuf = Gtk.IconTheme.get_default().load_icon("go-previous", TICON_SIZE, 0)
        fprev_image = Gtk.Image.new_from_pixbuf(pixbuf)
        fprev_button = Gtk.Button(image=fprev_image)
        fprev_button.set_tooltip_text("Previous result")
        button_box.add(fprev_button)
        fprev_button.connect("clicked", self.ffprev_button)
        # copy to clipboard
        self.copy_text_to_clipboard = ""
        # separator
        separator = Gtk.Separator()
        button_box.add(separator)
        # copy to clipboard button
        pixbuf = Gtk.IconTheme.get_default().load_icon("edit-paste", TICON_SIZE, 0)
        clip_image = Gtk.Image.new_from_pixbuf(pixbuf)
        clip_button = Gtk.Button(image=clip_image)
        clip_button.set_tooltip_text("Copy to clipboard")
        button_box.add(clip_button)
        clip_button.connect("clicked", self.on_clip_button)
        
        # separator
        separator = Gtk.Separator()
        button_box.add(separator)
        # info button
        pixbuf = Gtk.IconTheme.get_default().load_icon("gnome-help", TICON_SIZE, 0)
        info_image = Gtk.Image.new_from_pixbuf(pixbuf)
        info_button = Gtk.Button(image=info_image)
        info_button.set_tooltip_text("Document info")
        button_box.add(info_button)
        # annotations
        pixbuf = Gtk.IconTheme.get_default().load_icon("annotations-text-symbolic", TICON_SIZE, 0)
        annot_image = Gtk.Image.new_from_pixbuf(pixbuf)
        # annot_button = Gtk.Button(image=annot_image)
        annot_button = Gtk.MenuButton(image=annot_image)
        
        menu = Gtk.Menu()
        annot_button.set_popup(menu)
        menuitem1 = Gtk.MenuItem("Highlight")
        menuitem1.connect("activate", self.on_menuitem_activated, "h")
        menu.append(menuitem1)
        menuitem2 = Gtk.MenuItem("Icon")
        menuitem2.connect("activate", self.on_menuitem_activated, "i")
        menu.append(menuitem2)
        menu.show_all()
        
        annot_button.set_tooltip_text("Annotations")
        annot_button.hide()
        button_box.add(annot_button)
        #
        # night mode
        pixbuf = Gtk.IconTheme.get_default().load_icon("format-justify-fill", TICON_SIZE, 0)
        night_mode_image = Gtk.Image.new_from_pixbuf(pixbuf)
        night_mode_button= Gtk.Button(image=night_mode_image)
        night_mode_button.set_tooltip_text("Night mode")
        night_mode_button.connect("clicked", self.night_mode)
        button_box.add(night_mode_button)
        night_mode_button.show()
        # separator
        separator = Gtk.Separator()
        button_box.add(separator)
        #
        # save document button
        pixbuf = Gtk.IconTheme.get_default().load_icon("gtk-save", TICON_SIZE, 0)
        save_image = Gtk.Image.new_from_pixbuf(pixbuf)
        self.save_button = Gtk.Button(image=save_image)
        self.save_button.set_tooltip_text("Save this document")
        button_box.add(self.save_button)
        self.save_button.connect("clicked", self.fsave_button)
        self._is_modified = False
        # self.save_button.set_sensitive(False)
        # separator
        #separator = Gtk.Separator()
        #button_box.add(separator)
        #
        # quit the program button
        pixbuf = Gtk.IconTheme.get_default().load_icon("exit", TICON_SIZE, 0)
        quit_image = Gtk.Image.new_from_pixbuf(pixbuf)
        quit_button = Gtk.Button(image=quit_image)
        quit_button.set_tooltip_text("Quit")
        button_box.pack_end(quit_button, False, False, 0)
        quit_button.connect("clicked", self.on_quit)
        #
        # scrolled window for the viewer
        scroll = Gtk.ScrolledWindow()
        self.main_box.pack_start(scroll, True, True, 0)
        if (len(sys.argv) != 2):
            self.info_dialog("Usage:\npdfreader.py FILE")
            sys.exit()
        if ftype == None:
            self.info_dialog(os.path.basename(sys.argv[1])+":\nError while opening the file\nor type not supported.")
            sys.exit()
        # EVINCE DOCUMENT
        EvinceDocument.init()
        self._has_password = 0
        # load the document or exit
        try:
            self.doc = EvinceDocument.Document.factory_get_document('file://'+docfile)
        except Exception as E:
            # is encripted
            if E.code == 2:
                self._has_password = 1
                self.info_dialog(os.path.basename(sys.argv[1])+":\nThe file is password protected.")
                sys.exit()
            else:
                self.info_dialog(os.path.basename(sys.argv[1])+":\nError while opening the file.")
                sys.exit()
        #
        self.total_label.set_label(str(self.doc.get_n_pages()))
        # TOC of doc by links
        try:
            if self.doc.has_document_links():
                self.job_links = EvinceView.JobLinks.new(self.doc)
                EvinceView.Job.scheduler_push_job(self.job_links,
                            EvinceView.JobPriority.PRIORITY_NONE)
                self.job_links.connect('finished', self.index_load)
            else:
                hist_button.set_sensitive(False)
        except:
            pass
        # evince view
        self.view = EvinceView.View()
        #
        self.view.can_zoom_in()
        self.view.can_zoom_out()
        # evince model
        self.model = EvinceView.DocumentModel()
        self.model.set_document(self.doc)
        self.view.set_model(self.model)
        self.model.props.sizing_mode = EvinceView.SizingMode.FIT_WIDTH #AUTOMATIC FIT_PAGE FIT_WIDTH 
        self.page = EvinceDocument.Page.new(0)

        # add to scroll window
        scroll.add(self.view)
        self.window.show_all()
        self.fullscreen=False
        
        # print the page - needed to show the print dialog
        # workaround for the cbr file types and maybe others
        try:
            self.evprint = EvinceView.PrintOperation.new(self.doc)
            button_print.connect("clicked", self.button_clicked)
        except:
            pass
        #
        self.window.connect("check-resize", self.on_win_resize)
        self.view.connect("selection-changed", self.view_sel_changed)
        self.model.connect("page-changed", self.model_page_changed)
        self.curr_entry.connect("activate", self.curr_entry_activate)
        #
        gdi = self.doc.get_info()
        info_list = []
        info_list.append(gdi.author or "")
        info_list.append(gdi.modified_date or "")
        info_list.append(gdi.creator or "")
        info_list.append(gdi.format or "")
        info_list.append(gdi.n_pages or "")
        info_list.append(gdi.producer or "")
        info_button.connect("clicked", self.finfo_button, info_list)
        # window size constants
        self.win_width = self.window.get_size().width
        self.win_height = self.window.get_size().height
        # treemodel
        self.hstore = Gtk.TreeStore(str, int)
        self.tree = Gtk.TreeView.new_with_model(self.hstore)
        self.tree.set_show_expanders(True)
        self.tree.set_activate_on_single_click(True)
        self.tree.connect("row-activated", self.on_single_click)
        renderer1 = Gtk.CellRendererText()
        column1 = Gtk.TreeViewColumn("Title", renderer1, text=0)
        self.tree.append_column(column1)
        renderer2 = Gtk.CellRendererText()
        column2 = Gtk.TreeViewColumn("Page", renderer2, text=1)
        self.tree.append_column(column2)
        self.sw = Gtk.ScrolledWindow()
        # the width of the scrollbar
        self.sw.set_size_request(250, -1)
        self.sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.sw.add(self.tree)
        self.hbox.pack_start(self.sw, False, False, 1)
        self.tree.set_expander_column(column1)
        #
        self.list_annotations = []
        #
        if ftype == "application/pdf":
            hist_button.set_sensitive(True)
            # if self.doc.can_add_annotation():
                # annot_button.show()
            # self._doc_can_remove_annotations = self.doc.can_remove_annotation()
        else:
            annot_button.hide()
            
    def show_event(self, event):
        pass
        
    def on_quit(self, btn):
        if self._is_modified and self.model.get_document().get_modified():
            self.info_dialog("This document has been modified.\nSave it or quit this program again.")
            self._is_modified = False
            return
        Gtk.main_quit()
    
    def on_menuitem_activated(self, menuitem, _type):
        if _type == "h":
            if self.view.get_has_selection():
                ret = self.view.add_text_markup_annotation_for_selected_text()
                # _annotation = EvinceDocument.AnnotationType.TEXT_MARKUP
                # ret = self.view.begin_add_annotation(_annotation)
                if ret == False:
                    self.info_dialog("Error while adding the annotation.")
                else:
                    self._is_modified = True
                    # self.save_button.set_sensitive(True)
                    # self.list_annotations.append(_annotation)
        elif _type == "i":
            _annotation = EvinceDocument.AnnotationType.TEXT
            ret = self.view.begin_add_annotation(_annotation)
            if ret == False:
                self.info_dialog("Error while adding the annotation.")
            else:
                self._is_modified = True
                # self.save_button.set_sensitive(True)
                # self.list_annotations.append(_annotation)
    
    def on_add_annotation(self, btn):
        if self.view.get_has_selection():
            # EvinceDocument.AnnotationType.TEXT TEXT_MARKUP ATTACHMENT
            _annotation = EvinceDocument.AnnotationType.TEXT
            ret = self.view.begin_add_annotation(_annotation)
            if ret == False:
                self.info_dialog("Error while adding the annotation.")
            else:
                self._is_modified = True
                # self.save_button.set_sensitive(True)
                self.list_annotations.append(_annotation)
    
    # open file function
    def on_open_file(self, button):
        filename = self.fopen_dialog()
        if filename:
            try:
                subprocess.Popen([os.path.abspath(sys.argv[0]), filename], universal_newlines=True)
            except Exception as E:
                self.info_dialog(str(E))

    # file open dialog
    def fopen_dialog(self):
        dialog = Gtk.FileChooserDialog(title="Open File", parent=self.window, action=Gtk.FileChooserAction.OPEN, buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.set_current_folder(os.path.dirname(sys.argv[1]))
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            dialog.destroy()
            return filename
        elif response == Gtk.ResponseType.CANCEL:
            dialog.destroy()
            return False

    # rotate page left function
    def on_rotate_left(self, button):
        rotation = self.model.get_rotation()
        self.model.set_rotation(rotation - 90)
        
    # rotate page right function
    def on_rotate_right(self, button):
        rotation = self.model.get_rotation()
        self.model.set_rotation(rotation + 90)

    # double click on bookmark item
    def on_single_click(self, tree, path, data=None):
        treeiter = self.hstore.get_iter(path)
        value = self.hstore.get_value(treeiter, 1)
        self.model.set_page(int(value)-1)

    # history button
    def on_hist_button(self, button):
        hstore = self.hstore
        if not self.tree.get_visible():
            self.tree.show()
            self.sw.show()
        else:
            self.tree.hide()
            self.sw.hide()
        self.reset_zoom()
    
    # issue  
    def reset_zoom(self):
        self.zoom_label.set_text(format(self.model.get_scale(), '.2f'))

    # copy the selection to clipboard
    def on_clip_button(self, button):
        if self.view.get_has_selection():
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(self.copy_text_to_clipboard, -1)
    
    def on_win_resize(self, win):
        rwin_width = self.window.get_size().width
        rwin_height = self.window.get_size().height
        if (rwin_width) != (self.win_width) or (rwin_height) != (self.win_height):
            self.zoom_label.set_text(format(self.model.get_scale(), '.2f'))
            conf_file = os.path.dirname(os.path.abspath(sys.argv[0]))+"/conf.cfg"
            with open(conf_file, "w") as fconf:
                fconf.write(str(rwin_width)+"\n"+str(rwin_height))

    # set the view to dualpage
    def on_dual_page(self, button):
        if not self.dpage_state:
            self.model.set_dual_page_odd_pages_left(True)
            self.model.set_dual_page(True)
            self.dpage_state = True
            self.zoom_label.set_text(format(self.model.get_scale(), '.2f'))
        elif self.dpage_state:
            self.model.set_dual_page(False)
            self.dpage_state = False
            self.zoom_label.set_text(format(self.model.get_scale(), '.2f'))

    # mouse scrolling for zoom
    def fscroll_event(self, widget, event):
        if event.direction == Gdk.ScrollDirection.UP:
            self.zoom_label.set_text(format(self.model.get_scale(), '.2f'))
        elif event.direction == Gdk.ScrollDirection.DOWN:
            self.zoom_label.set_text(format(self.model.get_scale(), '.2f'))

    # left mouse click to cancel the highlighted selected words
    def view_sel_changed(self, view):
        self.view.find_cancel()

### search words function ###

    # search button
    def on_enter(self, button, popover):
        if popover.get_visible():
            popover.hide()
        self.perform_search()

    # press return on entry widget
    def on_entry_activate(self, entry, popover):
        popover.hide()
        self.perform_search()

    def perform_search(self):
        #
        stext = self.sb_entry.get_text()
        #
        evj = EvinceView.JobFind.new(document=self.doc, start_page=0, n_pages=self.doc.get_n_pages(), text=stext, case_sensitive=False)
        find_updated_handler = evj.connect('updated', self.updated_cb)
        self.view.find_started(evj)
        EvinceView.Job.scheduler_push_job(
            evj, EvinceView.JobPriority.PRIORITY_NONE)

    # popover show-hide
    def on_sb_button_click(self, button, popover):
        if popover.get_visible():
            popover.hide()
        else:
            popover.show_all()    
#########

### save document functions ###
    
    # button save
    def fsave_button(self, button):
        filename = self.fsave_dialog()
    
    def d_write_file(self, filename):
        os.unlink(filename)
        self.doc.save("file://"+filename)

    # file save dialog
    def fsave_dialog(self):
        dialog = Gtk.FileChooserDialog("Save File", self.window, Gtk.FileChooserAction.SAVE, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        dialog.set_current_folder(os.path.dirname(sys.argv[1]))
        dialog.set_do_overwrite_confirmation(True)
        self.add_filters(dialog)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            if os.path.exists(filename):
                self.d_write_file(filename)
            else:
                self.doc.save("file://"+filename)
                self.view.reload()
            dialog.destroy()
            return filename
        elif response == Gtk.ResponseType.CANCEL:
            dialog.destroy()
            return False

    def add_filters(self, dialog):
        if ftype == "application/pdf":
            filter_pdf = Gtk.FileFilter()
            filter_pdf.set_name("Pdf files")
            filter_pdf.add_mime_type("application/pdf")
            dialog.add_filter(filter_pdf)
        elif ftype == "application/postscript":
            filter_ps = Gtk.FileFilter()
            filter_ps.set_name("Ps files")
            filter_ps.add_mime_type("application/postscript")
            dialog.add_filter(filter_ps)
        elif ftype == "image/tiff":
            filter_tiff = Gtk.FileFilter()
            filter_tiff.set_name("Tiff files")
            filter_tiff.add_mime_type("image/tiff")
            dialog.add_filter(filter_tiff)
        else:
            filter_any = Gtk.FileFilter()
            filter_any.set_name("Any files")
            filter_any.add_pattern("*")
            dialog.add_filter(filter_any)
#########

    # find the TOC by links
    def index_load(self, job):
        index_model = job.get_model()
        # treestore
        iiter = index_model.get_iter_first()
        curr_page = self.doc.get_n_pages()
        while True:
            link = index_model.get_value(iiter, 1)
            numpage = int(self.doc.get_link_page(link)+1)
            # populate the treestore
            piter = self.hstore.append(None, [link.get_title(), numpage])
            self.iter_child(index_model, iiter, piter)
            
            if index_model.iter_next(iiter) != None:
                iiter = index_model.iter_next(iiter)
            else:
                break

    def iter_child(self, index_model, iiter, piter):
        if index_model.iter_has_child(iiter):
            childiter = index_model.iter_children(iiter)
            while True:
                clink = index_model.get_value(childiter, 1)
                cnumpage = int(self.doc.get_link_page(clink)+1)
                ppiter = self.hstore.append(piter, [clink.get_title(), cnumpage])
                if index_model.iter_has_child(childiter):
                    self.iter_child(index_model, childiter, ppiter)
                if index_model.iter_next(childiter) != None:
                    childiter = index_model.iter_next(childiter)
                else:
                    break

#############
    def fsearch_button(self, button, stext):
        evj = EvinceView.JobFind.new(document=self.doc, start_page=0, n_pages=self.doc.get_n_pages(), text=stext, case_sensitive=False)
        find_updated_handler = evj.connect('updated', self.updated_cb)
        self.view.find_started(evj)
        EvinceView.Job.scheduler_push_job(
            evj, EvinceView.JobPriority.PRIORITY_NONE)
    
    def updated_cb(self, a, b):
        self.view.find_set_highlight_search(True)

    # highligth the next result of searching
    def ffnext_button(self, button):
        self.view.find_next()

    # highligth the previous result of searching
    def ffprev_button(self, button):
        self.view.find_previous()

##########

    # next page button
    def next_button(self, button):
        self.view.next_page()

    # previous page button
    def prev_button(self, button):
        self.view.previous_page()

    #
    def fbt_zoomp(self, button):
        self.model.props.sizing_mode = EvinceView.SizingMode.FREE
        self.view.zoom_in()
        zoom = self.model.get_scale()
        self.zoom_label.set_text(format(zoom, '.2f'))

    #
    def fbt_zoomm(self, button):
        self.model.props.sizing_mode = EvinceView.SizingMode.FREE
        self.view.zoom_out()
        zoom = self.model.get_scale()
        self.zoom_label.set_text(format(zoom, '.2f'))
    
    # get the info of the document
    def finfo_button(self, button, info_list):
        if ftype == "application/pdf":
            ddate = ""
            try:
                ddate = datetime.datetime.fromtimestamp(int(info_list[1])).strftime(' %m-%d-%Y %H:%M:%S ')
            except:
                ddate = ""
            self.info_dialog("Author: "+info_list[0]+"\n"+"Date: "+str(ddate)+"\n"+"Creator: "+str(info_list[2])+"\n"+"Type: "+info_list[3]+"\n"+"Pages: "+str(info_list[4])+"\n"+"Program: "+info_list[5])
    
    # document info dialog
    def info_dialog(self, stext):
        
        dialog = Gtk.MessageDialog(self.window, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                          Gtk.MessageType.INFO, Gtk.ButtonsType.OK, stext)
    
        response = dialog.run()

        dialog.set_default_size(400, 300)
        
        if response == Gtk.ResponseType.OK:
            dialog.destroy()
        else:
            dialog.destroy()
        
    def night_mode(self, btn):
        self.model.set_inverted_colors(not self.model.get_inverted_colors())
        
    # go to the page n
    def curr_entry_activate(self, entry):
        get_page = entry.get_text()
        self.model.set_page(int(get_page)-1)

    def model_page_changed(self, model, oobject, p0):
        self.curr_entry.set_text(str(model.get_page()+1))
    
    def button_clicked(self, button):
        global settings
        if not settings:
            self.evprint.run(self.window)
            settings = self.evprint.get_print_settings()
        else:
            self.evprint = EvinceView.PrintOperation.new(self.doc)
            self.evprint.run(self.window)
        
    # handling keyboard events
    def keypress(self,widget,event):
        keyname = Gdk.keyval_name(event.keyval)
        # # reload the document
        # if keyname=='r':
            # self.model.get_document().load('file://'+docfile) # <- ADD THIS LINE
            # self.view.reload()
        # el
        if keyname == 'Return':
            if self.fullscreen == False:
                self.fullscreen=True
                self.window.fullscreen()
            else:
                self.fullscreen=False
                self.window.unfullscreen()
        # # quit the program
        # elif keyname=='q':
            # Gtk.main_quit()
        # # select all the text
        # elif keyname=='a':
            # self.view.select_all()
        # escape
        elif keyname == 'escape':
            self.view.cancel_add_annotation()

### CLIPBOARD ###

class Clipboard:
    
    def __init__(self):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY)
        clipboard.set_text("", -1)
        clipboard.connect('owner-change', self.clipb)

    def clipb(self, clipboard, EventOwnerChange):
        clipboard.request_text(self.callback, None)

    def callback(self, clipboard, text, data):
        if text:
            self.ccontent(text)

    def ccontent(self, ctdata):
        if ctdata:
            evinceViewer.copy_text_to_clipboard = ctdata

Clipboard()
#####################

if __name__ == "__main__":
    evinceViewer = EvinceViewer()
    zoom = evinceViewer.model.get_scale()
    evinceViewer.zoom_label.set_text(format(zoom, '.2f'))
    Gtk.main()
