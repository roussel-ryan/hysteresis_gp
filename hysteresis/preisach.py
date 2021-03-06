import torch
import numpy as np
from . import densities

import matplotlib.pyplot as plt

class PreisachModel:
    def __init__(self, H = None, **kwargs):
        #specify grid size
        self.grid_size = kwargs.get('grid_size',100)
        
        #positive and negative saturation levels
        self.alpha_0 = kwargs.get('alpha_0',1.0)
        self.beta_0 = kwargs.get('beta_0',-1.0)
        self.sat_fld = kwargs.get('sat_fld', 1.0)
        assert self.alpha_0 > self.beta_0

        #create grid
        b = np.linspace(self.beta_0, -self.beta_0, self.grid_size)
        a = np.linspace(-self.alpha_0, self.alpha_0, self.grid_size)
        bb,aa = np.meshgrid(b, a)

        #create grid tensors
        self.beta = torch.from_numpy(bb)
        self.alpha = torch.from_numpy(aa)

        #create grid for mu (hysterion density)
        #self.mu = torch.zeros((self.grid_size, self.grid_size))

        #create grid for the state history
        #size: (tsteps+1, grid_size, grid_size)
        self.initial_state = -1 * torch.tril(torch.ones((1, self.grid_size, self.grid_size)))
        self.state = self.initial_state

        if not H == None:
            self.set_applied_field(H)

            
    def set_applied_field(self, H, append = False):
        #set the applied field values H
        if append:
            self.H = torch.vstack((self.H,H))
        else:
            self.H = H
            self.state = self.initial_state

            
    def get_grid(self):
        #returns copy of grid points in alpha/beta space
        t = torch.vstack((torch.flatten(self.beta),torch.flatten(self.alpha)))
        return torch.transpose(t,0,1)

    
    def calculate_scaling(self, mu):
        #calculate the scale factor to normalize the saturation field
        return -self.sat_fld / torch.sum(mu * self.initial_state)

    
    def calculate_magnetization(self, hysterion_density):
        #assert isinstance(hysterion_density, densities.HysterionDensity)

        #determine scaling via saturation fld
        mu = hysterion_density.forward(
            self.get_grid()).reshape(self.grid_size, self.grid_size)
        
        scaling = self.calculate_scaling(mu)
        
        #results container
        n_steps = self.state.shape[0]
        results = torch.empty((n_steps))
        for i in range(n_steps):
            results[i] = torch.sum(mu * self.state[i]) * scaling

            
        return results[1:]

    
    def propagate_states(self):
        #recalculate the state history given current applied field history H
        n_steps = self.H.shape[0]
        
        for i in range(n_steps):
            if i == 0:
                dH = 1
            else:
                dH = self.H[i] - self.H[i - 1]

            new_state = self.update_state(self.H[i], dH, self.state[i])
            self.state = torch.cat((self.state,new_state),0)

            
    def predict_magnetization(self, new_H, hysterion_density):
        #predict next magnetization based on new_H
        #dont add it to datatracking

        results = torch.zeros_like(new_H)
        for i in range(len(new_H)):
            dH = new_H[i] - self.H[-1]
            new_state = self.update_state(new_H[i], dH, self.state[-1])

            #calculate mu from density
            mu = hysterion_density.forward(
                self.get_grid()).reshape(self.grid_size, self.grid_size)
        
            scaling = self.calculate_scaling(mu)

            results[i] = torch.sum(mu * new_state) * scaling

        return results
    
    def update_state(self, H, dH, state):
        if dH > 0:
            #determine locations where we want to set the state to +1
            flip = torch.where(H > self.alpha,
                               torch.ones_like(self.alpha),
                               torch.zeros_like(self.alpha))
            #print(torch.nonzero(flip))
            new_state = state.clone()

            new_state[torch.nonzero(flip, as_tuple=True)] = 1
            new_state = new_state.reshape(1,self.grid_size,self.grid_size)
            
        elif dH < 0:
            #determine locations where we want to set the state to -1
            flip = torch.where(H < self.beta,
                               torch.ones_like(self.beta),
                               torch.zeros_like(self.beta))
            #print(torch.nonzero(flip))
            new_state = state.clone()

            new_state[torch.nonzero(flip, as_tuple=True)] = -1
            new_state = new_state.reshape(1,self.grid_size,self.grid_size)

            
        else:
            new_state = state.clone()
            new_state = new_state.reshape(1,self.grid_size,self.grid_size)

            
        #get upper triangle
        return torch.tril(new_state)

    
    def visualize(self):
        for i in range(self.state.shape[0]):
            plt.figure()
            plt.imshow(self.state[i].numpy(),vmin=-1,vmax=1,origin='lower')

            
#testing
if __name__ == '__main__':
    H = torch.tensor([-2.75, -0.25, 0.0, -0.5, 2.5])
    m = PreisachModel(H)

    mu = torch.ones((m.grid_size, m.grid_size))
    mu = mu / torch.sum(mu)
    
    m.propagate_states()
    m.visualize()

    print(m.calculate_field_response(mu))
    
    plt.show()
