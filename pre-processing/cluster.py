import pylidc as pl
import pickle
from matplotlib import pyplot as plt
import numpy as np
import seaborn as sns
import matplotlib
from sklearn.cluster import KMeans

matplotlib.use('TkAgg')


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
        data.append(
            [
                width,
                height,
                ann.subtlety,
                ann.lobulation,
                ann.spiculation,
                ann.malignancy
            ]
        )
        print(f"{count}/{max}: {(count / max) * 100}%")
    return data


if __name__ == "__main__":
    with open("WHSLSM.pcl", "rb") as f:
        data = pickle.load(f)

    data = np.array(data)

    kmeans = KMeans(n_clusters=4)
    kmeans.fit(data)
    y_kmeans = kmeans.predict(data)

    sns.set(style="darkgrid")

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    x = data[:, 0]
    y = data[:, 1]
    z = data[:, -1]

    ax.set_xlabel("Width")
    ax.set_ylabel("Height")
    ax.set_zlabel("Malignancy")

    ax.scatter(x, y, z, c=y_kmeans, s=50, cmap='viridis')
    centers = kmeans.cluster_centers_
    ax.scatter(centers[:, 0], centers[:, 1], centers[:, -1], c='black', s=200, alpha=0.5)

    plt.show()
    pickle.dump(kmeans, open("kmeans.pkl", "wb"))
