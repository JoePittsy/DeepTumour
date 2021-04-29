import pickle
import random
import pylidc as pl
from utils import *

LIDC_FOLDER = "/media/joe/16657094/LIDC-IDRI"


def calculate_label(nodule, width, height):
    list_of_subtlety = [ann.subtlety for ann in nodule]
    subtlety = np.mean(list_of_subtlety)

    list_of_lobulation = [ann.lobulation for ann in nodule]
    lobulation = np.mean(list_of_lobulation)

    list_of_spiculation = [ann.spiculation for ann in nodule]
    spiculation = np.mean(list_of_spiculation)

    list_of_malignancy = [ann.malignancy for ann in nodule]
    malignancy = np.mean(list_of_malignancy)

    point = np.array([
        width,
        height,
        subtlety,
        lobulation,
        spiculation,
        malignancy
    ])

    label = kmeans.predict(point.reshape(1, -1))

    return label[0]


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
                try:
                    mask_list = nodule_to_masks(nodule)
                    for slice, mask in mask_list.items():
                        if os.path.isfile(f"../pre-processing/data/Image/{patient_id}/{patient_id}_slice_{slice}.png"):
                            li = [(yx[1], yx[0]) for yx in mask['coordinates'][0]]
                            x, y = zip(*li)
                            out_string = ""
                            for i in range(len(x)):
                                out_string += f",{x[i]},{y[i]}"

                            width = np.max(x) - np.min(x)
                            height = np.max(y) - np.min(y)

                            label = calculate_label(nodule, width, height)
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
    kmeans: KMeans = pickle.load(open("kmeans.pkl", "rb"))
    create_annotations()
