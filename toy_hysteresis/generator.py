import numpy as np
import torch

from hysteresis import preisach

def generate_current_data(n_pts):
    #generate the sequence of current settings (in arb units)
    t = np.linspace(0,1,n_pts)
    #current = -1.25*(1 - 0.5*t)*np.sin(2 * np.pi * t / 0.1 + np.pi/2)
    current = -1.05*np.cos(2 * np.pi * t / 1.25)
    #current = -1.25 + t * 2.5
    return t, current

def generate_magnetization_model(n_pts = 20):
    t, current = generate_current_data(n_pts) 
    pmodel = preisach.PreisachModel(torch.from_numpy(current))

    pmodel.propagate_states()
    return t, current, pmodel
    
