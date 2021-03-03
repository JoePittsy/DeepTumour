import pylidc as pl
import pickle
from matplotlib import pyplot as plt
import numpy as np
import seaborn as sns
from mpl_toolkits.mplot3d import Axes3D
import matplotlib
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

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
            [width,
             height,
             ann.subtlety,
             ann.internalStructure,
             ann.calcification,
             ann.sphericity,
             ann.margin,
             ann.lobulation,
             ann.spiculation,
             ann.texture,
             ann.malignancy]
        )
        print(f"{count}/{max}: {(count/max)*100}%")
    return data


if __name__ == "__main__":
    with open("all_data.pcl", "rb") as f:
        data = pickle.load(f)

    sns.set(style="darkgrid")

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    x = data[:, 0] * data[:, 1]
    y = data[:, 2]
    z = data[:, -1]

    ax.set_xlabel("Area")
    ax.set_ylabel("Subtlety")
    ax.set_zlabel("Malignancy")

    ax.scatter(x, y, z)

    # plt.show()

    clusters = 7

    reduced_data = PCA(n_components=2).fit_transform(data)
    kmeans = KMeans(init="k-means++", n_clusters=clusters, n_init=4)
    kmeans.fit(reduced_data)

    # Step size of the mesh. Decrease to increase the quality of the VQ.
    h = .02  # point in the mesh [x_min, x_max]x[y_min, y_max].

    # Plot the decision boundary. For that, we will assign a color to each
    x_min, x_max = reduced_data[:, 0].min() - 1, reduced_data[:, 0].max() + 1
    y_min, y_max = reduced_data[:, 1].min() - 1, reduced_data[:, 1].max() + 1
    xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))

    # Obtain labels for each point in mesh. Use last trained model.
    Z = kmeans.predict(np.c_[xx.ravel(), yy.ravel()])

    # Put the result into a color plot
    Z = Z.reshape(xx.shape)
    plt.figure(1)
    plt.clf()
    plt.imshow(Z, interpolation="nearest",
               extent=(xx.min(), xx.max(), yy.min(), yy.max()),
               cmap=plt.cm.Paired, aspect="auto", origin="lower")

    plt.plot(reduced_data[:, 0], reduced_data[:, 1], 'k.', markersize=2)
    # Plot the centroids as a white X
    centroids = kmeans.cluster_centers_
    plt.scatter(centroids[:, 0], centroids[:, 1], marker="x", s=169, linewidths=3,
                color="w", zorder=10)
    plt.title("K-means clustering on the digits dataset (PCA-reduced data)\n"
              "Centroids are marked with white cross")
    plt.xlim(x_min, x_max)
    plt.ylim(y_min, y_max)
    plt.xticks(())
    plt.yticks(())
    plt.show()
