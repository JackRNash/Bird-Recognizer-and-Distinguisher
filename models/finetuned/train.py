import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import torchvision
from torchvision import datasets, models, transforms
import matplotlib.pyplot as plt
import time
import os
import copy
print("PyTorch Version: ",torch.__version__)
print("Torchvision Version: ",torchvision.__version__)
print('GPU Available: ', torch.cuda.is_available())

# code taken from https://pytorch.org/tutorials/beginner/finetuning_torchvision_models_tutorial.html