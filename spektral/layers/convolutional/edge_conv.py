from tensorflow.keras import activations
from tensorflow.keras import backend as K
from tensorflow.keras.layers import Dense
from tensorflow.keras.models import Sequential

from spektral.layers.convolutional.message_passing import MessagePassing


class EdgeConv(MessagePassing):
    r"""
    An edge convolutional layer from the paper

    > [Dynamic Graph CNN for Learning on Point Clouds](https://arxiv.org/abs/1801.07829)<br>
    > Yue Wang et al.

    **Mode**: single, disjoint, mixed.

    **This layer expects a sparse adjacency matrix.**

    This layer computes for each node \(i\):
    $$
        \x_i' = \sum\limits_{j \in \mathcal{N}(i)} \textrm{MLP}\big( \x_i \|
        \x_j - \x_i \big)
    $$
    where \(\textrm{MLP}\) is a multi-layer perceptron.

    **Input**

    - Node features of shape `(n_nodes, n_node_features)`;
    - Binary adjacency matrix of shape `(n_nodes, n_nodes)`.

    **Output**

    - Node features with the same shape of the input, but the last dimension
    changed to `channels`.

    **Arguments**

    - `channels`: integer, number of output channels;
    - `mlp_hidden`: list of integers, number of hidden units for each hidden
    layer in the MLP (if None, the MLP has only the output layer);
    - `mlp_activation`: activation for the MLP layers;
    - `activation`: activation function;
    - `use_bias`: bool, add a bias vector to the output;
    - `kernel_initializer`: initializer for the weights;
    - `bias_initializer`: initializer for the bias vector;
    - `kernel_regularizer`: regularization applied to the weights;
    - `bias_regularizer`: regularization applied to the bias vector;
    - `activity_regularizer`: regularization applied to the output;
    - `kernel_constraint`: constraint applied to the weights;
    - `bias_constraint`: constraint applied to the bias vector.
    """

    def __init__(
        self,
        channels,
        mlp_hidden=None,
        mlp_activation="relu",
        aggregate="sum",
        activation=None,
        use_bias=True,
        kernel_initializer="glorot_uniform",
        bias_initializer="zeros",
        kernel_regularizer=None,
        bias_regularizer=None,
        activity_regularizer=None,
        kernel_constraint=None,
        bias_constraint=None,
        **kwargs
    ):
        super().__init__(
            aggregate=aggregate,
            activation=activation,
            use_bias=use_bias,
            kernel_initializer=kernel_initializer,
            bias_initializer=bias_initializer,
            kernel_regularizer=kernel_regularizer,
            bias_regularizer=bias_regularizer,
            activity_regularizer=activity_regularizer,
            kernel_constraint=kernel_constraint,
            bias_constraint=bias_constraint,
            **kwargs
        )
        self.channels = channels
        self.mlp_hidden = mlp_hidden if mlp_hidden else []
        self.mlp_activation = activations.get(mlp_activation)

    def build(self, input_shape):
        assert len(input_shape) >= 2
        layer_kwargs = dict(
            kernel_initializer=self.kernel_initializer,
            bias_initializer=self.bias_initializer,
            kernel_regularizer=self.kernel_regularizer,
            bias_regularizer=self.bias_regularizer,
            kernel_constraint=self.kernel_constraint,
            bias_constraint=self.bias_constraint,
            dtype=self.dtype,
        )

        self.mlp = Sequential(
            [
                Dense(channels, self.mlp_activation, **layer_kwargs)
                for channels in self.mlp_hidden
            ]
            + [
                Dense(
                    self.channels,
                    self.activation,
                    use_bias=self.use_bias,
                    **layer_kwargs
                )
            ]
        )

        self.built = True

    def message(self, x, **kwargs):
        x_i = self.get_targets(x)
        x_j = self.get_sources(x)
        return self.mlp(K.concatenate((x_i, x_j - x_i)))

    @property
    def config(self):
        return {
            "channels": self.channels,
            "mlp_hidden": self.mlp_hidden,
            "mlp_activation": self.mlp_activation,
        }
