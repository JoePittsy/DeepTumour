import pylidc as pl
from vectors import Vector4D
from kmeans import *
import pprint
from scipy.stats import pearsonr


def get_data():
    data = []
    all_annotations = pl.query(pl.Annotation)
    ann: pl.Annotation
    count = 0
    max = all_annotations.count()
    for ann in all_annotations:
        count += 1
        bounding_box = ann.bbox()
        height = bounding_box[0].stop - bounding_box[0].start
        width = bounding_box[1].stop - bounding_box[1].start
        subtlety = ann.subtlety
        malignancy = ann.malignancy
        data.append(Vector4D(width, height, subtlety, malignancy))
        print(f"{count}/{max}: {(count / max) * 100}%")
    return data


if __name__ == "__main__":
    data = get_data()
    centroids, clusters, obj = kmeans(data, 2)
    # plt.title("Width & Malignancy. K = 5")
    # plt.xlabel("Width")
    # plt.ylabel("Height")
    # matrix = np.corrcoef(data, data)
    # pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(matrix)

    for c in clusters:
        cluster = np.array(c)
        print(cluster[:, 0].shape)
        print(cluster[:, 1].shape)
        print(cluster[:, 2].shape)
        print(cluster[:, 3].shape)

        plt.scatter(cluster[:, 0], cluster[: 1])
        plt.show()
