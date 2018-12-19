Create your own graph neural network
====================================

.. We shortly introduce the fundamental concepts of `PyTorch Geometric <https://github.com/rusty1s/pytorch_geometric>`_ through self-contained examples.
.. At its core, PyTorch Geometric provides the following main features:

.. contents::
    :local:

Message Passing Graph Neural Networks
-------------------------------------

Generalizing the convolution operator to irregular domains is typically expressed as a *neighborhood aggregation* or *message passing* scheme.
Let therefore :math:`\mathbf{x}^{(k-1)}_i \in \mathbb{R}^F` denote node features of node :math:`i` in layer :math:`(k-1)` and let :math:`\mathbf{e}_{i,j} \in \mathbb{R}^D` denote (optional) edge features from node :math:`i` to node :math:`j`.
In its most general form, message passing graph neural networks can then be described as

.. math::
  \mathbf{x}_i^{(k)} = \gamma^{(k)} \left( \mathbf{x}_i^{(k-1)}, \square_{j \in \mathcal{N}(i)} \, \phi^{(k)}\left(\mathbf{x}_i^{(k-1)}, \mathbf{x}_j^{(k-1)},\mathbf{e}_{i,j}\right) \right),

where :math:`\square` denotes a differentiable, permutation invariant function, *e.g.*, sum, mean or max, and :math:`\gamma` and :math:`\phi` denote differentiable functions such as MLPs.

Nearly all of the already implemented methods in PyTorch Geometric follow this simple scheme.
In addition, using the :class:`torch_geometric.nn.MessagePassing` base class, it is really simple to create them by yourself.
The :class:`torch_geometric.nn.MessagePassing` base class automatically takes care of message propagation, so that the user only needs to define the methods :math:`\phi` ,*i.e.* the :meth:`message` method, and :math:`\gamma` ,*.i.e.* the :meth:`update` method, as well as choosing between various permutation invariant functions :math:`\square`, *.e.g.* :obj:`aggr='add'`.

Let us verify this by re-implementing two popular GNN variants, `GCN from Kipf and Welling <https://arxiv.org/abs/1609.02907>`_ and the `Message Passing Layer from Gilmer et al. <https://arxiv.org/abs/1704.01212>`_:

A GCN layer is mathematically defined as

.. math::

    \mathbf{x}_i^{(k)} = \sum_{j \in \mathcal{N}(i) \cup \{ i \}} \frac{1}{\sqrt{\deg(i)} \cdot \sqrt{deg(j)}} \cdot \mathbf{\Theta} \cdot \mathbf{x}_j^{(k-1)},

where input node features are first transformed by a weight matrix :math:`\mathbf{\Theta}`, neighborhood-normalized and finally added together afterwards.



.. code-block:: python

    import torch
    from torch_geometric.nn import MessagePassing
    from torch_geometric.utils import add_self_loops, degree

    class GCNConv(MessagePassing):
        def __init__(self, in_channels, out_channels):
            super(GCNLayer, self).__init__(aggr='add')
            self.lin = torch.nn.Linear(in_channels, out_channels)

        def forward(self, x, edge_index):
            edge_index = add_self_loops(edge_index, num_nodes=x.size(0))

            row, col = edge_index
            deg = degree(row, num_nodes=x.size(0), dtype=x.dtype)
            deg_inv = deg.pow(-0.5)
            edge_attr = deg_inv[row] * deg_inv[col]

            x = self.lin(x)

            return super(GCNLayer, self).forward(x, edge_index, edge_attr)

        def message(self, x_i, x_j, edge_attr, **kwargs):
            return edge_attr * x_j

        def update(self, x_old, x):
            return x

Graph Nets
----------

Other Graph Neural Networks
---------------------------

The beauty of PyTorch Geometric is that one can easily create new message passing layer or more general graph nets, but is not limited to do.