import torch
from torch.autograd import Variable
import time

from .spline_conv_gpu import SplineConvGPU

def spline_conv(
        adj,  # Pytorch Tensor (!bp_to_adj) or Pytorch Variable (bp_to_adj)
        input,  # Pytorch Variable
        weight,  # Pytorch Variable
        e_input,
        kernel_size,  # Rest tensors or python variables
        is_open_spline,
        K,
        weighting_kernel,
        weighting_backward_kernel,
        basis_kernel,
        basis_backward_kernel=None,
        degree=1,
        bias=None):

    if input.dim() == 1:
        input = input.unsqueeze(1)

    values = adj['values']
    row, col = adj['indices']

    # Get features for every end vertex with shape [|E| x M_in].
    output = input[col]
    if e_input is not None:
        output = torch.cat([output, e_input], dim=1)
        input_ph = Variable(torch.zeros(input.size(0), e_input.size(1)).cuda())
        input = torch.cat([input, input_ph],
                          dim=1)

    bp_to_adj = False if torch.is_tensor(values) else True
    # Convert to [|E| x M_in] feature matrix and calculate [|E| x M_out].

    if output.is_cuda:
        if bp_to_adj:
            output = SplineConvGPU(kernel_size, is_open_spline, K, degree,
                                   basis_kernel, basis_backward_kernel,
                                   weighting_kernel, weighting_backward_kernel,
                                   bp_to_adj)(output, weight[:-1], values)
        else:
            output = SplineConvGPU(kernel_size, is_open_spline, K, degree,
                                   basis_kernel, basis_backward_kernel,
                                   weighting_kernel, weighting_backward_kernel,
                                   bp_to_adj, values)(output, weight[:-1])
    else:
        # CPU Implementation not available
        raise NotImplementedError()

    # Convolution via `scatter_add`. Converts [|E| x M_out] feature matrix to
    # [n x M_out] feature matrix.
    zero = output.data.new(adj['size'][1], output.size(1)).fill_(0.0)
    zero = Variable(zero) if not torch.is_tensor(output) else zero
    r = row.view(-1, 1).expand(row.size(0), output.size(1))
    output = zero.scatter_add_(0, Variable(r), output)

    # Weighten root node features by multiplying with root weight.
    output += torch.mm(input, weight[-1])

    # Normalize output by degree.
    ones = output.data.new(values.size(0)).fill_(1)
    zero = output.data.new(output.size(0)).fill_(0)
    degree = zero.scatter_add_(0, row, ones)
    degree = torch.clamp(degree, min=1)
    output = output / Variable(degree.view(-1, 1))

    if bias is not None:
        output += bias

    return output