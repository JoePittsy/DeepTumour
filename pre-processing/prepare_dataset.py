import numpy as np
import pylidc as pl
import os
import warnings
from statistics import median_high
from utils import segment_lung
from pylidc.utils import consensus
import multiprocessing
import psutil

warnings.filterwarnings("ignore")

LIDC_FOLDER = "/media/joe/16657094/LIDC-IDRI"


def calculate_malignancy(nodule):
    list_of_malignancy = [ann.malignancy for ann in nodule]
    malignancy = median_high(list_of_malignancy)
    cancer = True if malignancy > 3 else False if malignancy < 3 else "Ambiguous"
    return malignancy, cancer


def munge_lung(lung: str):
    scan = pl.query(pl.Scan).filter(pl.Scan.patient_id == lung).first()
    print()
    nodules_annotation = scan.cluster_annotations()
    vol = scan.to_volume()
    print(f"ID: {lung} Annotated Nodules: {len(nodules_annotation)}")

    if len(nodules_annotation) > 0:
        for index, nodule in enumerate(nodules_annotation):
            print(nodule)
            mask, cbbox, masks = consensus(nodule, 0.5, 512)
            lung_np_array = vol[cbbox]
            malignancy, cancer_label = calculate_malignancy(nodule)

            for lung_slice in range(mask.shape[2]):
                if np.sum(mask[:, :, lung_slice]) <= 8:
                    continue
                l = lung_np_array[:, :, lung_slice].astype('float64')
                lung_segmented_np_array = segment_lung(l)
                lung_segmented_np_array[lung_segmented_np_array == -0] = 0

                lung_file = np.array([
                    l,
                    lung_segmented_np_array,
                    nodule[index].bbox(),
                    malignancy,
                    cancer_label
                ])

                if not os.path.exists(f'./data/Image/{lung}/'):
                    os.makedirs(f'./data/Image/{lung}/')

                np.save(f"./data/Image/{lung}/lung_slice{lung_slice}", lung_file, allow_pickle=True)


def limit_cpu():
    """is called at every process start"""
    p = psutil.Process(os.getpid())
    # set to lowest priority, this is windows only, on Unix use ps.nice(19)
    p.nice(19)


if __name__ == '__main__':
    LIDC_IDRI_list = [f for f in os.listdir(LIDC_FOLDER) if not f.startswith('.')]
    LIDC_IDRI_list.sort()
    print("Number of cpu : ", multiprocessing.cpu_count())

    pool = multiprocessing.Pool(None, limit_cpu)
    results = pool.map(munge_lung, LIDC_IDRI_list)
