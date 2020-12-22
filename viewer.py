from matplotlib import pyplot as plt
import numpy as np


if __name__ == "__main__":
    img_array = np.load('./data/Image/LIDC-IDRI-0001/0001_NI000_slice000.npy')
    # mask = np.load('./data/Mask/LIDC-IDRI-0005/0005_MA000_slice000.npy')

    plt.gca().set_axis_off()
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0,
                        hspace=0, wspace=0)
    plt.margins(0, 0)
    plt.gca().xaxis.set_major_locator(plt.NullLocator())
    plt.gca().yaxis.set_major_locator(plt.NullLocator())
    plt.imshow(img_array, cmap='cividis')
    plt.title("LIDC-IDRI-0001 K-Means Threshold")
    # plt.imshow(mask, cmap='gray')

    plt.show()