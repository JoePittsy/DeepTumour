import os
import sys
from collections import defaultdict
from math import floor, ceil, sqrt

import numpy as np
from medpy.filter.smoothing import anisotropic_diffusion
from rasterio import Affine, features
from scipy.ndimage import median_filter
from shapely.geometry import Polygon
from shapely.geometry import mapping, shape
from shapely.ops import cascaded_union
from skimage import measure, morphology
from sklearn.cluster import KMeans


def block_print():
    sys.stdout = open(os.devnull, 'w')


# Restore
def enable_print():
    sys.stdout = sys.__stdout__


def nodule_to_masks(nodule):
    masks = {}

    contours_dict = defaultdict(list)
    for ann in nodule:
        contours = sorted(ann.contours, key=lambda c: c.image_z_position)
        fnames = ann.scan.sorted_dicom_file_names.split(',')
        index_of_contour = [fnames.index(c.dicom_file_name) for c in contours]

        for i, s in enumerate(index_of_contour):
            contours_dict[s].append(contours[i])

    shapes_per_nodule = {i: [Polygon(c.to_matrix()) for c in contours_dict[i]] for i in contours_dict.keys()}

    for slice, shapes in shapes_per_nodule.items():
        try:
            if len(shapes) == 1:
                s = mapping(shapes[0])
                s['coordinates'] = [[xy[0:2] for xy in s['coordinates'][0]]]
                masks[slice] = s
                continue
            max_shape = cascaded_union([shape(s) for s in shapes])
            minx, miny, maxx, maxy = max_shape.bounds
            dx = dy = 1.0  # grid resolution; this can be adjusted
            lenx = dx * (ceil(maxx / dx) - floor(minx / dx))
            leny = dy * (ceil(maxy / dy) - floor(miny / dy))
            assert lenx % dx == 0.0
            assert leny % dy == 0.0
            nx = int(lenx / dx)
            ny = int(leny / dy)
            gt = Affine(
                dx, 0.0, dx * floor(minx / dx),
                0.0, -dy, dy * ceil(maxy / dy))
            pa = np.zeros((ny, nx), 'd')
            for s in shapes:
                r = features.rasterize([s], (ny, nx), transform=gt)
                pa[r > 0] += 1
            pa /= len(shapes)  # normalise values
            from scipy.signal import fftconvolve

            def gaussian_blur(in_array, gt, size):
                """Gaussian blur, returns tuple `(ar, gt2)` that have been expanded by `size`"""
                # expand in_array to fit edge of kernel; constant value is zero
                padded_array = np.pad(in_array, size, 'constant')
                # build kernel
                x, y = np.mgrid[-size:size + 1, -size:size + 1]
                g = np.exp(-(x ** 2 / float(size) + y ** 2 / float(size)))
                g = (g / g.sum()).astype(in_array.dtype)
                # do the Gaussian blur
                ar = fftconvolve(padded_array, g, mode='full')
                # convolved increased size of array ('full' option); update geotransform
                gt2 = Affine(
                    gt.a, gt.b, gt.xoff - (2 * size * gt.a),
                    gt.d, gt.e, gt.yoff - (2 * size * gt.e))
                return ar, gt2

            spa, sgt = gaussian_blur(pa, gt, 100)
            thresh = 0.4  # median
            pm = np.zeros(spa.shape, 'B')
            pm[spa > thresh] = 1
            poly_shapes = []
            for sh, val in features.shapes(pm, transform=sgt):
                if val == 1:
                    poly_shapes.append(shape(sh))
            if not any(poly_shapes):
                # Well no shapes found, just return the first radioligsts annotation
                s = mapping(shapes[0])
                s['coordinates'] = [[xy[0:2] for xy in s['coordinates'][0]]]
                masks[slice] = s
                continue
                # raise ValueError("could not find any shapes")
            avg_poly = cascaded_union(poly_shapes)
            # Simplify the polygon
            simp_poly = avg_poly.simplify(sqrt(dx ** 2 + dy ** 2))
            simp_shape = mapping(simp_poly)
            masks[slice] = simp_shape
        except:
            s = mapping(shapes[0])
            s['coordinates'] = [[xy[0:2] for xy in s['coordinates'][0]]]
            masks[slice] = s
    return masks


def bbox_to_frcnn(bbox):
    x = bbox[1].start
    y = bbox[0].start
    height = bbox[0].stop - bbox[0].start
    width = bbox[1].stop - bbox[1].start

    return x, y, width, height


def avg_bboxs(bboxs):
    x, y, w, h = 0, 0, 0, 0

    for bbox in bboxs:
        nx, ny, nw, nh = bbox_to_frcnn(bbox)
        # print(f"X: {nx} Y: {ny} W: {nw} H: {nh}")
        x += nx
        y += ny
        w += nw
        h += nw
    x /= len(bboxs)
    y /= len(bboxs)
    w /= len(bboxs)
    h /= len(bboxs)

    return x, y, w, h


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
