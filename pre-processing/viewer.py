#!/usr/bin/env python3
#
# from matplotlib import pyplot as plt
# import numpy as np
# import sys
#
#
# if __name__ == "__main__":
#     file_path = sys.argv[1]
#     print(file_path[-3:])
#     if file_path[-3:] == "npy":
#
#         img_data = np.load(file_path, allow_pickle=True)
#         img_array = img_data[0]
#         # mask = np.load('./data/Mask/LIDC-IDRI-0005/0005_MA000_slice000.npy')
#
#         plt.gca().set_axis_off()
#         plt.subplots_adjust(top=1, bottom=0, right=1, left=0,
#                             hspace=0, wspace=0)
#         plt.margins(0, 0)
#         plt.gca().xaxis.set_major_locator(plt.NullLocator())
#         plt.gca().yaxis.set_major_locator(plt.NullLocator())
#         plt.imshow(img_array, cmap='cividis')
#         plt.show()
import sys
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

matplotlib.use('TkAgg')
global image, patch_status
image = "BASE"
patch_status = False


def swap_image(event):
    global image

    if image == "BASE":
        ax.imshow(img_data[1], cmap="cividis")

        image = "KMEANS"
    else:
        ax.imshow(img_data[0], cmap="cividis")
        image = "BASE"
    if patch_status:
        ax.add_patch(patch)
    plt.show()


def toggle_patch(event):
    global patch_status
    patch_status = False if patch_status else True
    if not patch_status:
        ax.patches = []
    else:
        ax.add_patch(patch)
    plt.show()


def bbox_to_patch(bbox):
    tl = (bbox[1].start, bbox[0].start)
    height = bbox[0].stop - bbox[0].start
    width = bbox[1].stop - bbox[1].start
    patch = matplotlib.patches.Rectangle(tl, width, height, fill=False, color=(0, 1, 0, 1))

    return patch


if __name__ == "__main__":
    file_path = sys.argv[1]
    if file_path[-3:] == "npy":
        img_data = np.load(file_path, allow_pickle=True)
        ax = plt.subplot(111)
        plt.gca().set_axis_off()
        patch = bbox_to_patch(img_data[2])

        axcut = plt.axes([0.22, 0.02, 0.15, 0.075])
        bxcut = plt.axes([0.65, 0.02, 0.15, 0.075])

        bcut = Button(axcut, 'Toggle View')
        tcut = Button(bxcut, 'Toggle BBox')

        bcut.on_clicked(swap_image)
        tcut.on_clicked(toggle_patch)
        ax.set_title(f"Tumour Malignancy = {img_data[3]} {'Cancerous' if img_data[4] else 'Not Cancerous'}")

        ax.imshow(img_data[0], cmap="cividis")
        plt.show()
