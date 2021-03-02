import random
from statistics import median_high

import pylidc as pl

from utils import *

LIDC_FOLDER = "/media/joe/16657094/LIDC-IDRI"


def calculate_malignancy(nodule):
    list_of_malignancy = [ann.malignancy for ann in nodule]
    malignancy = median_high(list_of_malignancy)
    return malignancy


def create_annotations():
    all_scans = pl.query(pl.Scan)
    scan: pl.Scan
    count = 0
    for scan in all_scans:
        count += 1
        print(f"{count}/1000, {(count/1000)*100}%")
        patient_id = scan.patient_id
        if os.path.isdir(f"../pre-processing/data/Image/{patient_id}"):
            nodules = scan.cluster_annotations()
            for nodule in nodules:
                try:
                    mask_list = nodule_to_masks(nodule)
                    for slice, mask in mask_list.items():
                        if os.path.isfile(f"../pre-processing/data/Image/{patient_id}/{patient_id}_slice_{slice}.png"):
                            li = [(yx[1], yx[0]) for yx in mask['coordinates'][0]]
                            x, y = zip(*li)
                            out_string = ""
                            for i in range(len(x)):
                                out_string += f",{x[i]},{y[i]}"
                            label = calculate_malignancy(nodule)
                            set = "train" if random.random() <= 0.7 else "test"
                            with open(f"./data/{set}.txt", "a") as f:
                                f.write(f'\n/content/drive/My Drive/DeepTumour/pre-processing/data/Image/{patient_id}/{patient_id}_slice_{slice}.png{out_string},{label}')
                except:
                    pass

if __name__ == "__main__":
    create_annotations()
