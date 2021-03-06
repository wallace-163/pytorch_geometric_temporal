import torch
from torch_geometric.nn import ChebConv


class GConvGRU(torch.nn.Module):
    r"""An implementation of the Chebyshev Graph Convolutional Gated Recurrent Unit
    Cell. For details see this paper: `"Structured Sequence Modeling with Graph
    Convolutional Recurrent Networks." <https://arxiv.org/abs/1612.07659>`_

    Args:
        in_channels (int): Number of input features.
        out_channels (int): Number of output features.
        K (int): Chebyshev filter size.
    """
    def __init__(self, in_channels: int, out_channels: int, K: int):
        super(GConvGRU, self).__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.K = K
        self._create_parameters_and_layers()


    def _create_update_gate_parameters_and_layers(self):

        self.conv_x_z = ChebConv(in_channels=self.in_channels,
                                 out_channels=self.out_channels,
                                 K=self.K)

        self.conv_h_z = ChebConv(in_channels=self.out_channels,
                                 out_channels=self.out_channels,
                                 K=self.K)


    def _create_reset_gate_parameters_and_layers(self):

        self.conv_x_r = ChebConv(in_channels=self.in_channels,
                                 out_channels=self.out_channels,
                                 K=self.K)

        self.conv_h_r = ChebConv(in_channels=self.out_channels,
                                 out_channels=self.out_channels,
                                 K=self.K)


    def _create_candidate_state_parameters_and_layers(self):

        self.conv_x_h = ChebConv(in_channels=self.in_channels,
                                 out_channels=self.out_channels,
                                 K=self.K)

        self.conv_h_h = ChebConv(in_channels=self.out_channels,
                                 out_channels=self.out_channels,
                                 K=self.K)


    def _create_parameters_and_layers(self):
        self._create_update_gate_parameters_and_layers()
        self._create_reset_gate_parameters_and_layers()
        self._create_candidate_state_parameters_and_layers()


    def _set_hidden_state(self, X, H):
        if H is None:
            H = torch.zeros(X.shape[0], self.out_channels)
        return H


    def _calculate_update_gate(self, X, edge_index, edge_weight, H):
        Z = self.conv_x_z(X, edge_index, edge_weight)
        Z = Z + self.conv_h_z(H, edge_index, edge_weight)
        Z = torch.sigmoid(Z)
        return Z


    def _calculate_reset_gate(self, X, edge_index, edge_weight, H):
        R = self.conv_x_r(X, edge_index, edge_weight)
        R = R + self.conv_h_r(H, edge_index, edge_weight)
        R = torch.sigmoid(R) 
        return R


    def _calculate_candidate_state(self, X, edge_index, edge_weight, H, R):
        H_tilde = self.conv_x_h(X, edge_index, edge_weight)
        H_tilde = H_tilde + self.conv_h_h(H*R, edge_index, edge_weight)
        H_tilde = torch.tanh(H_tilde)
        return H_tilde


    def _calculate_hidden_state(self, Z, H, H_tilde):
        H = Z*H + (1-Z)*H_tilde
        return H


    def forward(self, X: torch.FloatTensor, edge_index: torch.LongTensor,
                edge_weight: torch.FloatTensor=None, H: torch.FloatTensor=None):
        """
        Making a forward pass. If edge weights are not present the forward pass
        defaults to an unweighted graph. If the hidden state matrix is not present
        when the forward pass is called it is initialized with zeros.

        Arg types:
            * **X** *(PyTorch Float Tensor)* - Node features.
            * **edge_index** *(PyTorch Long Tensor)* - Graph edge indices.
            * **edge_weight** *(PyTorch Long Tensor)* - Edge weight vector (optional).
            * **H** *(PyTorch Float Tensor)* - Hidden state matrix for all nodes (optional).

        Return types:
            * **H** *(PyTorch Float Tensor)* - Hidden state matrix for all nodes.
        """
        H = self._set_hidden_state(X, H)
        Z = self._calculate_update_gate(X, edge_index, edge_weight, H)
        R = self._calculate_reset_gate(X, edge_index, edge_weight, H)
        H_tilde = self._calculate_candidate_state(X, edge_index, edge_weight, H, R)
        H = self._calculate_hidden_state(Z, H, H_tilde)
        return H
