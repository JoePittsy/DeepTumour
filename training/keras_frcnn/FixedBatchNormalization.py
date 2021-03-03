from keras.engine import Layer, InputSpec
from keras import initializers, regularizers
from keras import backend as K
import tensorflow as tf


class FixedBatchNormalization(Layer):

    def __init__(self, epsilon=1e-3, axis=-1,
                 weights=None, beta_init='zero', gamma_init='one',
                 gamma_regularizer=None, beta_regularizer=None, **kwargs):

        self.supports_masking = True
        self.beta_init = initializers.get(beta_init)
        self.gamma_init = initializers.get(gamma_init)
        self.epsilon = epsilon
        self.axis = axis
        self.gamma_regularizer = regularizers.get(gamma_regularizer)
        self.beta_regularizer = regularizers.get(beta_regularizer)
        self.initial_weights = weights
        super(FixedBatchNormalization, self).__init__(**kwargs)

    def build(self, input_shape):
        self.input_spec = [InputSpec(shape=input_shape)]
        shape = (input_shape[self.axis],)

        self.gamma = self.add_weight(shape,
                                     initializer=self.gamma_init,
                                     regularizer=self.gamma_regularizer,
                                     name='{}_gamma'.format(self.name),
                                     trainable=False)
        self.beta = self.add_weight(shape,
                                    initializer=self.beta_init,
                                    regularizer=self.beta_regularizer,
                                    name='{}_beta'.format(self.name),
                                    trainable=False)
        self.running_mean = self.add_weight(shape, initializer='zero',
                                            name='{}_running_mean'.format(self.name),
                                            trainable=False)
        self.running_std = self.add_weight(shape, initializer='one',
                                           name='{}_running_std'.format(self.name),
                                           trainable=False)

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

        self.built = True

    def call(self, x, mask=None):

        assert self.built, 'Layer must be built before being called'
        input_shape = K.int_shape(x)

        reduction_axes = list(range(len(input_shape)))
        del reduction_axes[self.axis]
        broadcast_shape = [1] * len(input_shape)
        broadcast_shape[self.axis] = input_shape[self.axis]

        if sorted(reduction_axes) == range(K.ndim(x))[:-1]:
            x_normed = K.batch_normalization(
                x, self.running_mean, self.running_std,
                self.beta, self.gamma,
                epsilon=self.epsilon)
        else:
            # need broadcasting
            broadcast_running_mean = K.reshape(self.running_mean, broadcast_shape)
            broadcast_running_std = K.reshape(self.running_std, broadcast_shape)
            broadcast_beta = K.reshape(self.beta, broadcast_shape)
            broadcast_gamma = K.reshape(self.gamma, broadcast_shape)
            x_normed = FixedBatchNormalization.batch_normalization(
                x, broadcast_running_mean, broadcast_running_std,
                broadcast_beta, broadcast_gamma,
                epsilon=self.epsilon)

        return x_normed

    def get_config(self):
        config = {'epsilon': self.epsilon,
                  'axis': self.axis,
                  'gamma_regularizer': self.gamma_regularizer.get_config() if self.gamma_regularizer else None,
                  'beta_regularizer': self.beta_regularizer.get_config() if self.beta_regularizer else None}
        base_config = super(FixedBatchNormalization, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

    @staticmethod
    def batch_normalization(x, mean, var, beta, gamma, axis=-1, epsilon=1e-3):
        """Applies batch normalization on x given mean, var, beta and gamma.

        I.e. returns:
        `output = (x - mean) / sqrt(var + epsilon) * gamma + beta`

        # Arguments
            x: Input tensor or variable.
            mean: Mean of batch.
            var: Variance of batch.
            beta: Tensor with which to center the input.
            gamma: Tensor by which to scale the input.
            axis: Integer, the axis that should be normalized.
                (typically the features axis).
            epsilon: Fuzz factor.

        # Returns
            A tensor.
        """
        if K.ndim(x) == 4:
            # The CPU implementation of FusedBatchNorm only support NHWC
            if axis == 1 or axis == -3:
                tf_data_format = 'NCHW'
            elif axis == 3 or axis == -1:
                tf_data_format = 'NHWC'
            else:
                tf_data_format = None

            if tf_data_format == 'NHWC' or tf_data_format == 'NCHW' and K._has_nchw_support():
                # The mean / var / beta / gamma may be processed by broadcast
                # so it may have extra axes with 1, it is not needed and should be removed
                if K.ndim(mean) > 1:
                    mean = tf.reshape(mean, [-1])
                if K.ndim(var) > 1:
                    var = tf.reshape(var, [-1])
                if beta is None:
                    beta = K.zeros_like(mean)
                elif K.ndim(beta) > 1:
                    beta = tf.reshape(beta, [-1])
                if gamma is None:
                    gamma = K.ones_like(mean)
                elif K.ndim(gamma) > 1:
                    gamma = tf.reshape(gamma, [-1])
                y, _, _ = tf.nn.fused_batch_norm(
                    x,
                    gamma,
                    beta,
                    epsilon=epsilon,
                    mean=mean,
                    variance=var,
                    data_format=tf_data_format,
                    is_training=False
                )
                return y
        # default
        return tf.nn.batch_normalization(x, mean, var, beta, gamma, epsilon)
