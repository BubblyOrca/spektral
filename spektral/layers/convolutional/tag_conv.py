from tensorflow.keras import backend as K
from tensorflow.keras.layers import Dense

from spektral.layers.convolutional.message_passing import MessagePassing
from spektral.utils import normalized_adjacency


class TAGConv(MessagePassing):
    r"""
    A Topology Adaptive Graph Convolutional layer (TAG) from the paper

    > [Topology Adaptive Graph Convolutional Networks](https://arxiv.org/abs/1710.10370)<br>
    > Jian Du et al.

    **Mode**: single, disjoint, mixed.

    **This layer expects a sparse adjacency matrix.**

    This layer computes:
    $$
        \Z = \sum\limits_{k=0}^{K} \D^{-1/2}\A^k\D^{-1/2}\X\W^{(k)}
    $$

    **Input**

    - Node features of shape `(n_nodes, n_node_features)`;
    - Binary adjacency matrix of shape `(n_nodes, n_nodes)`.

    **Output**

    - Node features with the same shape of the input, but the last dimension
    changed to `channels`.

    **Arguments**

    - `channels`: integer, number of output channels;
    - `K`: the order of the layer (i.e., the layer will consider a K-hop
    neighbourhood for each node);
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
        K=3,
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
        self.K = K
        self.linear = Dense(
            channels,
            activation=activation,
            use_bias=use_bias,
            kernel_initializer=kernel_initializer,
            bias_initializer=bias_initializer,
            kernel_regularizer=kernel_regularizer,
            bias_regularizer=bias_regularizer,
            activity_regularizer=activity_regularizer,
            kernel_constraint=kernel_constraint,
            bias_constraint=bias_constraint,
        )

    def build(self, input_shape):
        assert len(input_shape) >= 2
        self.built = True

    def call(self, inputs, **kwargs):
        x, a, _ = self.get_inputs(inputs)
        edge_weight = a.values

        output = [x]
        for _ in range(self.K):
            output.append(self.propagate(x, a, edge_weight=edge_weight))
        output = K.concatenate(output)

        return self.linear(output)

    def message(self, x, edge_weight=None):
        x_j = self.get_sources(x)
        return edge_weight[:, None] * x_j

    @property
    def config(self):
        return {
            "channels": self.channels,
        }

    @staticmethod
    def preprocess(a):
        return normalized_adjacency(a)
