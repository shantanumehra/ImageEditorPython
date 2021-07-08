import tkinter as tk
from tkinter import ttk
from tkinter import Frame, Canvas, CENTER, ROUND
from PIL import Image, ImageTk
import cv2
from tkinter import Toplevel, Button, RIGHT
import numpy as np
from tkinter import LEFT
from tkinter import filedialog
from tkinter import Label, Scale, HORIZONTAL


class Main(tk.Tk):

    def __init__(self):
        tk.Tk.__init__(self)

        self.filename = ""
        self.OriginalImage = None
        self.EditedImage = None
        self.is_image_selected = False
        self.is_draw_state = False
        self.is_crop_state = False

        self.filterFrame = None
        self.adjustFrame = None

        self.title("Image Editor")

        self.editbar = EditBar(master=self)
        separator1 = ttk.Separator(master=self, orient=tk.HORIZONTAL)
        self.imagePreview = ImageViewer(master=self)

        self.editbar.pack(pady=10)
        separator1.pack(fill=tk.X, padx=20, pady=5)
        self.imagePreview.pack(fill=tk.BOTH, padx=20, pady=10, expand=1)

###############################################################################################################

class ImageViewer(Frame):

    def __init__(self, master=None):
        Frame.__init__(self, master=master, bg="black", width=600, height=400)

        self.shown_image = None
        self.x = 0
        self.y = 0
        self.crop_start_x = 0
        self.crop_start_y = 0
        self.crop_end_x = 0
        self.crop_end_y = 0
        self.draw_ids = list()
        self.rectangle_id = 0
        self.ratio = 0

        self.canvas = Canvas(self, bg="black", width=600, height=400)
        self.canvas.place(relx=0.5, rely=0.5, anchor=CENTER)

    def show_image(self, img=None):
        self.clear_canvas()

        if img is None:
            image = self.master.EditedImage.copy()
        else:
            image = img

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width, channels = image.shape
        ratio = height / width

        new_width = width
        new_height = height

        if height > self.winfo_height() or width > self.winfo_width():
            if ratio < 1:
                new_width = self.winfo_width()
                new_height = int(new_width * ratio)
            else:
                new_height = self.winfo_height()
                new_width = int(new_height * (width / height))

        self.shown_image = cv2.resize(image, (new_width, new_height))
        self.shown_image = ImageTk.PhotoImage(Image.fromarray(self.shown_image))

        self.ratio = height / new_height

        self.canvas.config(width=new_width, height=new_height)
        self.canvas.create_image(new_width / 2, new_height / 2, anchor=CENTER, image=self.shown_image)

    def activate_draw(self):
        self.canvas.bind("<ButtonPress>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)

        self.master.is_draw_state = True

    def activate_crop(self):
        self.canvas.bind("<ButtonPress>", self.start_crop)
        self.canvas.bind("<B1-Motion>", self.crop)
        self.canvas.bind("<ButtonRelease>", self.end_crop)

        self.master.is_crop_state = True

    def deactivate_draw(self):
        self.canvas.unbind("<ButtonPress>")
        self.canvas.unbind("<B1-Motion>")

        self.master.is_draw_state = False

    def deactivate_crop(self):
        self.canvas.unbind("<ButtonPress>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease>")

        self.master.is_crop_state = False

    def start_draw(self, event):
        self.x = event.x
        self.y = event.y

    def draw(self, event):
        self.draw_ids.append(self.canvas.create_line(self.x, self.y, event.x, event.y, width=2,
                                                     fill="red", capstyle=ROUND, smooth=True))

        cv2.line(self.master.EditedImage, (int(self.x * self.ratio), int(self.y * self.ratio)),
                 (int(event.x * self.ratio), int(event.y * self.ratio)),
                 (0, 0, 255), thickness=int(self.ratio * 2),
                 lineType=8)

        self.x = event.x
        self.y = event.y

    def start_crop(self, event):
        self.crop_start_x = event.x
        self.crop_start_y = event.y

    def crop(self, event):
        if self.rectangle_id:
            self.canvas.delete(self.rectangle_id)

        self.crop_end_x = event.x
        self.crop_end_y = event.y

        self.rectangle_id = self.canvas.create_rectangle(self.crop_start_x, self.crop_start_y,
                                                         self.crop_end_x, self.crop_end_y, width=1)

    def end_crop(self, event):
        if self.crop_start_x <= self.crop_end_x and self.crop_start_y <= self.crop_end_y:
            start_x = int(self.crop_start_x * self.ratio)
            start_y = int(self.crop_start_y * self.ratio)
            end_x = int(self.crop_end_x * self.ratio)
            end_y = int(self.crop_end_y * self.ratio)
        elif self.crop_start_x > self.crop_end_x and self.crop_start_y <= self.crop_end_y:
            start_x = int(self.crop_end_x * self.ratio)
            start_y = int(self.crop_start_y * self.ratio)
            end_x = int(self.crop_start_x * self.ratio)
            end_y = int(self.crop_end_y * self.ratio)
        elif self.crop_start_x <= self.crop_end_x and self.crop_start_y > self.crop_end_y:
            start_x = int(self.crop_start_x * self.ratio)
            start_y = int(self.crop_end_y * self.ratio)
            end_x = int(self.crop_end_x * self.ratio)
            end_y = int(self.crop_start_y * self.ratio)
        else:
            start_x = int(self.crop_end_x * self.ratio)
            start_y = int(self.crop_end_y * self.ratio)
            end_x = int(self.crop_start_x * self.ratio)
            end_y = int(self.crop_start_y * self.ratio)

        x = slice(start_x, end_x, 1)
        y = slice(start_y, end_y, 1)

        self.master.EditedImage = self.master.EditedImage[y, x]

        self.show_image()

    def clear_canvas(self):
        self.canvas.delete("all")

    def clear_draw(self):
        self.canvas.delete(self.draw_ids)


#############################################################################################################




class FilterFrame(Toplevel):

    def __init__(self, master=None):
        Toplevel.__init__(self, master=master)

        self.OriginalImage = self.master.EditedImage
        self.filtered_image = None

        self.negative_button = Button(master=self, text="Negative",width=12)
        self.black_white_button = Button(master=self, text="Black White",width=12)
        self.sepia_button = Button(master=self, text="Sepia",width=12)
        self.emboss_button = Button(master=self, text="Emboss",width=12)
        # self.gaussian_blur_button = Button(master=self, text="Gaussian Blur",width=12)
        self.median_blur_button = Button(master=self, text="Median Blur",width=12)
        self.cancel_button = Button(master=self, text="Cancel")
        self.apply_button = Button(master=self, text="Apply")

        self.negative_button.bind("<ButtonRelease>", self.negative_button_released)
        self.black_white_button.bind("<ButtonRelease>", self.black_white_released)
        self.sepia_button.bind("<ButtonRelease>", self.sepia_button_released)
        self.emboss_button.bind("<ButtonRelease>", self.emboss_button_released)
        # self.gaussian_blur_button.bind("<ButtonRelease>", self.gaussian_blur_button_released)
        self.median_blur_button.bind("<ButtonRelease>", self.median_blur_button_released)
        self.apply_button.bind("<ButtonRelease>", self.apply_button_released)
        self.cancel_button.bind("<ButtonRelease>", self.cancel_button_released)

        self.negative_button.pack()
        self.black_white_button.pack()
        self.sepia_button.pack()
        self.emboss_button.pack()
        # self.gaussian_blur_button.pack()
        self.median_blur_button.pack()
        self.cancel_button.pack(side=RIGHT)
        self.apply_button.pack(side=LEFT)

    def negative_button_released(self, event):
        self.negative()
        self.show_image()

    def black_white_released(self, event):
        self.black_white()
        self.show_image()

    def sepia_button_released(self, event):
        self.sepia()
        self.show_image()

    def emboss_button_released(self, event):
        self.emboss()
        self.show_image()

    # def gaussian_blur_button_released(self, event):
    #     self.gaussian_blur()
    #     self.show_image()

    def median_blur_button_released(self, event):
        self.median_blur()
        self.show_image()

    def apply_button_released(self, event):
        self.master.EditedImage = self.filtered_image
        self.show_image()
        self.close()

    def cancel_button_released(self, event):
        self.master.imagePreview.show_image()
        self.close()

    def show_image(self):
        self.master.imagePreview.show_image(img=self.filtered_image)

    def negative(self):
        self.filtered_image = cv2.bitwise_not(self.OriginalImage)

    def black_white(self):
        self.filtered_image = cv2.cvtColor(self.OriginalImage, cv2.COLOR_BGR2GRAY)
        self.filtered_image = cv2.cvtColor(self.filtered_image, cv2.COLOR_GRAY2BGR)

    def sepia(self):
        kernel = np.array([[0.272, 0.534, 0.131],
                           [0.349, 0.686, 0.168],
                           [0.393, 0.769, 0.189]])

        self.filtered_image = cv2.filter2D(self.OriginalImage, -1, kernel)

    def emboss(self):
        kernel = np.array([[0, -1, -1],
                           [1, 0, -1],
                           [1, 1, 0]])

        self.filtered_image = cv2.filter2D(self.OriginalImage, -1, kernel)

    # def gaussian_blur(self):
    #     self.filtered_image = cv2.GaussianBlur(self.OriginalImage, (41, 41), 0)

    def median_blur(self):
        self.filtered_image = cv2.medianBlur(self.OriginalImage, 41)

    def close(self):
        # self.destroy()
        SystemExit



###################################################################################################################



class EditBar(Frame):

    def __init__(self, master=None):
        Frame.__init__(self, master=master)

        self.insert_button = Button(self, text="Insert",width=9)
        self.save_as_button = Button(self, text="Save As",width=9)
        self.draw_button = Button(self, text="Draw",width=9)
        self.crop_button = Button(self, text="Crop",width=9)
        self.filter_button = Button(self, text="Filter",width=9)
        self.adjust_button = Button(self, text="Adjust",width=9)
        self.clear_button = Button(self, text="Clear",width=9)
        self.close_button = Button(self, text="Close",width=9)

        self.insert_button.bind("<ButtonRelease>", self.insert_button_released)
        self.save_as_button.bind("<ButtonRelease>", self.save_as_button_released)
        self.draw_button.bind("<ButtonRelease>", self.draw_button_released)
        self.crop_button.bind("<ButtonRelease>", self.crop_button_released)
        self.filter_button.bind("<ButtonRelease>", self.filter_button_released)
        self.adjust_button.bind("<ButtonRelease>", self.adjust_button_released)
        self.clear_button.bind("<ButtonRelease>", self.clear_button_released)
        self.close_button.bind("<ButtonRelease>", self.close_button_released)

        self.insert_button.pack(side=LEFT)
        self.save_as_button.pack(side=LEFT)
        self.draw_button.pack(side=LEFT)
        self.crop_button.pack(side=LEFT)
        self.filter_button.pack(side=LEFT)
        self.adjust_button.pack(side=LEFT)
        self.clear_button.pack(side=LEFT)
        self.close_button.pack()

    def insert_button_released(self, event):
        if self.winfo_containing(event.x_root, event.y_root) == self.insert_button:
            if self.master.is_draw_state:
                self.master.imagePreview.deactivate_draw()
            if self.master.is_crop_state:
                self.master.imagePreview.deactivate_crop()

            filename = filedialog.askopenfilename()
            image = cv2.imread(filename)

            if image is not None:
                self.master.filename = filename
                self.master.OriginalImage = image.copy()
                self.master.EditedImage = image.copy()
                self.master.imagePreview.show_image()
                self.master.is_image_selected = True

    def close_button_released(self,event):
            self.destroy()

    def save_as_button_released(self, event):
        if self.winfo_containing(event.x_root, event.y_root) == self.save_as_button:
            if self.master.is_image_selected:
                if self.master.is_draw_state:
                    self.master.imagePreview.deactivate_draw()
                if self.master.is_crop_state:
                    self.master.imagePreview.deactivate_crop()

                original_file_type = self.master.filename.split('.')[-1]
                filename = filedialog.asksaveasfilename()
                filename = filename + "." + original_file_type

                save_image = self.master.EditedImage
                cv2.imwrite(filename, save_image)

                self.master.filename = filename

    def draw_button_released(self, event):
        if self.winfo_containing(event.x_root, event.y_root) == self.draw_button:
            if self.master.is_image_selected:
                if self.master.is_crop_state:
                    self.master.imagePreview.deactivate_crop()
                if self.master.is_draw_state:
                    self.master.imagePreview.deactivate_draw()
                else:
                    self.master.imagePreview.activate_draw()

    def crop_button_released(self, event):
        if self.winfo_containing(event.x_root, event.y_root) == self.crop_button:
            if self.master.is_image_selected:
                if self.master.is_draw_state:
                    self.master.imagePreview.deactivate_draw()
                if self.master.is_crop_state:
                    self.master.imagePreview.deactivate_crop()
                else:
                    self.master.imagePreview.activate_crop()

    def filter_button_released(self, event):
        if self.winfo_containing(event.x_root, event.y_root) == self.filter_button:
            if self.master.is_image_selected:
                if self.master.is_draw_state:
                    self.master.imagePreview.deactivate_draw()
                if self.master.is_crop_state:
                    self.master.imagePreview.deactivate_crop()

                self.master.filterFrame = FilterFrame(master=self.master)
                self.master.filterFrame.grab_set()

    def adjust_button_released(self, event):
        if self.winfo_containing(event.x_root, event.y_root) == self.adjust_button:
            if self.master.is_image_selected:
                if self.master.is_draw_state:
                    self.master.imagePreview.deactivate_draw()
                if self.master.is_crop_state:
                    self.master.imagePreview.deactivate_crop()

                self.master.adjustFrame = AdjustFrame(master=self.master)
                self.master.adjustFrame.grab_set()

    def clear_button_released(self, event):
        if self.winfo_containing(event.x_root, event.y_root) == self.clear_button:
            if self.master.is_image_selected:
                if self.master.is_draw_state:
                    self.master.imagePreview.deactivate_draw()
                if self.master.is_crop_state:
                    self.master.imagePreview.deactivate_crop()

                self.master.EditedImage = self.master.OriginalImage.copy()
                self.master.imagePreview.show_image()




#############################################################################################





class AdjustFrame(Toplevel):

    def __init__(self, master=None):
        Toplevel.__init__(self, master=master)

        self.brightness_value = 0
        self.previous_brightness_value = 0

        self.OriginalImage = self.master.EditedImage
        self.processing_image = self.master.EditedImage

        self.brightness_label = Label(self, text="Brightness")
        self.brightness_scale = Scale(self, from_=0, to_=10, length=250, resolution=0.1,
                                      orient=HORIZONTAL)
        self.r_label = Label(self, text="Red")
        self.r_scale = Scale(self, from_=-100, to_=100, length=250, resolution=1,
                             orient=HORIZONTAL)
        self.g_label = Label(self, text="Green")
        self.g_scale = Scale(self, from_=-100, to_=100, length=250, resolution=1,
                             orient=HORIZONTAL)
        self.b_label = Label(self, text="Blue")
        self.b_scale = Scale(self, from_=-100, to_=100, length=250, resolution=1,
                             orient=HORIZONTAL)
        self.apply_button = Button(self, text="Apply",width=5,pady=5,padx=20)
        self.preview_button = Button(self, text="Preview",width=5,pady=5,padx=20)
        self.cancel_button = Button(self, text="Cancel",width=5,pady=5,padx=20)

        self.brightness_scale.set(0)

        self.apply_button.bind("<ButtonRelease>", self.apply_button_released)
        self.preview_button.bind("<ButtonRelease>", self.preview_button_release)
        self.cancel_button.bind("<ButtonRelease>", self.cancel_button_released)

        self.brightness_label.pack()
        self.brightness_scale.pack()
        self.r_label.pack()
        self.r_scale.pack()
        self.g_label.pack()
        self.g_scale.pack()
        self.b_label.pack()
        self.b_scale.pack()
        self.cancel_button.pack(side=RIGHT)
        self.apply_button.pack(side=LEFT)
        self.preview_button.pack()
        

    def apply_button_released(self, event):
        self.master.EditedImage = self.processing_image
        self.close()

    def preview_button_release(self, event):
        self.processing_image = cv2.convertScaleAbs(self.OriginalImage, alpha=self.brightness_scale.get())
        b, g, r = cv2.split(self.processing_image)

        for b_value in b:
            cv2.add(b_value, self.b_scale.get(), b_value)
        for g_value in g:
            cv2.add(g_value, self.g_scale.get(), g_value)
        for r_value in r:
            cv2.add(r_value, self.r_scale.get(), r_value)

        self.processing_image = cv2.merge((b, g, r))
        self.show_image(self.processing_image)

    def cancel_button_released(self, event):
        self.close()

    def show_image(self, img=None):
        self.master.imagePreview.show_image(img=img)

    def close(self):
        self.show_image()
        self.destroy()



window = Main()
window.mainloop()
