from medpy.filter.smoothing import anisotropic_diffusion
from scipy.ndimage import median_filter
from skimage import measure, morphology
from sklearn.cluster import KMeans
import numpy as np


def mean_filter(img: np.ndarray):
    mean = np.mean(img)
    std_dev = np.std(img)

    img -= mean
    img /= std_dev

    return img


def middle_filter(img):
    middle = img[100:400, 100:400]
    middle_mean = np.mean(middle)
    lung_max = np.max(img)
    lung_min = np.min(img)

    # Set the max and min values to the middle mean
    img[img == lung_max] = middle_mean
    img[img == lung_min] = middle_mean

    return img


def k_means_filter(img):
    middle = img[100:400, 100:400]

    k_means = KMeans(n_clusters=2)
    k_means.fit(np.reshape(middle, [np.prod(middle.shape), 1]))

    centers = sorted(k_means.cluster_centers_.flatten())
    centers_mean = np.mean(centers)

    threshold_img = np.where(img < centers_mean, 1.0, 0.0)

    eroded = morphology.erosion(threshold_img, np.ones([4, 4]))
    dilation = morphology.dilation(eroded, np.ones([10, 10]))

    labels = measure.label(dilation)
    regions = measure.regionprops(labels)

    good_labels = []
    for prop in regions:
        bound_box = prop.bbox
        if bound_box[2] - bound_box[0] < 475 and bound_box[3] - bound_box[1] < 475 and bound_box[0] > 40 and \
                bound_box[2] < 472:
            good_labels.append(prop.label)
    mask = np.ndarray([512, 512], dtype=np.int8)
    mask[:] = 0

    for N in good_labels:
        mask = mask + np.where(labels == N, 1, 0)
    mask = morphology.dilation(mask, np.ones([10, 10]))  # one last dilation
    return mask * img


def segment_lung(lung):
    lung = mean_filter(lung)
    lung = middle_filter(lung)
    lung = median_filter(lung, size=3)
    lung = anisotropic_diffusion(lung)
    lung = k_means_filter(lung)

    return lung


def count_params(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


