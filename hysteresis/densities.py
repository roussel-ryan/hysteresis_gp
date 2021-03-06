import torch
import numpy as np


class HysterionDensity:
    def __init__(self, name):
        self.name = name
        self.params = {}
        
    def get_denisty(self, X):
        raise NotImplementedError


class MultiVariateNormal(torch.nn.Module):
    def __init__(self, mu, cov = None, diag_cov = None):
        #assert cov.shape[0] == 2
        #assert cov.shape[0] == cov.shape[1]
        #assert mu.shape[0] == cov.shape[0]
        
        super(MultiVariateNormal, self).__init__()

        self.mu = torch.nn.parameter.Parameter(mu)

        if not diag_cov == None:
            self.use_diag = True
            self.diag_cov = torch.nn.parameter.Parameter(diag_cov)
        elif not cov == None:
            self.use_diag = False
            self.cov = torch.nn.parameter.Parameter(cov)
        else:
            raise RuntimeError('can only specify cov or diag_cov! not both')

            
    def forward(self, X):
        '''
        calculate the multivariate hysterion desity function on a
        2D on a set of points given by X

        Arguments
        ---------
        X : torch.tensor, shape (n,2)
            Coordinates to calculate density on

        Returns
        -------
        mn : torch.tensor, shape (n,1)
            Hysterion density at given points X

        '''
        if self.use_diag:
            self.cov = torch.diag(self.diag_cov)
        
        assert self.cov.shape[0] == X.shape[1]
    
        diff = (X - self.mu).float()
        
        mdist1 = torch.matmul(diff,torch.inverse(self.cov.float()))
        mdist = torch.diag(torch.matmul(mdist1, torch.transpose(diff, 0, 1)))
        mn = torch.exp(-0.5 * mdist) / torch.sqrt(4 * np.pi**2 * torch.det(self.cov))
        return mn
