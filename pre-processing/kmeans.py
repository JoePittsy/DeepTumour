#!/usr/bin/env python3
# Written by: Joseph Pitts; 16657094@students.lincoln.ac.uk


import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import math
import copy
from vectors import Vector4D


def compute_euclidean_distance(vec_1, vec_2):
    """
    Compute the euclidean distance between Vector 1 and Vector 2
    :param vec_1: The first vector
    :param vec_2: The second vector
    :return: The euclidean distance between the vectors

    Note: Uses the dist funciton in the vectors.py file I wrote

    Func:
        def dist(self, x_coord, y_coord, z_coord, t_coord):
        '''	Calculates the distance between the Vector and a point.
        >>> v = Vector4D(3, 4, 5, 6)
        >>> v.dist(10, 6, 4, 2)
        8.3666002653
        '''
        a = x_coord - self.x
        b = y_coord - self.y
        c = z_coord - self.z
        d = t_coord - self.t

        return round(math.sqrt((a * a) + (b * b) + (c * c) + (d * d)), 10)
    """

    return vec_1.distVector4D(vec_2)

def initialise_centroids(dataset, k):
    """
    Initialise centroids for the K-Means function
    :param dataset: The dataset to choose centroids from
    :param k: The amount of centroids to pick
    :return: An array of K random points from the dataset
    """
    samples = len(dataset)
    return [dataset[i] for i in np.random.choice(samples, k, False)]


def kmeans(dataset, k):
    """
    An implementation of the K-Means algorithm
    :param dataset: The data to cluster
    :param k: How many clusters to create
    :return: A tupple with three values; the list of centroids, the clusters and the objective function data.
    """

    centroids = initialise_centroids(dataset, k)
    iteration = 0
    agg_distance = []

    while True:
        clusters = [[] for _ in range(k)]
        agg = 0  # The variable to hold the within cluster spread value

        for point in dataset:
            closest = np.argmin([compute_euclidean_distance(point, centroid) for centroid in centroids])
            clusters[closest].append(point)
            agg += abs(math.pow(compute_euclidean_distance(point, centroids[closest]), 2))

        # Record the within cluster spread for this iteration
        agg_distance.append([iteration, agg])
        iteration += 1

        old_centroids = copy.deepcopy(centroids)

        # Create new centroids from cluster means
        for i, cluster in enumerate(clusters):
            mean_cluster = Vector4D(0, 0, 0, 0)
            [mean_cluster.addVector4D(v) for v in cluster]
            size = len(cluster)
            mean_cluster.div(size, size, size, size)

            centroids[i] = mean_cluster

        # If the distance between the old centroids and the new centroids is zero we are done
        if sum([compute_euclidean_distance(centroids[i], old_centroids[i]) for i in range(k)]) == 0:
            print(f"Completed in {iteration} iterations")
            centroids = [v.array() for v in centroids]
            clusters = [[v.array() for v in c] for c in clusters]
            return centroids, clusters, np.array(agg_distance)
