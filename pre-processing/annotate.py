import random
from statistics import median_high

import pylidc as pl
from collections import defaultdict

from utils import *

LIDC_FOLDER = "/media/joe/16657094/LIDC-IDRI"


def calculate_malignancy(nodule):
    list_of_malignancy = [ann.diameter for ann in nodule]
    malignancy = np.mean(list_of_malignancy)
    if malignancy >= 50:
        malignancy = "5"
    elif malignancy >= 40:
        malignancy = "4"
    elif malignancy >= 30:
        malignancy = "3"
    elif malignancy >= 20:
        malignancy = "2"
    else:
        malignancy = "1"

    return malignancy


def create_annotations():
    all_scans = pl.query(pl.Scan)
    scan: pl.Scan
    count = 0

    slices = defaultdict(list)

    for scan in all_scans:
        count += 1
        print(f"{count}/1000, {(count / 1000) * 100}%")
        patient_id = scan.patient_id
        if os.path.isdir(f"../pre-processing/data/Image/{patient_id}"):
            nodules = scan.cluster_annotations()
            for nodule in nodules:
                label = calculate_malignancy(nodule)
                if int(label) != 1:
                    continue
                try:
                    mask_list = nodule_to_masks(nodule)
                    for slice, mask in mask_list.items():
                        if os.path.isfile(f"../pre-processing/data/Image/{patient_id}/{patient_id}_slice_{slice}.png"):
                            li = [(yx[1], yx[0]) for yx in mask['coordinates'][0]]
                            x, y = zip(*li)
                            out_string = ""
                            for i in range(len(x)):
                                out_string += f",{x[i]},{y[i]}"
                            slices[f"{patient_id}_slice_{slice}"].append({'polygon': out_string[1:], 'label': label})
                except:
                    pass
    test = []
    train = []
    for slice in slices:
        patient_id = slice[:slice.index('_')]
        tumours = slices[slice]
        polys = ""
        for t in tumours:
            polys += f"|{t['polygon']},{t['label']}"
        print(polys)
        val = f'\n/content/drive/My Drive/DeepTumour/pre-processing/data/Image/{patient_id}/{slice}.png,{polys[1:]}'

        if random.random() <= 0.7:
            train.append(val)
        else:
            test.append(val)

    with open("./data/train.txt", "w") as f:
        f.writelines(train)
    with open("./data/test.txt", "w") as f:
        f.writelines(test)


if __name__ == "__main__":
    create_annotations()
