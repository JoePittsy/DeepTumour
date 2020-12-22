import numpy as np
import pylidc as pl
import os
from statistics import median_high
from utils import segment_lung
from pylidc.utils import consensus
import multiprocessing


LIDC_FOLDER = "/home/joe/PycharmProjects/dissertation/ct_scans/LIDC-IDRI"

def calculate_malignancy(nodule):
    list_of_malignancy = [ann.malignancy for ann in nodule]
    malignancy = median_high(list_of_malignancy)
    cancer = True if malignancy > 3 else False if malignancy < 3 else "Ambiguous"
    return malignancy, cancer


def munge_lung(lung):
    scan = pl.query(pl.Scan).filter(pl.Scan.patient_id == lung).first()
    print()
    nodules_annotation = scan.cluster_annotations()
    vol = scan.to_volume()
    print(f"ID: {lung} Annotated Nodules: {len(nodules_annotation)}")

    if len(nodules_annotation) > 0:
        for index, nodule in enumerate(nodules_annotation):
            mask, cbbox, masks = consensus(nodule, 0.5, 512)
            lung_np_array = vol[cbbox]
            malignancy, cancer_label = calculate_malignancy(nodule)
            print(malignancy, cancer_label)

            for lung_slice in range(mask.shape[2]):
                if np.sum(mask[:, :, lung_slice]) <= 8:
                    continue
                lung_segmented_np_array = segment_lung(lung_np_array[:, :, lung_slice])
                lung_segmented_np_array[lung_segmented_np_array == -0] = 0

                if not os.path.exists(f'./data/Image/{lung}/'):
                    os.makedirs(f'./data/Image/{lung}/')

                np.save(f"./data/Image/{lung}/lung_slice{lung_slice}", lung_segmented_np_array)


if __name__ == '__main__':
    LIDC_IDRI_list = [f for f in os.listdir(LIDC_FOLDER) if not f.startswith('.')]
    LIDC_IDRI_list.sort()
    print("Number of cpu : ", multiprocessing.cpu_count())

    procs = []

    # instantiating process with arguments
    for lung in LIDC_IDRI_list:
        # print(name)
        proc = multiprocessing.Process(target=munge_lung, args=(lung,))
        procs.append(proc)
        proc.start()

    # complete the processes
    for proc in procs:
        proc.join()
